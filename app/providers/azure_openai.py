from __future__ import annotations

import time
from typing import Dict, Any, Optional

import httpx

from .base import ProviderResult


class AzureOpenAIProvider:
    provider_name = "azure"

    def __init__(self, *, endpoint: str, api_key: str, api_version: str) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.api_version = api_version

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
        Uses Azure OpenAI Chat Completions REST API:
        POST {endpoint}/openai/deployments/{deployment}/chat/completions?api-version=...
        """
        url = (
            f"{self.endpoint}/openai/deployments/{model_or_deployment}/chat/completions"
            f"?api-version={self.api_version}"
        )

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_output_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

        start = time.perf_counter()
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
            latency_ms = int((time.perf_counter() - start) * 1000)

        if resp.status_code >= 400:
            raise RuntimeError(f"Azure OpenAI error {resp.status_code}: {resp.text}")

        data = resp.json()
        text = ""
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception:
            raise RuntimeError(f"Unexpected Azure response format: {data}")

        return ProviderResult(
            provider=self.provider_name,
            model=model_or_deployment,
            text=text,
            latency_ms=latency_ms,
            raw=data if isinstance(data, dict) else None,
        )
