from __future__ import annotations

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.llm import LLMRouter
from app.services.llm.base import LLMClient


def get_llm_client(
    settings: Settings = Depends(get_settings),
) -> LLMClient:
    return LLMRouter(settings)
