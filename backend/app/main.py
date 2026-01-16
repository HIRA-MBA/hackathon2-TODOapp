import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.config.database import close_db
from app.api.routes import router

settings = get_settings()

# Set OpenAI API key in environment for the agents SDK
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
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
from app.mcp.server import create_mcp_app
app.mount("/mcp", create_mcp_app())
