"""CORS middleware configuration."""

from fastapi.middleware.cors import CORSMiddleware

from agentic_clinical_assistant.config import settings


def setup_cors(app) -> None:
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

