from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Dict, Any, Optional


@dataclass
class ProviderResult:
    provider: str
    model: str
    text: str
    latency_ms: int
    raw: Optional[Dict[str, Any]] = None


class LLMProvider(Protocol):
    provider_name: str

    def generate(
        self,
        *,
        prompt: str,
        system_prompt: str,
        model_or_deployment: str,
        max_output_tokens: int,
        temperature: float,
        top_p: float,
        timeout_s: float,
    ) -> ProviderResult:
        ...
