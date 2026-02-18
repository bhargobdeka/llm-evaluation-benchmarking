from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ResponseCache:
    """Simple filesystem cache keyed by deterministic request hash."""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, cache_key: str) -> Path:
        return self.root_dir / f"{cache_key}.json"

    def has(self, cache_key: str) -> bool:
        return self._path_for_key(cache_key).exists()

    def get(self, cache_key: str) -> dict[str, Any] | None:
        path = self._path_for_key(cache_key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def set(self, cache_key: str, payload: dict[str, Any]) -> None:
        path = self._path_for_key(cache_key)
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
