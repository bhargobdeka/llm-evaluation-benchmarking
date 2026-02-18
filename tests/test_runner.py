from pathlib import Path

from llm_eval.config import load_run_config
from llm_eval.providers.base import InferenceRequest, InferenceResponse
from llm_eval.runner import run_evaluation


class FakeProvider:
    provider_name = "fake"

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        _ = request
        return InferenceResponse(
            text="B",
            model="fake-model",
            provider=self.provider_name,
            latency_ms=1,
            usage=None,
        )


def test_runner_writes_artifacts_and_resumes(monkeypatch, tmp_path: Path) -> None:
    config = load_run_config("configs/run.example.yaml")
    config.benchmark.max_samples = 2

    def _fake_factory(provider_config, timeout_seconds):  # noqa: ANN001, ANN202
        _ = timeout_seconds
        return FakeProvider(provider_name=provider_config.provider)

    monkeypatch.setattr("llm_eval.runner.build_provider_client", _fake_factory)

    summary_first = run_evaluation(
        config=config,
        policy_path="configs/policy.yaml",
        artifacts_root=str(tmp_path / "artifacts"),
    )
    run_dir = tmp_path / "artifacts" / "runs" / summary_first.run_id
    assert run_dir.exists()
    results_lines_first = (run_dir / "results.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(results_lines_first) == 4

    summary_second = run_evaluation(
        config=config,
        policy_path="configs/policy.yaml",
        artifacts_root=str(tmp_path / "artifacts"),
    )
    assert summary_first.run_id == summary_second.run_id
    results_lines_second = (run_dir / "results.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(results_lines_second) == 4
