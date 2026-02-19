from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_results(run_dir: str | Path) -> list[dict[str, Any]]:
    path = Path(run_dir) / "results.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_summary(run_dir: str | Path) -> dict[str, Any]:
    path = Path(run_dir) / "summary.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_system_id(row: dict[str, Any]) -> str:
    if row.get("system_id"):
        return str(row["system_id"])
    provider = str(row.get("provider", "unknown"))
    model = str(row.get("model", "unknown"))
    return f"{provider}:{model}"


def score_results(results: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    by_system: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "provider": "",
            "model": "",
            "attempted": 0,
            "correct": 0,
            "accuracy": 0.0,
            "avg_latency_ms": 0.0,
            "categories": defaultdict(lambda: {"attempted": 0, "correct": 0, "accuracy": 0.0}),
        }
    )

    for row in results:
        system_id = _resolve_system_id(row)
        provider = str(row.get("provider", "unknown"))
        model = str(row.get("model", "unknown"))
        is_correct = bool(row.get("is_correct", False))
        category = str(row.get("category", "unknown"))
        latency = float(row.get("latency_ms") or 0)

        system_bucket = by_system[system_id]
        system_bucket["provider"] = provider
        system_bucket["model"] = model
        system_bucket["attempted"] += 1
        system_bucket["correct"] += int(is_correct)
        system_bucket["avg_latency_ms"] += latency

        category_bucket = system_bucket["categories"][category]
        category_bucket["attempted"] += 1
        category_bucket["correct"] += int(is_correct)

    for system_id, metrics in by_system.items():
        attempted = metrics["attempted"]
        metrics["accuracy"] = (metrics["correct"] / attempted) if attempted else 0.0
        metrics["avg_latency_ms"] = (metrics["avg_latency_ms"] / attempted) if attempted else 0.0

        metrics["errors"] = int(summary.get("provider_metrics", {}).get(system_id, {}).get("errors", 0))

        for cat_name, cat in metrics["categories"].items():
            cat_attempted = cat["attempted"]
            cat["accuracy"] = (cat["correct"] / cat_attempted) if cat_attempted else 0.0
            metrics["categories"][cat_name] = dict(cat)

        metrics["categories"] = dict(metrics["categories"])

    return {
        "providers": dict(by_system),
        "total_rows": len(results),
        "status": summary.get("status", "unknown"),
    }
