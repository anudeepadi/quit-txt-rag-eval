"""Data loading utilities for QA datasets."""

import json
from pathlib import Path

# Default data directory
DATA_DIR = Path(__file__).parent.parent / "data"


def load_qa_jsonl(file_path: Path) -> list[dict]:
    """Load QA pairs from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of dictionaries with 'question' and 'answer' keys
    """
    pairs = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def load_human_curated(data_dir: Path | None = None) -> list[dict]:
    """Load the human-curated QA dataset.

    Args:
        data_dir: Optional custom data directory

    Returns:
        List of QA pairs from qa.jsonl
    """
    data_dir = data_dir or DATA_DIR
    # Check data/ first, then fall back to project root
    qa_path = data_dir / "qa.jsonl"
    if not qa_path.exists():
        qa_path = data_dir.parent / "qa.jsonl"
    return load_qa_jsonl(qa_path)


def load_ai_generated(data_dir: Path | None = None) -> list[dict]:
    """Load the AI-generated QA dataset.

    Tries ai_generated_qa.jsonl first, then falls back to
    ai_generated_qa_full.json (which wraps pairs under a 'qa_pairs' key).

    Args:
        data_dir: Optional custom data directory

    Returns:
        List of QA pairs with 'question' and 'answer' keys
    """
    data_dir = data_dir or DATA_DIR
    jsonl_path = data_dir / "ai_generated" / "ai_generated_qa.jsonl"
    if jsonl_path.exists():
        return load_qa_jsonl(jsonl_path)
    json_path = data_dir / "ai_generated" / "ai_generated_qa_full.json"
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["qa_pairs"]


def load_web_scraped(data_dir: Path | None = None) -> list[dict]:
    """Load the web-scraped Q&A dataset.

    Args:
        data_dir: Optional custom data directory

    Returns:
        List of QA pairs from web_scraped_qa.jsonl
    """
    data_dir = data_dir or DATA_DIR
    path = data_dir / "web_scraped_qa.jsonl"
    return load_qa_jsonl(path)


def load_evaluation_results(file_path: Path) -> dict:
    """Load evaluation results from a JSON file.

    Args:
        file_path: Path to the evaluation results JSON

    Returns:
        Dictionary with evaluation results
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def save_evaluation_results(results: dict, file_path: Path) -> None:
    """Save evaluation results to a JSON file.

    Args:
        results: Dictionary with evaluation results
        file_path: Path to save the results
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
