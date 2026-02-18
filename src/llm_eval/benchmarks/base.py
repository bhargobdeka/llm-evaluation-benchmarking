from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class BenchmarkSample:
    sample_id: str
    question: str
    choices: list[str]
    answer_index: int
    category: str

    def prompt(self) -> str:
        option_lines = [f"{chr(65 + i)}. {choice}" for i, choice in enumerate(self.choices)]
        return "\n".join(
            [
                f"Category: {self.category}",
                "Answer the following multiple-choice question.",
                self.question,
                *option_lines,
                "Reply with only the option letter (A, B, C, D, ...).",
            ]
        )


class BenchmarkDataset(ABC):
    name: str

    @abstractmethod
    def load(self) -> Iterable[BenchmarkSample]:
        raise NotImplementedError
