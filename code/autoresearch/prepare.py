"""QuitTxt Autoresearch — Data preparation and evaluation utilities.

Fixed infrastructure. NOT modified by the agent.
One-time validation + runtime utilities for the experiment loop.
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

_ENV_PATH = _ROOT / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set. Add it to .env or export it.")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEST_SET_PATH = _ROOT / "data" / "test_set" / "150_qa_testset.xlsx"
RESULTS_FILE = Path(__file__).parent / "results.tsv"
N_EVAL = 20  # questions per experiment (fixed for fair comparison)
MODEL_NAME = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# Imports (heavy)
# ---------------------------------------------------------------------------
import chromadb
from chromadb.config import Settings
from openai import OpenAI

from shared.data_loader import load_ai_generated, load_human_curated, load_web_scraped
from shared.ragas_utils import load_test_set

# ---------------------------------------------------------------------------
# Dataset map
# ---------------------------------------------------------------------------
DATASET_MAP = {
    "ai_rag": ("ai_generated", load_ai_generated),
    "human_rag": ("human_curated", load_human_curated),
    "web_rag": ("web_scraped", load_web_scraped),
}


def load_dataset_for_config(config: str) -> list[dict]:
    """Load the QA dataset for a given config name."""
    if config not in DATASET_MAP:
        raise ValueError(f"Unknown config: {config}. Use: {list(DATASET_MAP.keys())}")
    _, loader_fn = DATASET_MAP[config]
    return loader_fn()


def build_collection(
    chroma_client: chromadb.Client,
    config: str,
    qa_pairs: list[dict],
) -> chromadb.Collection:
    """Build ephemeral ChromaDB collection from QA pairs."""
    coll_name, _ = DATASET_MAP[config]
    try:
        chroma_client.delete_collection(coll_name)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=coll_name,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 100
    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i : i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [str(p.get("id", f"{coll_name}_{i + j}")) for j, p in enumerate(batch)]
        collection.add(documents=documents, ids=ids)

    return collection


def get_test_questions(max_rows: int = N_EVAL) -> list[dict]:
    """Load deterministic set of test questions."""
    return load_test_set(TEST_SET_PATH, max_rows=max_rows)


# ---------------------------------------------------------------------------
# Fast faithfulness proxy — LLM-as-judge
# ---------------------------------------------------------------------------
_JUDGE_PROMPT = """Rate how well the Response is grounded in the Context.

Scale:
0 = Response is entirely fabricated, nothing from Context
3 = Mostly fabricated with a few grounded facts
5 = Mix of grounded and fabricated information
7 = Mostly grounded with minor unsupported additions
10 = Every claim in Response is directly supported by Context

Context:
{context}

Question: {question}

Response: {response}

Score (just the number, nothing else):"""


def score_faithfulness_proxy(
    oai_client: OpenAI,
    question: str,
    response: str,
    contexts: list[str],
) -> float:
    """Fast faithfulness proxy using LLM-as-judge. Returns 0.0–1.0."""
    context_text = "\n\n".join(contexts) if contexts else "(no context)"
    try:
        result = oai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": _JUDGE_PROMPT.format(
                    context=context_text, question=question, response=response,
                )},
            ],
            temperature=0.0,
            max_tokens=5,
        )
        raw = result.choices[0].message.content.strip()
        score = float("".join(c for c in raw if c.isdigit() or c == "."))
        return min(max(score / 10.0, 0.0), 1.0)
    except Exception:
        return 0.5  # safe fallback


def compute_word_stats(responses: list[str]) -> dict:
    """Compute word count statistics across responses."""
    counts = [len(r.split()) for r in responses]
    if not counts:
        return {"avg": 0, "min": 0, "max": 0}
    return {
        "avg": round(sum(counts) / len(counts), 1),
        "min": min(counts),
        "max": max(counts),
    }


# ---------------------------------------------------------------------------
# Results log
# ---------------------------------------------------------------------------
_TSV_HEADER = (
    "experiment_id\ttimestamp\thypothesis\ttarget_config\t"
    "faithfulness_proxy\tavg_words\tmin_words\tmax_words\t"
    "temperature\tmax_tokens\ttop_k\tverdict\n"
)


def get_best_score() -> float:
    """Read the best faithfulness_proxy score from results.tsv."""
    if not RESULTS_FILE.exists():
        return 0.0
    best = 0.0
    with open(RESULTS_FILE) as f:
        for line in f:
            if line.startswith("experiment_id") or line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 5:
                try:
                    score = float(parts[4])
                    if score > best:
                        best = score
                except ValueError:
                    pass
    return best


def get_experiment_count() -> int:
    """Count existing experiments in results.tsv."""
    if not RESULTS_FILE.exists():
        return 0
    count = 0
    with open(RESULTS_FILE) as f:
        for line in f:
            if not line.startswith("experiment_id") and not line.startswith("#") and line.strip():
                count += 1
    return count


def log_result(
    experiment_id: int,
    hypothesis: str,
    target_config: str,
    score: float,
    word_stats: dict,
    temperature: float,
    max_tokens: int,
    top_k: int,
    verdict: str,
) -> None:
    """Append one result row to results.tsv."""
    from datetime import datetime

    if not RESULTS_FILE.exists():
        with open(RESULTS_FILE, "w") as f:
            f.write(_TSV_HEADER)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = (
        f"{experiment_id}\t{timestamp}\t{hypothesis}\t{target_config}\t"
        f"{score:.4f}\t{word_stats['avg']}\t{word_stats['min']}\t{word_stats['max']}\t"
        f"{temperature}\t{max_tokens}\t{top_k}\t{verdict}\n"
    )
    with open(RESULTS_FILE, "a") as f:
        f.write(row)


# ---------------------------------------------------------------------------
# One-time validation (run this file directly)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("QuitTxt Autoresearch — Environment Validation")
    print("=" * 60)

    print(f"\nOpenAI API key: {'set' if OPENAI_API_KEY else 'MISSING'}")
    print(f"Test set path: {TEST_SET_PATH} ({'exists' if TEST_SET_PATH.exists() else 'MISSING'})")
    print(f"Results file: {RESULTS_FILE}")

    print("\nLoading datasets...")
    for config, (name, loader) in DATASET_MAP.items():
        try:
            data = loader()
            print(f"  {config} ({name}): {len(data):,} pairs")
        except Exception as e:
            print(f"  {config} ({name}): ERROR — {e}")

    print("\nLoading test set...")
    rows = get_test_questions()
    print(f"  Loaded {len(rows)} questions (using first {N_EVAL})")

    print("\nQuick API test...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        r = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Say 'ok' and nothing else."}],
            max_tokens=5,
        )
        print(f"  API response: {r.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"  API ERROR: {e}")

    print("\n✓ Validation complete. Ready for autoresearch.")
