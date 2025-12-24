"""Session memory service."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.models.session_memory import SessionMemory as SessionMemoryModel


class SessionMemory:
    """Service for managing session memory."""

    DEFAULT_EXPIRATION_DAYS = 30

    async def create_session(
        self,
        user_id: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        expiration_days: int = DEFAULT_EXPIRATION_DAYS,
    ) -> SessionMemoryModel:
        """
        Create a new session.

        Args:
            user_id: User identifier
            preferences: Initial preferences
            expiration_days: Session expiration in days

        Returns:
            Created session
        """
        session_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(days=expiration_days)

        session = SessionMemoryModel(
            session_id=session_id,
            user_id=user_id,
            preferences=preferences or {},
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        async for db_session in get_async_session():
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)
            return session

    async def get_session(self, session_id: UUID) -> Optional[SessionMemoryModel]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session or None if not found/expired
        """
        async for db_session in get_async_session():
            session = await db_session.get(SessionMemoryModel, session_id)
            if session and not session.is_expired():
                session.update_access()
                await db_session.commit()
                return session
            return None

    async def get_user_session(self, user_id: str) -> Optional[SessionMemoryModel]:
        """
        Get active session for user.

        Args:
            user_id: User identifier

        Returns:
            Most recent active session or None
        """
        async for db_session in get_async_session():
            from sqlalchemy import select

            stmt = (
                select(SessionMemoryModel)
                .where(SessionMemoryModel.user_id == user_id)
                .where(SessionMemoryModel.expires_at > datetime.utcnow())
                .order_by(SessionMemoryModel.last_accessed.desc())
                .limit(1)
            )
            result = await db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                session.update_access()
                await db_session.commit()
            
            return session

    async def update_preferences(
        self,
        session_id: UUID,
        preferences: Dict[str, Any],
    ) -> Optional[SessionMemoryModel]:
        """
        Update session preferences.

        Args:
            session_id: Session identifier
            preferences: Preferences to update

        Returns:
            Updated session or None if not found
        """
        async for db_session in get_async_session():
            session = await db_session.get(SessionMemoryModel, session_id)
            if session and not session.is_expired():
                # Update preferences
                session.preferences.update(preferences)
                
                # Update specific preference fields if provided
                if "display_format" in preferences:
                    session.display_format = preferences["display_format"]
                if "jurisdiction" in preferences:
                    session.jurisdiction = preferences["jurisdiction"]
                if "department" in preferences:
                    session.department = preferences["department"]
                if "preferred_backend" in preferences:
                    session.preferred_backend = preferences["preferred_backend"]
                
                session.update_access()
                await db_session.commit()
                await db_session.refresh(session)
                return session
            return None

    async def extend_session(self, session_id: UUID, days: int = DEFAULT_EXPIRATION_DAYS) -> Optional[SessionMemoryModel]:
        """
        Extend session expiration.

        Args:
            session_id: Session identifier
            days: Days to extend

        Returns:
            Updated session or None if not found
        """
        async for db_session in get_async_session():
            session = await db_session.get(SessionMemoryModel, session_id)
            if session:
                session.extend_expiration(days)
                session.update_access()
                await db_session.commit()
                await db_session.refresh(session)
                return session
            return None

    async def delete_session(self, session_id: UUID) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        async for db_session in get_async_session():
            session = await db_session.get(SessionMemoryModel, session_id)
            if session:
                await db_session.delete(session)
                await db_session.commit()
                return True
            return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions deleted
        """
        async for db_session in get_async_session():
            from sqlalchemy import delete, select

            # Find expired sessions
            stmt = select(SessionMemoryModel).where(SessionMemoryModel.expires_at < datetime.utcnow())
            result = await db_session.execute(stmt)
            expired_sessions = result.scalars().all()

            count = len(expired_sessions)
            for session in expired_sessions:
                await db_session.delete(session)

            await db_session.commit()
            return count

    async def get_preferences(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get session preferences.

        Args:
            session_id: Session identifier

        Returns:
            Preferences dictionary or None
        """
        session = await self.get_session(session_id)
        if session:
            return {
                "display_format": session.display_format,
                "jurisdiction": session.jurisdiction,
                "department": session.department,
                "preferred_backend": session.preferred_backend,
                **session.preferences,
            }
        return None


# Global instance
_session_memory: Optional[SessionMemory] = None


def get_session_memory() -> SessionMemory:
    """Get global session memory instance."""
    global _session_memory
    if _session_memory is None:
        _session_memory = SessionMemory()
    return _session_memory

