from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List


Priority = Literal["low_cost", "low_latency", "high_quality"]
Task = Literal["chat", "summarise", "extract", "classify", "rewrite", "qa"]


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt / input text")
    task: Task = Field("chat", description="Task hint for routing/system prompting")
    priority: Priority = Field("low_cost", description="Routing preference")
    max_output_tokens: int = Field(512, ge=1, le=4096)
    temperature: float = Field(0.2, ge=0.0, le=1.5)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    provider_hint: Optional[Literal["azure", "bedrock"]] = Field(
        None, description="Optional hard hint; routing may still override if invalid"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderUsage(BaseModel):
    input_tokens_est: int
    output_tokens_est: int
    total_tokens_est: int
    cost_est_usd: float


class ProviderResponse(BaseModel):
    provider: Literal["azure", "bedrock"]
    model: str
    text: str
    latency_ms: int
    usage: ProviderUsage
    raw: Optional[Dict[str, Any]] = None


class GenerateResponse(BaseModel):
    request_id: str
    chosen_provider: Literal["azure", "bedrock"]
    chosen_model: str
    text: str
    latency_ms: int
    fallback_used: bool
    attempts: List[ProviderResponse]
