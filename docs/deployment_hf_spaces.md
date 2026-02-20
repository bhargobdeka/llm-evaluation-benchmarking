# Hugging Face Spaces Deployment

This project includes a Gradio app (`app.py`) designed for public Hugging Face Space deployment with BYOK behavior.

## Deployment Target

- Space type: Gradio
- Visibility: public
- Owner: `bhargob11`
- Recommended hardware: `cpu-basic` for MVP

## BYOK Security Model

- Users provide API keys in the app UI for the current session.
- Keys are injected in-memory as runtime env overrides.
- Keys are not written to `.env`, artifacts, or report files.

## Local Validation

```bash
make install
.venv/bin/python app.py
```

## Publish Command

```bash
.venv/bin/python scripts/publish_hf_space.py --owner bhargob11 --space-name llm-eval-framework
```

## Notes

- `requirements.txt` is used by Spaces build.
- Upload flow excludes local/private paths like `.env`, `artifacts/`, and `reports/`.
