"""
Vertex AI Memory Bank — long-term facts per WhatsApp user (phone as user_id).

Disabled when VERTEX_AGENT_ENGINE_NAME is unset (local dev without Vertex).
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def _normalize_user_id(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    return digits or phone


class MemoryBankService:
    def __init__(self) -> None:
        self._engine_name = (settings.vertex_agent_engine_name or "").strip()
        self._region = (settings.google_cloud_region or "us-central1").strip()
        self._project = (
            (settings.google_cloud_project or "").strip()
            or None
        )
        self._client: Any = None

    @property
    def enabled(self) -> bool:
        return bool(self._engine_name)

    def _get_client(self) -> Any:
        if self._client is None:
            import vertexai

            project = self._project
            if not project:
                import os

                project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
            if not project:
                raise RuntimeError(
                    "Memory Bank needs GOOGLE_CLOUD_PROJECT or google_cloud_project in settings"
                )
            self._client = vertexai.Client(project=project, location=self._region)
        return self._client

    async def retrieve_facts(self, user_phone: str, search_text: str = "") -> list[str]:
        """Return memory facts for this user; empty if disabled or on error."""
        if not self.enabled:
            return []
        user_id = _normalize_user_id(user_phone)
        scope = {"user_id": user_id}

        def _retrieve() -> list[str]:
            client = self._get_client()
            facts: list[str] = []
            q = (search_text or "").strip()
            if q:
                results = client.agent_engines.memories.retrieve(
                    name=self._engine_name,
                    scope=scope,
                    similarity_search_params={"search_query": q, "top_k": 12},
                )
            else:
                results = client.agent_engines.memories.retrieve(
                    name=self._engine_name,
                    scope=scope,
                    simple_retrieval_params={"page_size": 12},
                )
            for item in results:
                mem = getattr(item, "memory", None)
                fact = getattr(mem, "fact", None) if mem else None
                if fact and str(fact).strip():
                    facts.append(str(fact).strip())
            return facts[:12]

        try:
            return await asyncio.to_thread(_retrieve)
        except Exception as e:
            logger.warning("Memory Bank retrieve failed for %s: %s", user_id, e)
            return []

    async def record_exchange(
        self,
        user_phone: str,
        turns: list[dict[str, str]],
        *,
        session_name: str | None = None,
    ) -> None:
        """
        Append turns to a Vertex session and trigger memory generation (non-blocking).
        turns: [{"role": "user"|"assistant", "content": "..."}]
        """
        if not self.enabled or not turns:
            return

        user_id = _normalize_user_id(user_phone)

        def _write() -> None:
            client = self._get_client()
            sess_name = session_name
            if not sess_name:
                session = client.agent_engines.sessions.create(
                    name=self._engine_name,
                    user_id=user_id,
                )
                sess_name = session.response.name

            invocation_id = 0
            for turn in turns:
                role = turn.get("role", "user")
                content = (turn.get("content") or "").strip()
                if not content:
                    continue
                gemini_role = "model" if role == "assistant" else "user"
                client.agent_engines.sessions.events.append(
                    name=sess_name,
                    author=user_id,
                    invocation_id=str(invocation_id),
                    timestamp=datetime.now(tz=timezone.utc),
                    config={
                        "content": {
                            "role": gemini_role,
                            "parts": [{"text": content[:8000]}],
                        }
                    },
                )
                invocation_id += 1

            client.agent_engines.memories.generate(
                name=self._engine_name,
                vertex_session_source={"session": sess_name},
                config={"wait_for_completion": False},
            )

        try:
            await asyncio.to_thread(_write)
        except Exception as e:
            logger.warning("Memory Bank record_exchange failed for %s: %s", user_id, e)


memory_bank_service = MemoryBankService()
