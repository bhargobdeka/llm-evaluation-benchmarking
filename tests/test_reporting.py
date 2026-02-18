from llm_eval.reporting import build_markdown_report


def test_markdown_report_contains_sections() -> None:
    scored = {
        "status": "completed",
        "total_rows": 4,
        "providers": {
            "anthropic": {
                "attempted": 2,
                "correct": 2,
                "accuracy": 1.0,
                "avg_latency_ms": 123.0,
                "errors": 0,
                "accuracy_ci95": {"low": 0.34, "high": 1.0},
                "categories": {"math": {"attempted": 2, "correct": 2, "accuracy": 1.0}},
            }
        },
    }
    pairwise = []
    report = build_markdown_report("run123", scored, pairwise)
    assert "# Evaluation Report: run123" in report
    assert "## Leaderboard" in report
    assert "## Category Breakdown" in report
