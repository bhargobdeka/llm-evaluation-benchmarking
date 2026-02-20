from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from llm_eval.config import build_run_manifest, load_run_config
from llm_eval.reporting import write_reports
from llm_eval.runner import run_evaluation
from llm_eval.scoring import load_results, load_summary, score_results
from llm_eval.stats import add_confidence_intervals, pairwise_significance


def execute_eval_job(
    *,
    config_path: str,
    policy_path: str,
    max_samples: int,
    run_name_prefix: str,
    env_overrides: dict[str, str],
    artifacts_root: str = "artifacts",
    reports_root: str = "reports",
) -> dict[str, str]:
    config = load_run_config(config_path)
    config.benchmark.max_samples = max_samples
    config.run_name = f"{run_name_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    summary = run_evaluation(
        config=config,
        policy_path=policy_path,
        artifacts_root=artifacts_root,
        env_path=".env",
        env_overrides=env_overrides,
    )

    run_dir = Path(artifacts_root) / "runs" / summary.run_id
    scored = add_confidence_intervals(score_results(load_results(run_dir), load_summary(run_dir)))
    pairwise = pairwise_significance(load_results(run_dir))
    outputs = write_reports(
        run_id=summary.run_id,
        scored=scored,
        pairwise=pairwise,
        reports_root=reports_root,
    )
    manifest = build_run_manifest(config)
    return {
        "run_id": summary.run_id,
        "run_name": config.run_name,
        "manifest_id": manifest.run_id,
        "markdown_report": outputs["markdown"],
        "html_report": outputs["html"],
        "json_report": outputs["json"],
        "status": "completed",
    }
