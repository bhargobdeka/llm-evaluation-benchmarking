from llm_eval.scoring import score_results
from llm_eval.stats import add_confidence_intervals, pairwise_significance, wilson_confidence_interval


def test_score_results_builds_provider_metrics() -> None:
    results = [
        {
            "system_id": "anthropic:claude-3-5-haiku-latest",
            "provider": "anthropic",
            "model": "claude-3-5-haiku-latest",
            "sample_id": "s1",
            "category": "math",
            "is_correct": True,
            "latency_ms": 100,
        },
        {
            "system_id": "anthropic:claude-3-5-haiku-latest",
            "provider": "anthropic",
            "model": "claude-3-5-haiku-latest",
            "sample_id": "s2",
            "category": "science",
            "is_correct": False,
            "latency_ms": 200,
        },
        {
            "system_id": "gemini:gemini-2.0-flash",
            "provider": "gemini",
            "model": "gemini-2.0-flash",
            "sample_id": "s1",
            "category": "math",
            "is_correct": False,
            "latency_ms": 150,
        },
    ]
    summary = {
        "status": "completed",
        "provider_metrics": {
            "anthropic:claude-3-5-haiku-latest": {"errors": 0},
            "gemini:gemini-2.0-flash": {"errors": 1},
        },
    }
    scored = score_results(results, summary)
    assert scored["providers"]["anthropic:claude-3-5-haiku-latest"]["attempted"] == 2
    assert scored["providers"]["anthropic:claude-3-5-haiku-latest"]["correct"] == 1
    assert scored["providers"]["gemini:gemini-2.0-flash"]["errors"] == 1


def test_stats_functions_output_expected_shapes() -> None:
    lo, hi = wilson_confidence_interval(8, 10)
    assert 0 <= lo <= hi <= 1

    scored = {"providers": {"anthropic": {"attempted": 10, "correct": 8}}}
    scored = add_confidence_intervals(scored)
    assert "accuracy_ci95" in scored["providers"]["anthropic"]

    pairwise = pairwise_significance(
        [
            {"system_id": "anthropic:claude-3-5-haiku-latest", "sample_id": "1", "is_correct": True},
            {"system_id": "gemini:gemini-2.0-flash", "sample_id": "1", "is_correct": False},
            {"system_id": "anthropic:claude-3-5-haiku-latest", "sample_id": "2", "is_correct": False},
            {"system_id": "gemini:gemini-2.0-flash", "sample_id": "2", "is_correct": False},
        ]
    )
    assert len(pairwise) == 1
    assert pairwise[0]["provider_a"] == "anthropic:claude-3-5-haiku-latest"
