# Governance and Automation Policy

This document defines how the project runs with minimal supervision while preserving methodological rigor and security.

## Operating Principle

Default to autonomous execution. Human input is required only at predefined critical decision gates.

## Decision Gates (Human Approval Required)

1. Benchmark family or scoring policy changes.
2. Budget threshold increases or stop-rule changes.
3. New provider onboarding requiring credentials/billing setup.
4. Public release decisions (repository milestones or Hugging Face Space go-live).

Decision gate definitions live in `configs/decision_gates.yaml`.

## Autonomous Scope (No Approval Needed)

- Routine implementation and refactors within approved scope.
- Unit tests, lint/type fixes, and documentation updates.
- Benchmark runs within approved budget, reliability, and security policy.
- Report generation and non-breaking operational improvements.

## Execution Policy

The canonical machine-readable policy is `configs/policy.yaml`.

Current defaults:
- Maximum budget per run: `$5`.
- Maximum parallel requests: `3`.
- Provider error-rate hard stop: `10%` over rolling window.
- Secrets policy: BYOK only; do not persist user API keys.

## Security and Secrets

- Store provider keys in local `.env` only.
- Never log raw secrets or include them in artifacts.
- Redact secret-like tokens in error traces and logs.
- Hugging Face Space must process keys in memory per session and discard them after run completion.

## Escalation Protocol

When a critical gate is hit:
1. Pause autonomous actions touching that scope.
2. Produce a short decision brief:
   - what changed
   - why it matters
   - proposed option
   - rollback plan
3. Await explicit human approval before proceeding.

## Reproducibility Requirements

- Every run must include deterministic run metadata.
- Store prompt hash, model config, seed, timestamps, and error details.
- Keep artifacts versioned to allow audit and replay.

## Change Control

- Any updates to `configs/policy.yaml` or `configs/decision_gates.yaml` must be treated as governance changes.
- Governance changes require a decision gate approval event.
