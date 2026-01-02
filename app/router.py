from __future__ import annotations

import uuid
from typing import Tuple, List, Dict, Any

from .models import GenerateRequest, ProviderResponse
from .providers.azure_openai import AzureOpenAIProvider
from .providers.aws_bedrock import AwsBedrockProvider
from .cost_tracker import estimate_cost, UsageLogger
from .config import AppConfig, AzureConfig, BedrockConfig


def build_system_prompt(task: str) -> str:
    base = (
        "You are a helpful enterprise assistant. "
        "Be concise, correct, and safe. "
        "If the user requests sensitive personal data, refuse. "
        "If uncertain, say you are uncertain and ask a short clarifying question."
    )
    task_hints = {
        "summarise": "Summarise the input in bullet points, capturing key facts and decisions.",
        "extract": "Extract key entities/fields as JSON. If a field is missing, set it to null.",
        "classify": "Classify the input into a small set of labels and explain briefly.",
        "rewrite": "Rewrite for clarity and professionalism without changing meaning.",
        "qa": "Answer the question using the provided text. If missing context, say so.",
        "chat": "Respond naturally and helpfully.",
    }
    return f"{base}\n\nTask: {task_hints.get(task, task_hints['chat'])}"


def choose_models(req: GenerateRequest, azure: AzureConfig, bedrock: BedrockConfig) -> Tuple[Tuple[str, str], Tuple[str, str]]:
    """
    Returns:
      primary: (provider_name, model_or_deployment)
      secondary: (provider_name, model_or_deployment)
    """
    # If user hints provider, we respect it for primary where possible.
    # Still keep a fallback.
    priority = req.priority

    # Simple routing:
    # - low_cost -> Azure low-cost deployment first
    # - high_quality -> Bedrock high-quality first (often Claude is strong); fallback to Azure high-quality
    # - low_latency -> Azure low-latency first; fallback to Bedrock low-latency
    if priority == "low_cost":
        primary =  ("bedrock", bedrock.model_low_cost)
        secondary =("azure", azure.deployment_low_cost)
    elif priority == "high_quality":
        primary = ("bedrock", bedrock.model_high_quality)
        secondary = ("azure", azure.deployment_high_quality)
    else:  # low_latency
        primary = ("azure", azure.deployment_low_latency)
        secondary = ("bedrock", bedrock.model_low_latency)

    # Apply provider_hint by swapping order if needed
    if req.provider_hint == "azure" and primary[0] != "azure":
        primary, secondary = secondary, primary
    elif req.provider_hint == "bedrock" and primary[0] != "bedrock":
        primary, secondary = secondary, primary

    return primary, secondary


def run_generation(
    *,
    app_cfg: AppConfig,
    azure_cfg: AzureConfig,
    bedrock_cfg: BedrockConfig,
    req: GenerateRequest,
    azure_provider: AzureOpenAIProvider,
    bedrock_provider: AwsBedrockProvider,
    usage_logger: UsageLogger,
) -> Dict[str, Any]:
    request_id = str(uuid.uuid4())
    system_prompt = build_system_prompt(req.task)
    primary, secondary = choose_models(req, azure_cfg, bedrock_cfg)

    attempts: List[ProviderResponse] = []
    fallback_used = False

    def call(provider_name: str, model_id: str) -> ProviderResponse:
        if provider_name == "azure":
            result = azure_provider.generate(
                prompt=req.prompt,
                system_prompt=system_prompt,
                model_or_deployment=model_id,
                max_output_tokens=req.max_output_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                timeout_s=app_cfg.hard_timeout_s,
            )
            est = estimate_cost(
                provider="azure",
                prompt=req.prompt,
                output_text=result.text,
                cost_per_1k_input_usd=app_cfg.azure_cost_per_1k_input_usd,
                cost_per_1k_output_usd=app_cfg.azure_cost_per_1k_output_usd,
            )
        else:
            result = bedrock_provider.generate(
                prompt=req.prompt,
                system_prompt=system_prompt,
                model_or_deployment=model_id,
                max_output_tokens=req.max_output_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                timeout_s=app_cfg.hard_timeout_s,
            )
            est = estimate_cost(
                provider="bedrock",
                prompt=req.prompt,
                output_text=result.text,
                cost_per_1k_input_usd=app_cfg.bedrock_cost_per_1k_input_usd,
                cost_per_1k_output_usd=app_cfg.bedrock_cost_per_1k_output_usd,
            )

        # log success
        if app_cfg.enable_request_logging:
            usage_logger.log(
                request_id=request_id,
                provider=provider_name,
                model=model_id,
                task=req.task,
                priority=req.priority,
                estimate=est,
                latency_ms=result.latency_ms,
                success=True,
                error=None,
            )

        return ProviderResponse(
            provider=provider_name,  # type: ignore
            model=model_id,
            text=result.text,
            latency_ms=result.latency_ms,
            usage={
                "input_tokens_est": est.input_tokens_est,
                "output_tokens_est": est.output_tokens_est,
                "total_tokens_est": est.total_tokens_est,
                "cost_est_usd": est.cost_est_usd,
            },
            raw=None,  # keep responses lean; set to result.raw if you want debugging
        )

    # Try primary
    try:
        pr = call(primary[0], primary[1])
        attempts.append(pr)
        chosen = pr
    except Exception as e1:
        # log failure primary
        if app_cfg.enable_request_logging:
            # estimate cost with empty output
            from .cost_tracker import CostEstimate, est_tokens
            est = CostEstimate(
                input_tokens_est=est_tokens(req.prompt),
                output_tokens_est=0,
                total_tokens_est=est_tokens(req.prompt),
                cost_est_usd=0.0,
            )
            usage_logger.log(
                request_id=request_id,
                provider=primary[0],
                model=primary[1],
                task=req.task,
                priority=req.priority,
                estimate=est,
                latency_ms=0,
                success=False,
                error=str(e1)[:500],
            )

        # Try secondary
        fallback_used = True
        try:
            sr = call(secondary[0], secondary[1])
            attempts.append(sr)
            chosen = sr
        except Exception as e2:
            if app_cfg.enable_request_logging:
                from .cost_tracker import CostEstimate, est_tokens
                est = CostEstimate(
                    input_tokens_est=est_tokens(req.prompt),
                    output_tokens_est=0,
                    total_tokens_est=est_tokens(req.prompt),
                    cost_est_usd=0.0,
                )
                usage_logger.log(
                    request_id=request_id,
                    provider=secondary[0],
                    model=secondary[1],
                    task=req.task,
                    priority=req.priority,
                    estimate=est,
                    latency_ms=0,
                    success=False,
                    error=str(e2)[:500],
                )
            raise RuntimeError(f"Both providers failed. Primary: {e1}; Secondary: {e2}")

    return {
        "request_id": request_id,
        "chosen_provider": chosen.provider,
        "chosen_model": chosen.model,
        "text": chosen.text,
        "latency_ms": chosen.latency_ms,
        "fallback_used": fallback_used,
        "attempts": [a.model_dump() for a in attempts],
    }
