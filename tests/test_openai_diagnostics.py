from llm_eval.connectivity import diagnose_openai_endpoints


def test_openai_diagnostics_missing_key(monkeypatch) -> None:
    monkeypatch.setattr("llm_eval.connectivity.load_env_file", lambda env_path: None)
    monkeypatch.setattr("llm_eval.connectivity.os.getenv", lambda k, default="": "")
    diagnostics = diagnose_openai_endpoints(env_var="OPENAI_API_KEY", env_path=".env")
    assert len(diagnostics) == 1
    assert diagnostics[0].ok is False
    assert diagnostics[0].endpoint == "key_presence"
