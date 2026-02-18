from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactStore:
    """Persistent run artifacts for replay, auditing, and reporting."""

    def __init__(self, artifacts_root: str | Path, run_id: str):
        self.run_dir = Path(artifacts_root) / "runs" / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.run_dir / "manifest.json"
        self.results_path = self.run_dir / "results.jsonl"
        self.errors_path = self.run_dir / "errors.jsonl"
        self.summary_path = self.run_dir / "summary.json"

    def write_manifest(self, manifest: dict[str, Any]) -> None:
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def append_result(self, record: dict[str, Any]) -> None:
        with self.results_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=True) + "\n")

    def append_error(self, record: dict[str, Any]) -> None:
        with self.errors_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=True) + "\n")

    def write_summary(self, summary: dict[str, Any]) -> None:
        self.summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def load_completed_keys(self) -> set[str]:
        keys: set[str] = set()
        if not self.results_path.exists():
            return keys
        with self.results_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                key = row.get("request_key")
                if key:
                    keys.add(str(key))
        return keys
