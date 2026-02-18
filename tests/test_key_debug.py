from llm_eval.connectivity import get_key_debug_info


def test_get_key_debug_info_for_present_key(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_DEBUG_KEY= sk-test1234567890abcd \n", encoding="utf-8")
    info = get_key_debug_info("TEST_DEBUG_KEY", env_path=str(env_file))
    assert info.present is True
    assert info.length > 10
    assert info.starts_with.startswith("sk-")
    assert info.has_whitespace is False
