from llm_eval.config import load_run_config
from llm_eval.connectivity import check_connectivity, redact_secrets
from llm_eval.providers.base import InferenceRequest, InferenceResponse


class FakeProvider:
    def __init__(self, provider: str):
        self.provider = provider

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        _ = request
        if self.provider == "openai":
            raise RuntimeError("Incorrect API key provided: sk-abc123456789xyz")
        return InferenceResponse(
            text="A",
            model="fake-model",
            provider=self.provider,
            latency_ms=1,
            usage=None,
        )


def test_redact_secrets_masks_openai_key() -> None:
    text = "bad key sk-abc123456789xyz and should be hidden"
    redacted = redact_secrets(text)
    assert "sk-abc123456789xyz" not in redacted
    assert "[REDACTED_KEY]" in redacted


def test_check_connectivity_returns_status(monkeypatch) -> None:
    config = load_run_config("configs/run.example.yaml")

    def _fake_factory(provider_config, timeout_seconds):  # noqa: ANN001, ANN202
        _ = timeout_seconds
        return FakeProvider(provider=provider_config.provider)

    monkeypatch.setattr("llm_eval.connectivity.build_provider_client", _fake_factory)
    monkeypatch.setattr("llm_eval.connectivity.load_env_file", lambda env_path: None)

    results = check_connectivity(config, env_path=".env")
    assert len(results) == 2
    assert any(result.provider == "anthropic" and result.ok for result in results)
    assert any(result.provider == "gemini" and result.ok for result in results)
