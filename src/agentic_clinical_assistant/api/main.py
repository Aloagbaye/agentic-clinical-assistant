"""FastAPI application main file."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from agentic_clinical_assistant.api.middleware import setup_cors, setup_logging_middleware
from agentic_clinical_assistant.api.routes import (
    agent_router,
    metrics_router,
    tools_router,
    workers_router,
)
from agentic_clinical_assistant.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="PHI-Safe Clinical Ops Copilot (Agentic RAG System)",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Setup middleware
setup_cors(app)
setup_logging_middleware(app)

# Include routers
app.include_router(agent_router)
app.include_router(metrics_router)
app.include_router(workers_router)
app.include_router(tools_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred",
        },
    )

