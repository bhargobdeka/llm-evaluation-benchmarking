from llm_eval.config import ProviderConfig
from llm_eval.providers.factory import build_provider_client
from llm_eval.providers.groq_provider import GroqProvider


def test_factory_builds_groq_provider() -> None:
    cfg = ProviderConfig(provider="groq", model="qwen/qwen3-32b", api_key_env="GROQ_API_KEY")
    client = build_provider_client(cfg, timeout_seconds=10)
    assert isinstance(client, GroqProvider)
