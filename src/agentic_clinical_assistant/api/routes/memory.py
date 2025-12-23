"""Memory API routes."""

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from agentic_clinical_assistant.memory.policy import get_policy_memory
from agentic_clinical_assistant.memory.session import get_session_memory

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/sessions")
async def create_session(
    user_id: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new session.

    Args:
        user_id: User identifier
        preferences: Initial preferences

    Returns:
        Created session information
    """
    session_memory = get_session_memory()
    session = await session_memory.create_session(
        user_id=user_id,
        preferences=preferences,
    )

    return {
        "session_id": str(session.session_id),
        "user_id": session.user_id,
        "preferences": {
            "display_format": session.display_format,
            "jurisdiction": session.jurisdiction,
            "department": session.department,
            "preferred_backend": session.preferred_backend,
            **session.preferences,
        },
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: UUID) -> Dict[str, Any]:
    """
    Get session information.

    Args:
        session_id: Session identifier

    Returns:
        Session information
    """
    session_memory = get_session_memory()
    session = await session_memory.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or expired",
        )

    return {
        "session_id": str(session.session_id),
        "user_id": session.user_id,
        "preferences": {
            "display_format": session.display_format,
            "jurisdiction": session.jurisdiction,
            "department": session.department,
            "preferred_backend": session.preferred_backend,
            **session.preferences,
        },
        "created_at": session.created_at.isoformat(),
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "last_accessed": session.last_accessed.isoformat() if session.last_accessed else None,
    }


@router.put("/sessions/{session_id}/preferences")
async def update_preferences(
    session_id: UUID,
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update session preferences.

    Args:
        session_id: Session identifier
        preferences: Preferences to update

    Returns:
        Updated session information
    """
    session_memory = get_session_memory()
    session = await session_memory.update_preferences(session_id, preferences)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or expired",
        )

    return {
        "session_id": str(session.session_id),
        "preferences": {
            "display_format": session.display_format,
            "jurisdiction": session.jurisdiction,
            "department": session.department,
            "preferred_backend": session.preferred_backend,
            **session.preferences,
        },
    }


@router.get("/policy/frequently-used")
async def get_frequently_used_documents(
    limit: int = 10,
    min_access_count: int = 5,
) -> Dict[str, Any]:
    """
    Get frequently used documents.

    Args:
        limit: Maximum number of documents
        min_access_count: Minimum access count

    Returns:
        List of frequently used documents
    """
    policy_memory = get_policy_memory()
    documents = await policy_memory.get_frequently_used_documents(
        limit=limit,
        min_access_count=min_access_count,
    )

    return {
        "documents": [
            {
                "doc_hash": doc.doc_hash,
                "document_id": doc.document_id,
                "access_count": doc.access_count,
                "last_accessed": doc.last_accessed.isoformat() if doc.last_accessed else None,
                "aliases": doc.aliases,
            }
            for doc in documents
        ],
        "count": len(documents),
    }


@router.post("/policy/aliases")
async def add_policy_alias(
    doc_hash: str,
    alias: str,
) -> Dict[str, Any]:
    """
    Add alias for a policy document.

    Args:
        doc_hash: Document hash
        alias: Alias name

    Returns:
        Success status
    """
    policy_memory = get_policy_memory()
    memory = await policy_memory.add_policy_alias(doc_hash, alias)

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with hash {doc_hash} not found",
        )

    return {
        "status": "success",
        "doc_hash": doc_hash,
        "alias": alias,
        "aliases": memory.aliases,
    }


@router.get("/policy/aliases/{alias}")
async def resolve_alias(alias: str) -> Dict[str, Any]:
    """
    Resolve policy alias.

    Args:
        alias: Alias name

    Returns:
        Policy information
    """
    policy_memory = get_policy_memory()
    memory = await policy_memory.resolve_alias(alias)

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alias '{alias}' not found",
        )

    return {
        "doc_hash": memory.doc_hash,
        "document_id": memory.document_id,
        "access_count": memory.access_count,
        "aliases": memory.aliases,
    }

