from llm_eval.benchmarks.mmlu_subset import MMLUSubsetDataset


def test_dataset_loads_rows() -> None:
    dataset = MMLUSubsetDataset("data/benchmarks/mmlu_subset/dev.jsonl")
    rows = list(dataset.load())
    assert len(rows) == 5
    assert rows[0].sample_id == "mmlu-001"


def test_dataset_respects_max_samples() -> None:
    dataset = MMLUSubsetDataset("data/benchmarks/mmlu_subset/dev.jsonl", max_samples=2)
    rows = list(dataset.load())
    assert len(rows) == 2


def test_prompt_format_includes_choice_labels() -> None:
    dataset = MMLUSubsetDataset("data/benchmarks/mmlu_subset/dev.jsonl", max_samples=1)
    sample = list(dataset.load())[0]
    prompt = sample.prompt()
    assert "A." in prompt
    assert "B." in prompt
