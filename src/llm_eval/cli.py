from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from llm_eval.connectivity import (
    check_connectivity,
    diagnose_openai_endpoints,
    get_key_debug_info,
)
from llm_eval.config import build_run_manifest, load_run_config, resolve_provider_keys
from llm_eval.reporting import write_reports
from llm_eval.runner import run_evaluation
from llm_eval.scoring import load_results, load_summary, score_results
from llm_eval.stats import add_confidence_intervals, pairwise_significance

app = typer.Typer(help="LLM multi-model evaluation framework CLI.")
console = Console()


@app.command("validate-config")
def validate_config(
    config_path: str = typer.Option(
        "configs/run.example.yaml", "--config", "-c", help="Path to run config YAML."
    ),
) -> None:
    """Validate a run configuration and print a manifest preview."""
    config = load_run_config(config_path)
    manifest = build_run_manifest(config)
    console.print("[green]Config is valid.[/green]")
    console.print_json(data=manifest.model_dump())


@app.command("check-keys")
def check_keys(
    config_path: str = typer.Option(
        "configs/run.example.yaml", "--config", "-c", help="Path to run config YAML."
    ),
    env_path: str = typer.Option(".env", "--env", help="Path to .env file."),
) -> None:
    """Check whether required provider keys are present in env."""
    config = load_run_config(config_path)
    key_status = resolve_provider_keys(config=config, env_path=env_path)
    table = Table(title="Provider Key Availability")
    table.add_column("Provider")
    table.add_column("Key Available")
    for provider_name, is_available in key_status.items():
        table.add_row(provider_name, "yes" if is_available else "no")
    console.print(table)


