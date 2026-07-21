from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.database import AsyncSessionFactory
from app.memory.models import MemoryEntryModel
from app.schemas.memory import MemoryEntry, MemoryWriteRequest, MemoryQueryRequest
from app.services.embedding import embed

MAX_ENTRIES_PER_SESSION = 50
EVICTION_KEEP = 10


class MemoryStore:
    """
    pgvector-backed memory store with per-agent/session isolation.
    Every query filters on (agent_id, session_id, user_id) —
    Agent A can never read Agent B's memory even in the same session.
    """

    # ── Write ─────────────────────────────────────────────────────────────────

    async def write(self, request: MemoryWriteRequest) -> MemoryEntry:
        vector = embed(request.content)

        async with AsyncSessionFactory() as session:
            async with session.begin():
                entry = MemoryEntryModel(
                    agent_id=request.agent_id,
                    session_id=request.session_id,
                    user_id=request.user_id,
                    content=request.content,
                    embedding=vector,
                    metadata_=request.metadata,
                )
                session.add(entry)

        # Eviction check after write (separate transaction)
        await self._maybe_evict(request)
        return self._to_schema(entry)

    # ── Semantic query ────────────────────────────────────────────────────────

    async def query(self, request: MemoryQueryRequest) -> list[MemoryEntry]:
        """
        Returns top_k most semantically similar entries for the agent+session.
        Uses pgvector cosine distance operator (<=>).
        """
        query_vector = embed(request.query)

        async with AsyncSessionFactory() as session:
            stmt = (
                select(MemoryEntryModel)
                .where(
                    MemoryEntryModel.agent_id == request.agent_id,
                    MemoryEntryModel.session_id == request.session_id,
                    MemoryEntryModel.user_id == request.user_id,
                )
                .order_by(
                    MemoryEntryModel.embedding.cosine_distance(query_vector)
                )
                .limit(request.top_k)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

        return [self._to_schema(r) for r in rows]

    # ── Clear session ─────────────────────────────────────────────────────────

    async def clear_session(self, agent_id: str, session_id: str) -> None:
        async with AsyncSessionFactory() as session:
            async with session.begin():
                await session.execute(
                    delete(MemoryEntryModel).where(
                        MemoryEntryModel.agent_id == agent_id,
                        MemoryEntryModel.session_id == session_id,
                    )
                )

    # ── Eviction + summarization ──────────────────────────────────────────────

    async def _maybe_evict(self, request: MemoryWriteRequest) -> None:
        """
        If session memory exceeds MAX_ENTRIES_PER_SESSION:
        1. Fetch oldest (count - EVICTION_KEEP) entries
        2. Summarize them via LLM
        3. Delete those entries
        4. Write the summary as one compressed entry

        Memory stays bounded; semantic context is preserved via summary.
        """
        async with AsyncSessionFactory() as session:
            count_result = await session.execute(
                select(func.count()).where(
                    MemoryEntryModel.agent_id == request.agent_id,
                    MemoryEntryModel.session_id == request.session_id,
                    MemoryEntryModel.user_id == request.user_id,
                )
            )
            count = count_result.scalar_one()

            if count <= MAX_ENTRIES_PER_SESSION:
                return

            evict_count = count - EVICTION_KEEP
            oldest_result = await session.execute(
                select(MemoryEntryModel)
                .where(
                    MemoryEntryModel.agent_id == request.agent_id,
                    MemoryEntryModel.session_id == request.session_id,
                    MemoryEntryModel.user_id == request.user_id,
                )
                .order_by(MemoryEntryModel.created_at.asc())
                .limit(evict_count)
            )
            old_entries = oldest_result.scalars().all()

            if not old_entries:
                return

            summary = await self._summarize_entries(old_entries)
            old_ids = [e.id for e in old_entries]

            async with session.begin():
                await session.execute(
                    delete(MemoryEntryModel).where(
                        MemoryEntryModel.id.in_(old_ids)
                    )
                )
                summary_entry = MemoryEntryModel(
                    agent_id=request.agent_id,
                    session_id=request.session_id,
                    user_id=request.user_id,
                    content=f'[SUMMARY] {summary}',
                    embedding=embed(summary),
                    metadata_={'evicted_count': evict_count, 'is_summary': True},
                )
                session.add(summary_entry)

    async def _summarize_entries(self, entries: list[MemoryEntryModel]) -> str:
        from app.services.llm import get_sync_llm
        from langchain_core.messages import HumanMessage

        combined = '\n'.join(f'- {e.content}' for e in entries)
        prompt = (
            'Summarize these memory entries into 2-3 concise sentences '
            f'preserving the most important facts:\n\n{combined}'
        )
        try:
            llm = get_sync_llm()
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            return result.content.strip()
        except Exception:
            return combined[:500] + '...'

    # ── Schema conversion ─────────────────────────────────────────────────────

    @staticmethod
    def _to_schema(model: MemoryEntryModel) -> MemoryEntry:
        return MemoryEntry(
            id=str(model.id),
            agent_id=model.agent_id,
            session_id=model.session_id,
            user_id=model.user_id,
            content=model.content,
            embedding=model.embedding,
            metadata=model.metadata_,
            created_at=model.created_at or datetime.utcnow(),
        )


# Singleton — imported by agents and nodes
memory_store = MemoryStore()
