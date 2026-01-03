"""Triagent Web API - FastAPI application."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from triagent.web.config import WebConfig
from triagent.web.routers import auth, chat, health, session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Triagent Web API",
    description="Web API for Triagent Azure DevOps automation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
config = WebConfig()
# Parse CORS origins: "*" means all, otherwise comma-separated list
cors_origins = (
    ["*"]
    if config.cors_origins == "*"
    else [origin.strip() for origin in config.cors_origins.split(",")]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(session.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
