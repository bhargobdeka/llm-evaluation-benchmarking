from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import HfApi, upload_folder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish current repository to a Hugging Face Space.")
    parser.add_argument("--owner", default="bhargob11")
    parser.add_argument("--space-name", default="llm-eval-framework")
    parser.add_argument("--private", action="store_true")
    parser.add_argument("--sdk", default="gradio")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_id = f"{args.owner}/{args.space_name}"
    api = HfApi()
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        private=args.private,
        exist_ok=True,
        space_sdk=args.sdk,
    )
    required_paths = [
        "app.py",
        "README.md",
        "requirements.txt",
        "LICENSE",
        "pyproject.toml",
        "configs",
        "data",
        "docs",
        "scripts",
        "src",
    ]
    for item in required_paths:
        if not Path(item).exists():
            raise FileNotFoundError(f"Required path missing for Space publish: {item}")

    upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=".",
        allow_patterns=[
            "app.py",
            "README.md",
            "requirements.txt",
            "LICENSE",
            "pyproject.toml",
            "configs/**",
            "data/**",
            "docs/**",
            "scripts/**",
            "src/**",
        ],
        ignore_patterns=[
            ".git/*",
            ".venv/*",
            "artifacts/*",
            "reports/*",
            ".hfignore",
            "__pycache__/*",
            ".pytest_cache/*",
            ".env",
            ".cursor/*",
            "*.pyc",
        ],
    )
    print(f"Published to https://huggingface.co/spaces/{repo_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
