from __future__ import annotations

import json
import time
from typing import Dict, Any, Optional

import boto3
from botocore.config import Config as BotoConfig

from .base import ProviderResult


class AwsBedrockProvider:
    provider_name = "bedrock"

    def __init__(self, *, region: str) -> None:
        # bedrock runtime client
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=BotoConfig(retries={"max_attempts": 2, "mode": "standard"}),
        )

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
        """
        Uses Bedrock 'invoke_model'. Payload format differs per model.
        This implementation targets Anthropic Claude-style messages API commonly used via Bedrock.

        Many Claude models accept:
        {
          "anthropic_version": "bedrock-2023-05-31",
          "max_tokens": ...,
          "temperature": ...,
          "top_p": ...,
          "messages": [{"role":"user","content":[{"type":"text","text":"..."}]}]
        }
        """
        body: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_output_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{system_prompt}\n\n{prompt}".strip()}
                    ],
                }
            ],
        }

        start = time.perf_counter()
        response = self.client.invoke_model(
            modelId=model_or_deployment,
            body=json.dumps(body).encode("utf-8"),
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        raw_bytes = response.get("body").read()
        data = json.loads(raw_bytes.decode("utf-8"))

        # Claude commonly returns: {"content":[{"type":"text","text":"..."}], ...}
        text = ""
        try:
            content = data.get("content", [])
            if content and isinstance(content, list):
                text = content[0].get("text", "")
            if not text:
                # fallback: some models may return "completion"
                text = data.get("completion", "")
        except Exception:
            raise RuntimeError(f"Unexpected Bedrock response format: {data}")

        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(f"Empty Bedrock completion. Raw: {data}")

        return ProviderResult(
            provider=self.provider_name,
            model=model_or_deployment,
            text=text,
            latency_ms=latency_ms,
            raw=data if isinstance(data, dict) else None,
        )
