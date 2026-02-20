from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SessionConfig:
    config_path: str
    max_samples: int
    run_name: str
