# LLM Multi-Model Evaluation Framework

Automation-first framework for evaluating multiple LLM APIs with reproducibility, statistical rigor, and minimal supervision.

## Phase Status

Phase 0 completed with governance and automation controls:

- Policy config: `configs/policy.yaml`
- Decision gates: `configs/decision_gates.yaml`
- Governance doc: `docs/governance.md`
- Environment template: `.env.example`

Phase 1 initialized with core scaffolding:

- Python package + CLI scaffold (`pyproject.toml`, `src/llm_eval/`)
- Typed config and run manifest models (`src/llm_eval/config.py`)
- Benchmark/provider interfaces (`src/llm_eval/benchmarks/base.py`, `src/llm_eval/providers/base.py`)
- Curated MMLU-style subset loader and sample data (`data/benchmarks/mmlu_subset/dev.jsonl`)
- Starter run config (`configs/run.example.yaml`)

## Autonomous Execution Model

- Default mode: autonomous execution.
- Human in the loop only for critical decisions:
  - benchmark/scoring policy changes
  - budget threshold changes
  - new providers requiring credentials
  - public release go/no-go

## Current Approved Defaults

- Max budget per run: `$5`
- Max parallel requests: `3`
- Hard stop if provider error rate exceeds `10%`
- Active providers for early milestones: Anthropic, OpenAI, Google Gemini
- Local provider deferred in initial milestones

## Secrets and BYOK Policy

- Use local `.env` for keys.
- Do not commit real keys.
- Do not persist user keys (required for Hugging Face Space BYOK model).

## CLI Quickstart

Install local package in editable mode:

```bash
python3 -m pip install -e ".[dev]"
```

Validate run config:

```bash
llm-eval validate-config --config configs/run.example.yaml
```

Check key presence for configured providers:

```bash
llm-eval check-keys --config configs/run.example.yaml --env .env
```

Print current policy:

```bash
llm-eval print-policy --policy configs/policy.yaml
```

## Next Phase

Phase 2 is in progress with resilient execution engine components:
- retries/timeouts and provider error-rate stop guard
- deterministic run IDs and resumability
- artifact persistence and request-level caching

Run a benchmark slice and generate artifacts:

```bash
llm-eval run --config configs/run.example.yaml --policy configs/policy.yaml
```

Run live provider connectivity checks:

```bash
llm-eval check-connectivity --config configs/run.example.yaml --env .env
```

## One-Time Setup Required from User

Populate local `.env` from `.env.example` with:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
