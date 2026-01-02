from __future__ import annotations

import os
from dataclasses import dataclass


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    v = os.getenv(name, default)
    if required and (v is None or v.strip() == ""):
        raise ValueError(f"Missing required environment variable: {name}")
    return v  # type: ignore


@dataclass(frozen=True)
class AzureConfig:
    endpoint: str
    api_key: str
    api_version: str
    # "deployment" is the Azure OpenAI deployment name (not the model name)
    deployment_low_cost: str
    deployment_high_quality: str
    deployment_low_latency: str


@dataclass(frozen=True)
class BedrockConfig:
    region: str
    model_low_cost: str
    model_high_quality: str
    model_low_latency: str


@dataclass(frozen=True)
class AppConfig:
    env: str
    log_db_path: str
    # routing settings
    hard_timeout_s: float
    enable_request_logging: bool
    # cost model (approx, adjust to taste)
    azure_cost_per_1k_input_usd: float
    azure_cost_per_1k_output_usd: float
    bedrock_cost_per_1k_input_usd: float
    bedrock_cost_per_1k_output_usd: float


def load_config() -> tuple[AppConfig, AzureConfig, BedrockConfig]:
    app = AppConfig(
        env=_get_env("APP_ENV", "dev"),
        log_db_path=_get_env("LOG_DB_PATH", "./usage_logs.sqlite"),
        hard_timeout_s=float(_get_env("HARD_TIMEOUT_S", "20")),
        enable_request_logging=_get_env("ENABLE_REQUEST_LOGGING", "true").lower() == "true",
        azure_cost_per_1k_input_usd=float(_get_env("AZURE_COST_PER_1K_INPUT_USD", "0.00015")),
        azure_cost_per_1k_output_usd=float(_get_env("AZURE_COST_PER_1K_OUTPUT_USD", "0.00060")),
        bedrock_cost_per_1k_input_usd=float(_get_env("BEDROCK_COST_PER_1K_INPUT_USD", "0.00025")),
        bedrock_cost_per_1k_output_usd=float(_get_env("BEDROCK_COST_PER_1K_OUTPUT_USD", "0.00125")),
    )

    azure = AzureConfig(
        endpoint=_get_env("AZURE_OPENAI_ENDPOINT", required=True),
        api_key=_get_env("AZURE_OPENAI_API_KEY", required=True),
        api_version=_get_env("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        deployment_low_cost=_get_env("AZURE_DEPLOYMENT_LOW_COST", required=True),
        deployment_high_quality=_get_env("AZURE_DEPLOYMENT_HIGH_QUALITY", required=True),
        deployment_low_latency=_get_env("AZURE_DEPLOYMENT_LOW_LATENCY", required=True),
    )

    bedrock = BedrockConfig(
        region=_get_env("AWS_REGION", required=True),
        model_low_cost=_get_env("BEDROCK_MODEL_LOW_COST", required=True),
        model_high_quality=_get_env("BEDROCK_MODEL_HIGH_QUALITY", required=True),
        model_low_latency=_get_env("BEDROCK_MODEL_LOW_LATENCY", required=True),
    )

    return app, azure, bedrock
