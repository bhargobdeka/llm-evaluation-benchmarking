from __future__ import annotations

from pathlib import Path

import gradio as gr

from llm_eval.ui.jobs import execute_eval_job


CONFIG_MAP = {
    "Anthropic + Gemini baseline": "configs/run.example.yaml",
    "Groq open-source pack (Qwen + Kimi-K2 + others)": "configs/run.groq.yaml",
}


def _run_from_ui(
    preset_name: str,
    max_samples: int,
    anthropic_key: str,
    gemini_key: str,
    groq_key: str,
) -> tuple[str, str, str]:
    config_path = CONFIG_MAP[preset_name]
    env_overrides: dict[str, str] = {}
    if anthropic_key.strip():
        env_overrides["ANTHROPIC_API_KEY"] = anthropic_key.strip()
    if gemini_key.strip():
        env_overrides["GEMINI_API_KEY"] = gemini_key.strip()
    if groq_key.strip():
        env_overrides["GROQ_API_KEY"] = groq_key.strip()

    result = execute_eval_job(
        config_path=config_path,
        policy_path="configs/policy.yaml",
        max_samples=max_samples,
        run_name_prefix="space",
        env_overrides=env_overrides,
        artifacts_root="artifacts",
        reports_root="reports",
    )
    report_path = Path(result["markdown_report"])
    report_text = report_path.read_text(encoding="utf-8")
    return (
        f"Run complete: `{result['run_id']}`",
        report_text,
        f"{result['markdown_report']}\n{result['html_report']}\n{result['json_report']}",
    )


def build_app() -> gr.Blocks:
    with gr.Blocks(title="LLM Multi-Model Evaluation Framework") as app:
        gr.Markdown(
            """
# LLM Multi-Model Evaluation Framework

Run benchmark evaluations with your own API keys (BYOK).  
Keys are used in-memory for the current run and are not persisted by the app.
"""
        )
        with gr.Row():
            preset = gr.Dropdown(
                choices=list(CONFIG_MAP.keys()),
                value="Groq open-source pack (Qwen + Kimi-K2 + others)",
                label="Evaluation preset",
            )
            max_samples = gr.Slider(
                minimum=1,
                maximum=25,
                value=5,
                step=1,
                label="Max samples",
            )
        with gr.Accordion("Provider keys (BYOK)", open=True):
            anthropic_key = gr.Textbox(label="ANTHROPIC_API_KEY", type="password")
            gemini_key = gr.Textbox(label="GEMINI_API_KEY", type="password")
            groq_key = gr.Textbox(label="GROQ_API_KEY", type="password")

        run_btn = gr.Button("Run evaluation", variant="primary")
        status = gr.Markdown("Ready.")
        report_md = gr.Markdown()
        report_paths = gr.Textbox(label="Generated files", interactive=False)

        run_btn.click(
            fn=_run_from_ui,
            inputs=[preset, max_samples, anthropic_key, gemini_key, groq_key],
            outputs=[status, report_md, report_paths],
        )

    return app
