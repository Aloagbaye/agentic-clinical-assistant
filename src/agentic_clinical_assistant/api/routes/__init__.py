"""API routes."""

from agentic_clinical_assistant.api.routes.agent import router as agent_router
from agentic_clinical_assistant.api.routes.metrics import router as metrics_router
from agentic_clinical_assistant.api.routes.tools import router as tools_router
from agentic_clinical_assistant.api.routes.workers import router as workers_router

__all__ = ["agent_router", "metrics_router", "workers_router", "tools_router"]

