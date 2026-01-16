import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.config.database import close_db
from app.api.routes import router
from app.mcp.server import create_mcp_app, get_mcp_http_app

settings = get_settings()

# Set OpenAI API key in environment for the agents SDK
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Create MCP app first to get its lifespan
mcp_app = create_mcp_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events including MCP server."""
    # Use the singleton MCP http_app's lifespan
    mcp_http_app = get_mcp_http_app()
    async with mcp_http_app.lifespan(mcp_http_app):
        yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Todo Web Application API",
    description="RESTful API for Phase II Full-Stack Todo Web Application",
    version="1.0.0",
    lifespan=lifespan,
)

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

# Mount MCP server for ChatKit (with auth middleware)
# FastMCP creates routes at /mcp internally, so mount at root
app.mount("", mcp_app)
