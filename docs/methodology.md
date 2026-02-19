# Evaluation Methodology and Reproducibility

This document describes the current evaluation protocol and how to reproduce benchmark runs.

## Scope

- Task type: single-turn text benchmark evaluation.
- Current benchmark: curated `mmlu_subset`.
- Current active providers: Anthropic, Gemini, Groq (OpenAI adapter remains optional).

## Reproducibility Controls

- Deterministic run identity:
  - `run_id` is derived from run config (run name, seed, benchmark config, providers).
- Artifact persistence:
  - `manifest.json` with policy snapshot and run metadata.
  - `results.jsonl` with per-sample outputs.
  - `errors.jsonl` with per-sample errors.
  - `summary.json` with aggregate execution outcome.
- Request cache:
  - deterministic request hash keyed on provider/model/prompt/sample/parameters.
  - supports resumability and duplicate-billing avoidance.

## Metrics

Per system (`provider:model`):
- Attempted count
- Correct count
- Accuracy
- Average latency
- Error count
- Category-level breakdown
- 95% confidence interval (Wilson interval)

Pairwise significance:
- Matched-sample win/tie comparison.
- Two-sided binomial-based p-value over non-tied outcomes.

## Policy Enforcement

Policy source: `configs/policy.yaml`

Key constraints:
- budget cap (`max_usd_per_run`)
- max parallel requests
- timeout and retries
- provider error-rate stop threshold
- BYOK/no secret persistence guarantees

## Standard Run Commands

Install and validate:

```bash
make venv
make install
make check
```

Run baseline evaluation:

```bash
make run-example
make report
```

Run open-source Groq benchmark:

```bash
make run-groq
make report
```

Automated nightly-style run:

```bash
make nightly
```

## Known Limitations

- Current benchmark corpus is intentionally small and curated for framework validation.
- OpenAI may be disabled in default configs when key access is unavailable.
- Cost tracking currently relies on policy + usage metadata capture; strict token-cost accounting can be expanded in a later phase.
