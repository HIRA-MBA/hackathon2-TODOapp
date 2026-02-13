import os
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.config.database import close_db
from app.api.routes import router
from app.mcp.server import create_mcp_app, get_mcp_http_app
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.correlation import CorrelationIDMiddleware
from app.services.event_publisher import shutdown_event_publisher


# Configure structured JSON logging per FR-024 and Task 6.3
class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from record
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms
        if hasattr(record, "tool"):
            log_data["tool"] = record.tool
        if hasattr(record, "tool_calls"):
            log_data["tool_calls"] = record.tool_calls
        if hasattr(record, "error"):
            log_data["error"] = record.error

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging():
    """Configure structured JSON logging for the application."""
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add JSON handler for stdout
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# Configure logging on module load
configure_logging()

settings = get_settings()

# Set OpenAI API key in environment for the agents SDK
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Create MCP app first to get its lifespan
mcp_app = create_mcp_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events including MCP server and event publisher."""
    # Use the singleton MCP http_app's lifespan
    mcp_http_app = get_mcp_http_app()
    async with mcp_http_app.lifespan(mcp_http_app):
        yield
    # Shutdown event publisher (Phase V)
    await shutdown_event_publisher()
    # Shutdown database
    await close_db()


app = FastAPI(
    title="Todo Web Application API",
    description="RESTful API with event-driven architecture (Phase V Cloud-Native)",
    version="1.5.0",
    lifespan=lifespan,
)

# Add Request ID middleware for observability (FR-024, FR-025)
app.add_middleware(RequestIDMiddleware)

# Add Correlation ID middleware for distributed tracing (Phase V)
app.add_middleware(CorrelationIDMiddleware)

# Add rate limiting middleware for chat endpoint (FR-026)
# 20 requests per minute per authenticated user
app.add_middleware(RateLimitMiddleware, paths=["/api/chat"])

# Configure CORS
# Per research.md: allow_credentials=True required for cookie-based auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


# Root health check endpoint
@app.get("/")
async def root():
    return {"status": "ok", "message": "Todo API is running"}


# Mount MCP server for ChatKit (with auth middleware)
# FastMCP creates routes at /mcp internally, so mount at root
app.mount("", mcp_app)
