from llm_eval.scoring import score_results
from llm_eval.stats import add_confidence_intervals, pairwise_significance, wilson_confidence_interval


def test_score_results_builds_provider_metrics() -> None:
    results = [
        {
            "provider": "anthropic",
            "sample_id": "s1",
            "category": "math",
            "is_correct": True,
            "latency_ms": 100,
        },
        {
            "provider": "anthropic",
            "sample_id": "s2",
            "category": "science",
            "is_correct": False,
            "latency_ms": 200,
        },
        {
            "provider": "gemini",
            "sample_id": "s1",
            "category": "math",
            "is_correct": False,
            "latency_ms": 150,
        },
    ]
    summary = {"status": "completed", "provider_metrics": {"anthropic": {"errors": 0}, "gemini": {"errors": 1}}}
    scored = score_results(results, summary)
    assert scored["providers"]["anthropic"]["attempted"] == 2
    assert scored["providers"]["anthropic"]["correct"] == 1
    assert scored["providers"]["gemini"]["errors"] == 1


def test_stats_functions_output_expected_shapes() -> None:
    lo, hi = wilson_confidence_interval(8, 10)
    assert 0 <= lo <= hi <= 1

    scored = {"providers": {"anthropic": {"attempted": 10, "correct": 8}}}
    scored = add_confidence_intervals(scored)
    assert "accuracy_ci95" in scored["providers"]["anthropic"]

    pairwise = pairwise_significance(
        [
            {"provider": "anthropic", "sample_id": "1", "is_correct": True},
            {"provider": "gemini", "sample_id": "1", "is_correct": False},
            {"provider": "anthropic", "sample_id": "2", "is_correct": False},
            {"provider": "gemini", "sample_id": "2", "is_correct": False},
        ]
    )
    assert len(pairwise) == 1
    assert pairwise[0]["provider_a"] == "anthropic"
