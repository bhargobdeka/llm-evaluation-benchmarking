from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from llm_eval.config import build_run_manifest, load_run_config
from llm_eval.reporting import write_reports
from llm_eval.runner import run_evaluation
from llm_eval.scoring import load_results, load_summary, score_results
from llm_eval.stats import add_confidence_intervals, pairwise_significance


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automated nightly evaluation runner with policy constraints."
    )
    parser.add_argument("--config", default="configs/run.groq.yaml")
    parser.add_argument("--policy", default="configs/policy.yaml")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--artifacts-root", default="artifacts")
    parser.add_argument("--reports-root", default="reports")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_run_config(args.config)
    manifest = build_run_manifest(config)
    started_at = datetime.now(timezone.utc).isoformat()

    summary = run_evaluation(
        config=config,
        policy_path=args.policy,
        artifacts_root=args.artifacts_root,
        env_path=args.env,
    )

    run_dir = Path(args.artifacts_root) / "runs" / summary.run_id
    results = load_results(run_dir)
    summary_payload = load_summary(run_dir)
    scored = score_results(results, summary_payload)
    scored = add_confidence_intervals(scored)
    pairwise = pairwise_significance(results)
    outputs = write_reports(
        run_id=summary.run_id,
        scored=scored,
        pairwise=pairwise,
        reports_root=args.reports_root,
    )

    job_meta = {
        "job_type": "nightly_eval",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "run_id": summary.run_id,
        "run_name": config.run_name,
        "status": summary_payload.get("status", "unknown"),
        "total_requests": summary.total_requests,
        "total_errors": summary.total_errors,
        "reports": outputs,
        "manifest_preview": {
            "run_id": manifest.run_id,
            "providers": manifest.providers,
            "benchmark": manifest.benchmark,
        },
    }
    out_path = Path(args.reports_root) / f"{summary.run_id}.nightly.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(job_meta, indent=2), encoding="utf-8")

    print(json.dumps(job_meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
