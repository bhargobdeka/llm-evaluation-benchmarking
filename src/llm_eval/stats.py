from __future__ import annotations

from collections import defaultdict
from math import comb, sqrt
from typing import Any


def wilson_confidence_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + (z**2 / total)
    center = (p + z * z / (2 * total)) / denom
    margin = (z / denom) * sqrt((p * (1 - p) / total) + (z * z / (4 * total * total)))
    lo = max(0.0, center - margin)
    hi = min(1.0, center + margin)
    return (lo, hi)


def add_confidence_intervals(scored: dict[str, Any]) -> dict[str, Any]:
    for provider, metrics in scored.get("providers", {}).items():
        lo, hi = wilson_confidence_interval(metrics["correct"], metrics["attempted"])
        metrics["accuracy_ci95"] = {"low": lo, "high": hi}
        scored["providers"][provider] = metrics
    return scored


def _binomial_two_sided_p_value(k: int, n: int, p: float = 0.5) -> float:
    if n <= 0:
        return 1.0
    observed_prob = comb(n, k) * (p**k) * ((1 - p) ** (n - k))
    cumulative = 0.0
    for i in range(n + 1):
        prob = comb(n, i) * (p**i) * ((1 - p) ** (n - i))
        if prob <= observed_prob + 1e-15:
            cumulative += prob
    return min(1.0, cumulative)


def pairwise_significance(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_provider_sample: dict[str, dict[str, bool]] = defaultdict(dict)
    for row in results:
        provider = str(row.get("system_id") or f"{row.get('provider')}:{row.get('model')}")
        sample_id = str(row.get("sample_id"))
        by_provider_sample[provider][sample_id] = bool(row.get("is_correct", False))

    providers = sorted(by_provider_sample.keys())
    comparisons: list[dict[str, Any]] = []
    for i in range(len(providers)):
        for j in range(i + 1, len(providers)):
            left = providers[i]
            right = providers[j]
            left_samples = by_provider_sample[left]
            right_samples = by_provider_sample[right]
            shared_ids = sorted(set(left_samples.keys()) & set(right_samples.keys()))
            wins_left = 0
            wins_right = 0
            ties = 0
            for sample_id in shared_ids:
                left_correct = left_samples[sample_id]
                right_correct = right_samples[sample_id]
                if left_correct == right_correct:
                    ties += 1
                elif left_correct and not right_correct:
                    wins_left += 1
                elif right_correct and not left_correct:
                    wins_right += 1
            non_ties = wins_left + wins_right
            p_value = _binomial_two_sided_p_value(max(wins_left, wins_right), non_ties)
            comparisons.append(
                {
                    "provider_a": left,
                    "provider_b": right,
                    "wins_a": wins_left,
                    "wins_b": wins_right,
                    "ties": ties,
                    "non_ties": non_ties,
                    "p_value_two_sided": p_value,
                }
            )
    return comparisons
