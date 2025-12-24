"""Database package for agentic-clinical-assistant."""

from agentic_clinical_assistant.database.base import (
    Base,
    get_async_session,
    get_async_session_local,
    get_db,
    get_engine,
)

# Import models to ensure they're registered
from agentic_clinical_assistant.database.models import (  # noqa: F401
    AgentRun,
    Citation,
    Evaluation,
    EvidenceRetrieval,
    GroundingVerification,
    PolicyMemory,
    PromptVersion,
    QueryPattern,
    RunStatus,
    SessionMemory,
    ToolCall,
)

# Lazy initialization - only create engine when needed
# This prevents issues when Alembic imports models
try:
    from agentic_clinical_assistant.database.base import AsyncSessionLocal, engine
except Exception:
    # If engine creation fails (e.g., during Alembic imports), set to None
    AsyncSessionLocal = None  # type: ignore
    engine = None  # type: ignore

__all__ = [
    "Base",
    "get_db",
    "get_async_session",
    "get_engine",
    "get_async_session_local",
    "AsyncSessionLocal",
    "engine",
    # Models
    "AgentRun",
    "RunStatus",
    "Citation",
    "Evaluation",
    "EvidenceRetrieval",
    "GroundingVerification",
    "PolicyMemory",
    "QueryPattern",
    "PromptVersion",
    "SessionMemory",
    "ToolCall",
]

