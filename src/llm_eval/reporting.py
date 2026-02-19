from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _provider_table_rows(scored: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return sorted(
        scored.get("providers", {}).items(),
        key=lambda item: item[1].get("accuracy", 0.0),
        reverse=True,
    )


def build_markdown_report(run_id: str, scored: dict[str, Any], pairwise: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append(f"# Evaluation Report: {run_id}")
    lines.append("")
    lines.append(f"- Status: `{scored.get('status', 'unknown')}`")
    lines.append(f"- Total evaluated rows: `{scored.get('total_rows', 0)}`")
    lines.append("")
    lines.append("## Leaderboard")
    lines.append("")
    lines.append("| System | Attempted | Correct | Accuracy | CI95 | Avg Latency (ms) | Errors |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for provider, metrics in _provider_table_rows(scored):
        ci = metrics.get("accuracy_ci95", {"low": 0.0, "high": 0.0})
        lines.append(
            "| "
            f"{provider} | {metrics.get('attempted', 0)} | {metrics.get('correct', 0)} | "
            f"{metrics.get('accuracy', 0.0):.3f} | "
            f"[{ci.get('low', 0.0):.3f}, {ci.get('high', 0.0):.3f}] | "
            f"{metrics.get('avg_latency_ms', 0.0):.1f} | {metrics.get('errors', 0)} |"
        )

    lines.append("")
    lines.append("## Pairwise Significance (Matched Samples)")
    lines.append("")
    if not pairwise:
        lines.append("No provider pairs available.")
    else:
        lines.append("| System A | System B | Wins A | Wins B | Ties | p-value |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for row in pairwise:
            lines.append(
                f"| {row['provider_a']} | {row['provider_b']} | {row['wins_a']} | "
                f"{row['wins_b']} | {row['ties']} | {row['p_value_two_sided']:.4f} |"
            )

    lines.append("")
    lines.append("## Category Breakdown")
    lines.append("")
    for provider, metrics in _provider_table_rows(scored):
        lines.append(f"### {provider}")
        lines.append("")
        lines.append("| Category | Attempted | Correct | Accuracy |")
        lines.append("|---|---:|---:|---:|")
        categories = sorted(metrics.get("categories", {}).items(), key=lambda x: x[0])
        for cat_name, cat in categories:
            lines.append(
                f"| {cat_name} | {cat.get('attempted', 0)} | {cat.get('correct', 0)} | "
                f"{cat.get('accuracy', 0.0):.3f} |"
            )
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_html_report(run_id: str, scored: dict[str, Any], pairwise: list[dict[str, Any]]) -> str:
    rows = _provider_table_rows(scored)
    provider_rows = []
    for provider, metrics in rows:
        ci = metrics.get("accuracy_ci95", {"low": 0.0, "high": 0.0})
        provider_rows.append(
            "<tr>"
            f"<td>{provider}</td><td>{metrics.get('attempted', 0)}</td>"
            f"<td>{metrics.get('correct', 0)}</td><td>{metrics.get('accuracy', 0.0):.3f}</td>"
            f"<td>[{ci.get('low', 0.0):.3f}, {ci.get('high', 0.0):.3f}]</td>"
            f"<td>{metrics.get('avg_latency_ms', 0.0):.1f}</td>"
            f"<td>{metrics.get('errors', 0)}</td></tr>"
        )
    pair_rows = []
    for row in pairwise:
        pair_rows.append(
            "<tr>"
            f"<td>{row['provider_a']}</td><td>{row['provider_b']}</td>"
            f"<td>{row['wins_a']}</td><td>{row['wins_b']}</td><td>{row['ties']}</td>"
            f"<td>{row['p_value_two_sided']:.4f}</td></tr>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>Evaluation Report {run_id}</title>"
        "<style>body{font-family:Arial,sans-serif;margin:24px}table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f4f4f4}</style>"
        "</head><body>"
        f"<h1>Evaluation Report: {run_id}</h1>"
        f"<p>Status: <code>{scored.get('status', 'unknown')}</code><br>"
        f"Total evaluated rows: <code>{scored.get('total_rows', 0)}</code></p>"
        "<h2>Leaderboard</h2><table><thead><tr>"
        "<th>System</th><th>Attempted</th><th>Correct</th><th>Accuracy</th>"
        "<th>CI95</th><th>Avg Latency (ms)</th><th>Errors</th>"
        "</tr></thead><tbody>"
        + "".join(provider_rows)
        + "</tbody></table>"
        "<h2>Pairwise Significance</h2><table><thead><tr>"
        "<th>System A</th><th>System B</th><th>Wins A</th><th>Wins B</th><th>Ties</th><th>p-value</th>"
        "</tr></thead><tbody>"
        + ("".join(pair_rows) if pair_rows else "<tr><td colspan='6'>No pairs available</td></tr>")
        + "</tbody></table>"
        "</body></html>"
    )


def write_reports(
    *,
    run_id: str,
    scored: dict[str, Any],
    pairwise: list[dict[str, Any]],
    reports_root: str | Path = "reports",
) -> dict[str, str]:
    root = Path(reports_root)
    root.mkdir(parents=True, exist_ok=True)
    md_path = root / f"{run_id}.md"
    html_path = root / f"{run_id}.html"
    json_path = root / f"{run_id}.json"

    md_path.write_text(build_markdown_report(run_id, scored, pairwise), encoding="utf-8")
    html_path.write_text(build_html_report(run_id, scored, pairwise), encoding="utf-8")
    json_path.write_text(
        json.dumps({"run_id": run_id, "scored": scored, "pairwise": pairwise}, indent=2),
        encoding="utf-8",
    )
    return {"markdown": str(md_path), "html": str(html_path), "json": str(json_path)}
