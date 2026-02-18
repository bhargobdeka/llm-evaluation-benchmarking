from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from llm_eval.benchmarks.base import BenchmarkDataset, BenchmarkSample


class MMLUSubsetDataset(BenchmarkDataset):
    name = "mmlu_subset"

    def __init__(self, dataset_path: str, max_samples: int | None = None):
        self.dataset_path = Path(dataset_path)
        self.max_samples = max_samples

    def load(self) -> Iterable[BenchmarkSample]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.dataset_path}")

        loaded = 0
        with self.dataset_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                raw = json.loads(line)
                yield BenchmarkSample(
                    sample_id=str(raw["sample_id"]),
                    question=str(raw["question"]),
                    choices=[str(choice) for choice in raw["choices"]],
                    answer_index=int(raw["answer_index"]),
                    category=str(raw.get("category", "general")),
                )
                loaded += 1
                if self.max_samples is not None and loaded >= self.max_samples:
                    return
