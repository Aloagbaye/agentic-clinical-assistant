"""Policy memory service."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.models.policy_memory import PolicyMemory, QueryPattern


class PolicyMemory:
    """Service for managing policy memory."""

    async def get_or_create_policy_memory(
        self,
        doc_hash: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PolicyMemory:
        """
        Get or create policy memory for a document.

        Args:
            doc_hash: Document hash
            document_id: Document identifier
            metadata: Document metadata

        Returns:
            Policy memory record
        """
        async for db_session in get_async_session():
            from sqlalchemy import select

            # Try to find existing memory
            stmt = select(PolicyMemory).where(PolicyMemory.doc_hash == doc_hash)
            result = await db_session.execute(stmt)
            memory = result.scalar_one_or_none()

            if memory:
                return memory

            # Create new memory
            memory = PolicyMemory(
                doc_hash=doc_hash,
                document_id=document_id,
                metadata=metadata or {},
                first_accessed=datetime.utcnow(),
            )
            db_session.add(memory)
            await db_session.commit()
            await db_session.refresh(memory)
            return memory

    async def record_document_access(
        self,
        doc_hash: str,
        document_id: Optional[str] = None,
        query_type: Optional[str] = None,
    ) -> PolicyMemory:
        """
        Record document access.

        Args:
            doc_hash: Document hash
            document_id: Document identifier
            query_type: Type of query that accessed the document

        Returns:
            Updated policy memory
        """
        memory = await self.get_or_create_policy_memory(doc_hash, document_id)
        
        async for db_session in get_async_session():
            memory.increment_access()
            if query_type:
                memory.add_query_pattern(query_type)
            await db_session.commit()
            await db_session.refresh(memory)
            return memory

    async def record_successful_query(
        self,
        doc_hash: str,
        query_type: Optional[str] = None,
    ) -> None:
        """
        Record successful query for a document.

        Args:
            doc_hash: Document hash
            query_type: Type of query
        """
        async for db_session in get_async_session():
            from sqlalchemy import select

            stmt = select(PolicyMemory).where(PolicyMemory.doc_hash == doc_hash)
            result = await db_session.execute(stmt)
            memory = result.scalar_one_or_none()

            if memory:
                memory.record_successful_query()
                if query_type:
                    memory.add_query_pattern(query_type)
                await db_session.commit()

    async def get_frequently_used_documents(
        self,
        limit: int = 10,
        min_access_count: int = 5,
    ) -> List[PolicyMemory]:
        """
        Get frequently used documents.

        Args:
            limit: Maximum number of documents to return
            min_access_count: Minimum access count threshold

        Returns:
            List of frequently used documents
        """
        async for db_session in get_async_session():
            from sqlalchemy import select

            stmt = (
                select(PolicyMemory)
                .where(PolicyMemory.access_count >= min_access_count)
                .order_by(PolicyMemory.access_count.desc())
                .limit(limit)
            )
            result = await db_session.execute(stmt)
            return list(result.scalars().all())

    async def add_policy_alias(
        self,
        doc_hash: str,
        alias: str,
    ) -> Optional[PolicyMemory]:
        """
        Add alias for a policy document.

        Args:
            doc_hash: Document hash
            alias: Alias name

        Returns:
            Updated policy memory or None
        """
        async for db_session in get_async_session():
            from sqlalchemy import select

            stmt = select(PolicyMemory).where(PolicyMemory.doc_hash == doc_hash)
            result = await db_session.execute(stmt)
            memory = result.scalar_one_or_none()

            if memory:
                memory.add_alias(alias)
                await db_session.commit()
                await db_session.refresh(memory)
                return memory
            return None

    async def resolve_alias(self, alias: str) -> Optional[PolicyMemory]:
        """
        Resolve policy alias to document.

        Args:
            alias: Alias name

        Returns:
            Policy memory or None if alias not found
        """
        async for db_session in get_async_session():
            from sqlalchemy import select

            # Search for alias in aliases JSON field
            stmt = select(PolicyMemory).where(PolicyMemory.aliases.contains([alias]))
            result = await db_session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_query_pattern(
        self,
        query_type: str,
        department: Optional[str] = None,
    ) -> Optional[QueryPattern]:
        """
        Get query pattern for a query type.

        Args:
            query_type: Type of query
            department: Department filter

        Returns:
            Query pattern or None
        """
        async for db_session in get_async_session():
            from sqlalchemy import select

            stmt = select(QueryPattern).where(QueryPattern.query_type == query_type)
            if department:
                stmt = stmt.where(QueryPattern.department == department)
            
            result = await db_session.execute(stmt)
            return result.scalar_one_or_none()

    async def record_query_pattern(
        self,
        query_type: str,
        query_template: str,
        department: Optional[str] = None,
        backend: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        success: bool = True,
        latency_ms: Optional[float] = None,
    ) -> QueryPattern:
        """
        Record or update query pattern.

        Args:
            query_type: Type of query
            query_template: Query template (no patient data)
            department: Department
            backend: Backend used
            filters: Filters used
            success: Whether query was successful
            latency_ms: Query latency

        Returns:
            Query pattern record
        """
        async for db_session in get_async_session():
            from sqlalchemy import select

            # Try to find existing pattern
            stmt = select(QueryPattern).where(QueryPattern.query_type == query_type)
            if department:
                stmt = stmt.where(QueryPattern.department == department)
            
            result = await db_session.execute(stmt)
            pattern = result.scalar_one_or_none()

            if pattern:
                pattern.increment_usage()
                pattern.update_success_rate(success)
                if backend and backend not in pattern.common_backends:
                    pattern.common_backends.append(backend)
                if filters:
                    # Merge filters
                    for key, value in filters.items():
                        if key not in pattern.common_filters:
                            pattern.common_filters[key] = value
                if latency_ms:
                    # Update average latency
                    if pattern.avg_latency_ms is None:
                        pattern.avg_latency_ms = latency_ms
                    else:
                        pattern.avg_latency_ms = (pattern.avg_latency_ms + latency_ms) / 2
            else:
                # Create new pattern
                pattern = QueryPattern(
                    query_type=query_type,
                    query_template=query_template,
                    department=department,
                    usage_count=1,
                    success_rate=1.0 if success else 0.0,
                    avg_latency_ms=latency_ms,
                    common_backends=[backend] if backend else [],
                    common_filters=filters or {},
                    created_at=datetime.utcnow(),
                    last_used=datetime.utcnow(),
                )
                db_session.add(pattern)

            await db_session.commit()
            await db_session.refresh(pattern)
            return pattern


# Global instance
_policy_memory: Optional[PolicyMemory] = None


def get_policy_memory() -> PolicyMemory:
    """Get global policy memory instance."""
    global _policy_memory
    if _policy_memory is None:
        _policy_memory = PolicyMemory()
    return _policy_memory