@app.command("scaffold-config")
def scaffold_config(
    output_path: str = typer.Option(
        "configs/run.example.yaml", "--out", "-o", help="Output path for scaffold config."
    )
) -> None:
    """Write a starter run config for Anthropic and Gemini."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise typer.BadParameter(f"{output_path} already exists.")
    template = {
        "run_name": "phase1-baseline",
        "seed": 42,
        "benchmark": {
            "name": "mmlu_subset",
            "split": "dev",
            "dataset_path": "data/benchmarks/mmlu_subset/dev.jsonl",
            "max_samples": 50,
        },
        "providers": [
            {
                "provider": "anthropic",
                "model": "claude-3-5-haiku-latest",
                "api_key_env": "ANTHROPIC_API_KEY",
                "temperature": 0.0,
                "max_tokens": 512,
            },
            {
                "provider": "gemini",
                "model": "gemini-2.0-flash",
                "api_key_env": "GEMINI_API_KEY",
                "temperature": 0.0,
                "max_tokens": 512,
            },
        ],
    }
    import yaml

    target.write_text(yaml.safe_dump(template, sort_keys=False), encoding="utf-8")
    console.print(f"[green]Created[/green] {output_path}")


@app.command("print-policy")
def print_policy(policy_path: str = typer.Option("configs/policy.yaml", "--policy")) -> None:
    """Print policy YAML as JSON for easy inspection."""
    import yaml

    data = yaml.safe_load(Path(policy_path).read_text(encoding="utf-8")) or {}
    console.print_json(data=json.loads(json.dumps(data)))


@app.command("run")
def run(
    config_path: str = typer.Option(
        "configs/run.example.yaml", "--config", "-c", help="Path to run config YAML."
    ),
    policy_path: str = typer.Option(
        "configs/policy.yaml", "--policy", help="Path to policy YAML."
    ),
    artifacts_root: str = typer.Option(
        "artifacts", "--artifacts-root", help="Directory for run artifacts."
    ),
    env_path: str = typer.Option(".env", "--env", help="Path to environment file."),
) -> None:
    """Execute a benchmark run and persist artifacts."""
    config = load_run_config(config_path)
    summary = run_evaluation(
        config=config,
        policy_path=policy_path,
        artifacts_root=artifacts_root,
        env_path=env_path,
    )
    table = Table(title=f"Run Summary ({summary.run_id})")
    table.add_column("System")
    table.add_column("Attempted")
    table.add_column("Correct")
    table.add_column("Errors")
    table.add_column("Accuracy")
    for system_id, metrics in summary.provider_metrics.items():
        table.add_row(
            system_id,
            str(metrics.get("attempted", 0)),
            str(metrics.get("correct", 0)),
            str(metrics.get("errors", 0)),
            f"{metrics.get('accuracy', 0.0):.3f}",
        )
    console.print(table)
    console.print(f"Artifacts written under [bold]{artifacts_root}/runs/{summary.run_id}[/bold]")


@app.command("check-connectivity")
def check_connectivity_command(
    config_path: str = typer.Option(
        "configs/run.example.yaml", "--config", "-c", help="Path to run config YAML."
    ),
    env_path: str = typer.Option(".env", "--env", help="Path to environment file."),
) -> None:
    """Execute lightweight provider calls to validate live connectivity."""
    config = load_run_config(config_path)
    results = check_connectivity(config=config, env_path=env_path)
    table = Table(title="Provider Connectivity")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Status")
    table.add_column("Detail")
    for result in results:
        table.add_row(
            result.provider,
            result.model,
            "PASS" if result.ok else "FAIL",
            result.detail,
        )
    console.print(table)


@app.command("debug-key")
def debug_key(
    env_var: str = typer.Option(
        "OPENAI_API_KEY", "--env-var", help="Environment variable name to inspect."
    ),
    env_path: str = typer.Option(".env", "--env", help="Path to environment file."),
) -> None:
    """Print masked key metadata (never prints full key)."""
    info = get_key_debug_info(env_var=env_var, env_path=env_path)
    table = Table(title=f"Key Debug ({info.env_var})")
    table.add_column("Field")
    table.add_column("Value")
    masked = (
        f"{info.starts_with}...{info.ends_with}"
        if info.present and info.length > 11
        else ("(short)" if info.present else "(missing)")
    )
    table.add_row("present", "yes" if info.present else "no")
    table.add_row("length", str(info.length))
    table.add_row("fingerprint", masked)
    table.add_row("has_whitespace", "yes" if info.has_whitespace else "no")
    console.print(table)


@app.command("diagnose-openai")
def diagnose_openai(
    env_var: str = typer.Option(
        "OPENAI_API_KEY", "--env-var", help="Environment variable containing OpenAI key."
    ),
    model: str = typer.Option("gpt-4o-mini", "--model", help="Model for completion check."),
    env_path: str = typer.Option(".env", "--env", help="Path to environment file."),
    project_id_env_var: str = typer.Option(
        "OPENAI_PROJECT_ID",
        "--project-id-env-var",
        help="Env var name containing OpenAI project id.",
    ),
    organization_id_env_var: str = typer.Option(
        "OPENAI_ORG_ID",
        "--organization-id-env-var",
        help="Env var name containing OpenAI organization id.",
    ),
) -> None:
    """Diagnose OpenAI key behavior on models vs chat completions endpoints."""
    diagnostics = diagnose_openai_endpoints(
        env_var=env_var,
        model=model,
        env_path=env_path,
        project_id_env_var=project_id_env_var,
        organization_id_env_var=organization_id_env_var,
    )
    table = Table(title="OpenAI Endpoint Diagnostics")
    table.add_column("Endpoint")
    table.add_column("Status")
    table.add_column("HTTP")
    table.add_column("Detail")
    for item in diagnostics:
        table.add_row(
            item.endpoint,
            "PASS" if item.ok else "FAIL",
            str(item.status_code) if item.status_code is not None else "-",
            item.detail,
        )
    console.print(table)


@app.command("report")
def report(
    run_id: str = typer.Option(..., "--run-id", help="Run id from artifacts/runs/<run_id>."),
    artifacts_root: str = typer.Option("artifacts", "--artifacts-root"),
    reports_root: str = typer.Option("reports", "--reports-root"),
) -> None:
    """Generate markdown/html/json reports from run artifacts."""
    run_dir = Path(artifacts_root) / "runs" / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"Run directory does not exist: {run_dir}")
    results = load_results(run_dir)
    summary = load_summary(run_dir)
    scored = score_results(results, summary)
    scored = add_confidence_intervals(scored)
    pairwise = pairwise_significance(results)
    outputs = write_reports(
        run_id=run_id,
        scored=scored,
        pairwise=pairwise,
        reports_root=reports_root,
    )
    table = Table(title=f"Report Outputs ({run_id})")
    table.add_column("Format")
    table.add_column("Path")
    for fmt, path in outputs.items():
        table.add_row(fmt, path)
    console.print(table)
