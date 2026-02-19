from __future__ import annotations

from llm_eval.config import ProviderConfig
from llm_eval.providers.anthropic_provider import AnthropicProvider
from llm_eval.providers.base import ProviderClient
from llm_eval.providers.gemini_provider import GeminiProvider
from llm_eval.providers.groq_provider import GroqProvider
from llm_eval.providers.openai_provider import OpenAIProvider


def build_provider_client(
    provider_config: ProviderConfig, timeout_seconds: int
) -> ProviderClient:
    if provider_config.provider == "openai":
        return OpenAIProvider(
            model=provider_config.model,
            api_key_env=provider_config.api_key_env or "OPENAI_API_KEY",
            timeout_seconds=timeout_seconds,
        )
    if provider_config.provider == "anthropic":
        return AnthropicProvider(
            model=provider_config.model,
            api_key_env=provider_config.api_key_env or "ANTHROPIC_API_KEY",
            timeout_seconds=timeout_seconds,
        )
    if provider_config.provider == "gemini":
        return GeminiProvider(
            model=provider_config.model,
            api_key_env=provider_config.api_key_env or "GEMINI_API_KEY",
            timeout_seconds=timeout_seconds,
        )
    if provider_config.provider == "groq":
        return GroqProvider(
            model=provider_config.model,
            api_key_env=provider_config.api_key_env or "GROQ_API_KEY",
            timeout_seconds=timeout_seconds,
        )
    raise NotImplementedError(
        f"Provider '{provider_config.provider}' is not implemented yet."
    )
