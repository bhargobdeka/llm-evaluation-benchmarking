# LLM Multi-Model Evaluation Framework

Automation-first framework for evaluating multiple LLM APIs with reproducibility, statistical rigor, and minimal supervision.

## Phase 0 Status

Phase 0 is initialized with governance and automation controls:

- Policy config: `configs/policy.yaml`
- Decision gates: `configs/decision_gates.yaml`
- Governance doc: `docs/governance.md`
- Environment template: `.env.example`

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

## Next Phase

Phase 1 will create:
- package skeleton and CLI
- typed configuration and run manifest models
- benchmark/provider interfaces
- first curated MMLU-style benchmark subset loader

## One-Time Setup Required from User

Populate local `.env` from `.env.example` with:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
