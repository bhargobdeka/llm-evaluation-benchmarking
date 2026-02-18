from llm_eval.config import build_run_manifest, load_run_config, resolve_provider_keys


def test_load_run_config() -> None:
    config = load_run_config("configs/run.example.yaml")
    assert config.run_name == "phase1-baseline"
    assert len(config.providers) == 3
    assert config.benchmark.name == "mmlu_subset"


def test_manifest_has_stable_shape() -> None:
    config = load_run_config("configs/run.example.yaml")
    manifest = build_run_manifest(config)
    assert len(manifest.run_id) == 16
    assert manifest.benchmark["name"] == "mmlu_subset"
    assert len(manifest.providers) == 3


def test_resolve_provider_keys_returns_expected_map() -> None:
    config = load_run_config("configs/run.example.yaml")
    resolved = resolve_provider_keys(config, env_path=".env.example")
    assert set(resolved.keys()) == {"anthropic", "openai", "gemini"}
