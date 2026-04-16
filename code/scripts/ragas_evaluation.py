#!/usr/bin/env python3
"""RAGAS Evaluation: Baseline vs AI-Generated vs Human-Curated vs Web-Scraped RAG.

Evaluates four configurations using RAGAS faithfulness, answer relevancy,
context precision, and context recall metrics against the 127-question LFV
test set (Dr. Louis Willis's 150-question set, 23 flagged by reviewer).

Produces a results table comparable to Ebrahim's n=20 benchmark.

Usage:
    python scripts/ragas_evaluation.py                         # all 127 questions
    python scripts/ragas_evaluation.py --max-questions 100     # paper run (100q)
    python scripts/ragas_evaluation.py --configs baseline ai_rag
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup & .env loading  (same pattern as fair_rag_evaluation.py)
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

# Validate key before heavy imports
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not _OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set. Add it to .env or export it.")

# ---------------------------------------------------------------------------
# Heavy imports
# ---------------------------------------------------------------------------
import chromadb
from chromadb.config import Settings
from openai import OpenAI, AsyncOpenAI
from ragas.dataset_schema import SingleTurnSample
from ragas.llms import llm_factory
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

from shared.data_loader import load_ai_generated, load_human_curated, load_web_scraped
from shared.ragas_utils import (
    compute_faithfulness_stats,
    format_results_markdown,
    load_test_set,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.3
MAX_TOKENS = 300
TOP_K = 3
RATE_LIMIT_SLEEP = 1.0  # seconds between answer-generation calls

TEST_SET_PATH = _ROOT / "data" / "test_set" / "test_set_150q.xlsx"
RESULTS_DIR = _ROOT / "results" / "ragas_evaluation"

SYSTEM_PROMPT = (
    "You are a compassionate smoking cessation counselor. "
    "Answer questions concisely (2-4 sentences)."
)

CONCISE_MAX_TOKENS = 150
CONCISE_SYSTEM_PROMPT = (
    "You are a smoking cessation counselor. "
    "Answer in 2-3 sentences using ONLY the facts provided. "
    "Do not add information beyond what is given."
)
CONCISE_RAG_TEMPLATE = (
    "You are a smoking cessation counselor.\n"
    "Answer the question in 2-3 sentences using ONLY facts from the "
    "knowledge base below.\n"
    "Do NOT add information, examples, or details not explicitly stated "
    "in the knowledge base.\n\n"
    "KNOWLEDGE BASE:\n{knowledge}"
)

# Ibrahim's reference rows for the comparison table (from paper screenshot)
EBRAHIM_REFERENCE = [
    {
        "config": "Ibrahim: Base LLM",
        "mean": 0.58,
        "sd": 0.22,
        "median": 0.61,
        "ci_lower": 0.42,
        "ci_upper": 0.74,
        "hallucination_rate": 0.40,
        "pct_high_risk": 20,
        "n": 10,
    },
    {
        "config": "Ibrahim: WebRAG",
        "mean": 0.86,
        "sd": 0.11,
        "median": 0.88,
        "ci_lower": 0.84,
        "ci_upper": 0.88,
        "hallucination_rate": 0.14,
        "pct_high_risk": 4,
        "n": 100,
    },
]

ALL_CONFIGS = ["baseline", "ai_rag", "human_rag", "web_rag"]


# ---------------------------------------------------------------------------
# Phase B: ChromaDB collection helpers
# ---------------------------------------------------------------------------


def build_collection(
    chroma_client: chromadb.Client,
    name: str,
    qa_pairs: list[dict],
) -> chromadb.Collection:
    """Build an ephemeral ChromaDB collection from QA pairs.

    Args:
        chroma_client: Active ChromaDB client.
        name: Collection name (will be recreated if exists).
        qa_pairs: List of dicts with 'question' and 'answer' keys.

    Returns:
        Populated ChromaDB collection.
    """
    # Delete if exists for a clean slate
    try:
        chroma_client.delete_collection(name)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 100
    for i in range(0, len(qa_pairs), batch_size):
        batch = qa_pairs[i : i + batch_size]
        documents = [f"Q: {p['question']}\nA: {p['answer']}" for p in batch]
        ids = [str(p.get("id", f"{name}_{i + j}")) for j, p in enumerate(batch)]
        metadatas = [{"question": p["question"], "answer": p["answer"]} for p in batch]
        collection.add(documents=documents, ids=ids, metadatas=metadatas)

    return collection


def retrieve_contexts(
    collection: chromadb.Collection,
    query: str,
    n_results: int = TOP_K,
) -> list[str]:
    """Retrieve top-k context chunks via semantic similarity.

    Args:
        collection: ChromaDB collection to query.
        query: The user question.
        n_results: Number of chunks to retrieve.

    Returns:
        List of retrieved document strings.
    """
    results = collection.query(query_texts=[query], n_results=n_results)
    if results["documents"] and results["documents"][0]:
        return list(results["documents"][0])
    return []


# ---------------------------------------------------------------------------
# Phase C: Answer generation
# ---------------------------------------------------------------------------


def generate_baseline_answer(oai_client: OpenAI, question: str, concise: bool = False) -> str:
    """Generate answer without any RAG context (baseline LLM only).

    Args:
        oai_client: Initialized OpenAI client.
        question: User's question.
        concise: Use strict concise prompt and lower max_tokens.

    Returns:
        Generated answer string.
    """
    sys_prompt = CONCISE_SYSTEM_PROMPT if concise else SYSTEM_PROMPT
    tokens = CONCISE_MAX_TOKENS if concise else MAX_TOKENS
    try:
        response = oai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": question},
            ],
            temperature=TEMPERATURE,
            max_tokens=tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "account_deactivated" in err_str or "invalid_api_key" in err_str:
            print(f"  [FATAL] Authentication error — aborting: {e}")
            raise SystemExit(1)
        print(f"  [WARN] Baseline generation error: {e}")
        return ""


def generate_rag_answer(
    oai_client: OpenAI,
    question: str,
    contexts: list[str],
    concise: bool = False,
) -> str:
    """Generate answer using retrieved contexts as knowledge base.

    Args:
        oai_client: Initialized OpenAI client.
        question: User's question.
        contexts: Retrieved context strings.
        concise: Use strict concise prompt and lower max_tokens.

    Returns:
        Generated answer string.
    """
    knowledge = "\n\n".join(contexts)
    if concise:
        system_prompt = CONCISE_RAG_TEMPLATE.format(knowledge=knowledge)
    else:
        system_prompt = (
            f"You are a compassionate smoking cessation counselor.\n"
            f"Use the following knowledge base to answer questions.\n"
            f"Base your answer on the knowledge provided.\n\n"
            f"KNOWLEDGE BASE:\n{knowledge}"
        )
    tokens = CONCISE_MAX_TOKENS if concise else MAX_TOKENS
    try:
        response = oai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=TEMPERATURE,
            max_tokens=tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "account_deactivated" in err_str or "invalid_api_key" in err_str:
            print(f"  [FATAL] Authentication error — aborting: {e}")
            raise SystemExit(1)
        print(f"  [WARN] RAG generation error: {e}")
        return ""


# ---------------------------------------------------------------------------
# Phase D: RAGAS evaluation runner
# ---------------------------------------------------------------------------


def _safe_batch_score(metric, inputs: list[dict]) -> list[float]:
    """Call metric.batch_score() and extract float values, returning NaN on error.

    Args:
        metric: A ragas.metrics.collections metric instance.
        inputs: List of dicts matching the metric's ascore() kwargs.

    Returns:
        List of float scores (NaN where scoring failed).
    """
    nan = float("nan")
    try:
        results = metric.batch_score(inputs)
        return [
            float(r.value) if r is not None and r.value is not None else nan
            for r in results
        ]
    except Exception as e:
        print(f"    [WARN] batch_score error for {type(metric).__name__}: {e}")
        return [nan] * len(inputs)


def run_ragas_evaluation(
    samples: list[SingleTurnSample],
    config_name: str,
    is_baseline: bool,
) -> dict[str, list[float]]:
    """Run RAGAS collections metrics via batch_score() for each metric.

    Uses the RAGAS 0.4.x InstructorLLM-based collections API.
    For baseline (empty contexts), Faithfulness will return NaN — expected.
    Context precision/recall are skipped for baseline.

    Args:
        samples: List of SingleTurnSample objects.
        config_name: Human-readable name for progress output.
        is_baseline: If True, skip context metrics.

    Returns:
        Dict mapping metric name -> list of per-question float scores.
    """
    print(f"\n  Running RAGAS evaluation for: {config_name}")
    print(f"  Samples: {len(samples)}")

    nan = float("nan")
    n = len(samples)

    # RAGAS collections metrics require AsyncOpenAI for their async scoring pipeline.
    # max_tokens=8192 prevents truncation in Faithfulness's verbose statement-by-statement JSON.
    async_oai = AsyncOpenAI(api_key=_OPENAI_API_KEY)
    ragas_llm = llm_factory(MODEL_NAME, provider="openai", client=async_oai, max_tokens=8192)
    ragas_emb = RagasOpenAIEmbeddings(client=async_oai)

    faith_metric = Faithfulness(llm=ragas_llm)
    relevancy_metric = AnswerRelevancy(llm=ragas_llm, embeddings=ragas_emb)

    # --- Build per-metric input dicts ---
    # Faithfulness: user_input, response, retrieved_contexts (non-empty required)
    faith_inputs = [
        {
            "user_input": s.user_input,
            "response": s.response,
            "retrieved_contexts": s.retrieved_contexts if s.retrieved_contexts else ["placeholder"],
        }
        for s in samples
    ]
    # AnswerRelevancy: user_input, response
    relevancy_inputs = [
        {"user_input": s.user_input, "response": s.response}
        for s in samples
    ]

    # 200K TPM limit: faithfulness burns ~2000 tokens/q × n in one async burst.
    # Sleep 65s between metrics so the bucket refills before the next call.
    _METRIC_COOLDOWN = 65  # seconds

    print("    Scoring: faithfulness...")
    faith_scores = _safe_batch_score(faith_metric, faith_inputs)

    print(f"    [rate-limit cooldown] sleeping {_METRIC_COOLDOWN}s...")
    time.sleep(_METRIC_COOLDOWN)

    print("    Scoring: answer_relevancy...")
    relevancy_scores = _safe_batch_score(relevancy_metric, relevancy_inputs)

    scores: dict[str, list[float]] = {
        "faithfulness": faith_scores,
        "answer_relevancy": relevancy_scores,
        "context_precision": [nan] * n,
        "context_recall": [nan] * n,
    }

    if not is_baseline:
        precision_metric = ContextPrecision(llm=ragas_llm)
        recall_metric = ContextRecall(llm=ragas_llm)

        # ContextPrecision: user_input, reference, retrieved_contexts
        precision_inputs = [
            {
                "user_input": s.user_input,
                "reference": s.reference,
                "retrieved_contexts": s.retrieved_contexts,
            }
            for s in samples
        ]
        # ContextRecall: user_input, retrieved_contexts, reference
        recall_inputs = [
            {
                "user_input": s.user_input,
                "retrieved_contexts": s.retrieved_contexts,
                "reference": s.reference,
            }
            for s in samples
        ]

        print(f"    [rate-limit cooldown] sleeping {_METRIC_COOLDOWN}s...")
        time.sleep(_METRIC_COOLDOWN)
        print("    Scoring: context_precision...")
        scores["context_precision"] = _safe_batch_score(precision_metric, precision_inputs)

        print(f"    [rate-limit cooldown] sleeping {_METRIC_COOLDOWN}s...")
        time.sleep(_METRIC_COOLDOWN)
        print("    Scoring: context_recall...")
        scores["context_recall"] = _safe_batch_score(recall_metric, recall_inputs)

    return scores


# ---------------------------------------------------------------------------
# Checkpointing helpers
# ---------------------------------------------------------------------------


def _checkpoint_path(config: str, n: Optional[int], concise: bool = False) -> Path:
    """Return checkpoint file path for a given config and question cap."""
    label = str(n) if n is not None else "all"
    prefix = "checkpoint_concise" if concise else "checkpoint"
    return RESULTS_DIR / f"{prefix}_{config}_{label}.jsonl"


def _load_checkpoint(config: str, n: Optional[int], concise: bool = False) -> list[dict]:
    """Load previously saved checkpoint records for this config+n.

    Args:
        config: Configuration name (e.g. 'ai_rag').
        n: The max_questions cap used for this run.
        concise: Whether to use concise checkpoint prefix.

    Returns:
        List of checkpoint record dicts, one per completed question.
    """
    path = _checkpoint_path(config, n, concise=concise)
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def _append_checkpoint(config: str, n: Optional[int], record: dict, concise: bool = False) -> None:
    """Append one question's result to the checkpoint file.

    Args:
        config: Configuration name.
        n: The max_questions cap.
        record: Dict with q_idx, question, answer, contexts, ground_truth.
        concise: Whether to use concise checkpoint prefix.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _checkpoint_path(config, n, concise=concise)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Phase E: Orchestration
# ---------------------------------------------------------------------------


def run_evaluation(
    configs: list[str],
    max_questions: int | None,
    resume: bool = False,
    concise: bool = False,
) -> dict:
    """Run the full evaluation pipeline.

    Args:
        configs: Subset of ['baseline', 'ai_rag', 'human_rag', 'web_rag'] to run.
        max_questions: Optional cap on test questions (None = all 127).
        resume: If True, load existing per-config checkpoints and skip
                already-answered questions.
        concise: If True, use strict concise prompts and lower max_tokens
                 to reduce response verbosity and improve faithfulness.

    Returns:
        Full results dict for JSON output.
    """
    n_cap = max_questions or 127
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_label = "CONCISE" if concise else "VERBOSE"

    print("=" * 70)
    print("RAGAS EVALUATION: AI-Generated vs Human-Curated RAG")
    print(f"Configs: {configs}  |  Questions: {n_cap}  |  Mode: {mode_label}  |  Resume: {resume}")
    print("=" * 70)

    # --- Load test set ---
    print(f"\nLoading test set from {TEST_SET_PATH.name}...")
    test_rows = load_test_set(TEST_SET_PATH, max_rows=max_questions)
    print(f"  Loaded {len(test_rows)} questions")

    # --- Load RAG datasets (only what's needed) ---
    print("\nLoading RAG datasets...")
    ai_data = load_ai_generated() if "ai_rag" in configs else []
    human_data = load_human_curated() if "human_rag" in configs else []
    web_data = load_web_scraped() if "web_rag" in configs else []
    if ai_data:
        print(f"  AI-generated:  {len(ai_data):,} pairs")
    if human_data:
        print(f"  Human-curated: {len(human_data):,} pairs")
    if web_data:
        print(f"  Web-scraped:   {len(web_data):,} pairs")

    # --- Build ChromaDB collections ---
    print("\nBuilding ChromaDB collections...")
    chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

    ai_collection = human_collection = web_collection = None
    if "ai_rag" in configs:
        ai_collection = build_collection(chroma_client, "ai_generated", ai_data)
        print(f"  ai_generated: {ai_collection.count()} docs")
    if "human_rag" in configs:
        human_collection = build_collection(chroma_client, "human_curated", human_data)
        print(f"  human_curated: {human_collection.count()} docs")
    if "web_rag" in configs:
        web_collection = build_collection(chroma_client, "web_scraped", web_data)
        print(f"  web_scraped: {web_collection.count()} docs")

    # --- Initialize OpenAI client ---
    oai_client = OpenAI(api_key=_OPENAI_API_KEY)

    # --- Load checkpoints (resume mode) ---
    checkpoints: dict[str, list[dict]] = {c: [] for c in configs}
    if resume:
        print("\nLoading checkpoints...")
        for config in configs:
            ckpt = _load_checkpoint(config, max_questions, concise=concise)
            checkpoints[config] = ckpt
            print(f"  {config}: {len(ckpt)} questions already done")

    # --- Generate answers per config ---
    config_samples: dict[str, list[SingleTurnSample]] = {c: [] for c in configs}

    # Pre-populate samples from checkpoints
    for config in configs:
        for rec in checkpoints[config]:
            config_samples[config].append(
                SingleTurnSample(
                    user_input=rec["question"],
                    retrieved_contexts=rec.get("contexts", []),
                    response=rec["answer"],
                    reference=rec["ground_truth"],
                )
            )

    print(f"\nGenerating answers for {len(test_rows)} questions × {len(configs)} configs...")
    print("-" * 70)

    for i, row in enumerate(test_rows, 1):
        question = row["question"]
        ground_truth = row["ground_truth"]
        q_idx = i - 1  # 0-based index for checkpoint matching

        print(f"[{i:3d}/{len(test_rows)}] {question[:60]}...")

        if "baseline" in configs:
            if q_idx < len(checkpoints["baseline"]):
                print(f"  [SKIP baseline] (checkpoint)")
            else:
                answer = generate_baseline_answer(oai_client, question, concise=concise)
                config_samples["baseline"].append(
                    SingleTurnSample(
                        user_input=question,
                        retrieved_contexts=[],
                        response=answer,
                        reference=ground_truth,
                    )
                )
                _append_checkpoint("baseline", max_questions, {
                    "q_idx": q_idx, "question": question,
                    "answer": answer, "contexts": [], "ground_truth": ground_truth,
                }, concise=concise)
                time.sleep(RATE_LIMIT_SLEEP)

        if "ai_rag" in configs and ai_collection is not None:
            if q_idx < len(checkpoints["ai_rag"]):
                print(f"  [SKIP ai_rag] (checkpoint)")
            else:
                contexts = retrieve_contexts(ai_collection, question)
                answer = generate_rag_answer(oai_client, question, contexts, concise=concise)
                config_samples["ai_rag"].append(
                    SingleTurnSample(
                        user_input=question,
                        retrieved_contexts=contexts,
                        response=answer,
                        reference=ground_truth,
                    )
                )
                _append_checkpoint("ai_rag", max_questions, {
                    "q_idx": q_idx, "question": question,
                    "answer": answer, "contexts": contexts, "ground_truth": ground_truth,
                }, concise=concise)
                time.sleep(RATE_LIMIT_SLEEP)

        if "human_rag" in configs and human_collection is not None:
            if q_idx < len(checkpoints["human_rag"]):
                print(f"  [SKIP human_rag] (checkpoint)")
            else:
                contexts = retrieve_contexts(human_collection, question)
                answer = generate_rag_answer(oai_client, question, contexts, concise=concise)
                config_samples["human_rag"].append(
                    SingleTurnSample(
                        user_input=question,
                        retrieved_contexts=contexts,
                        response=answer,
                        reference=ground_truth,
                    )
                )
                _append_checkpoint("human_rag", max_questions, {
                    "q_idx": q_idx, "question": question,
                    "answer": answer, "contexts": contexts, "ground_truth": ground_truth,
                }, concise=concise)
                time.sleep(RATE_LIMIT_SLEEP)

        if "web_rag" in configs and web_collection is not None:
            if q_idx < len(checkpoints["web_rag"]):
                print(f"  [SKIP web_rag] (checkpoint)")
            else:
                contexts = retrieve_contexts(web_collection, question)
                answer = generate_rag_answer(oai_client, question, contexts, concise=concise)
                config_samples["web_rag"].append(
                    SingleTurnSample(
                        user_input=question,
                        retrieved_contexts=contexts,
                        response=answer,
                        reference=ground_truth,
                    )
                )
                _append_checkpoint("web_rag", max_questions, {
                    "q_idx": q_idx, "question": question,
                    "answer": answer, "contexts": contexts, "ground_truth": ground_truth,
                }, concise=concise)
                time.sleep(RATE_LIMIT_SLEEP)

    # --- Run RAGAS per config ---
    print("\n" + "=" * 70)
    print("RUNNING RAGAS EVALUATION")
    print("=" * 70)

    # 120s inter-config cooldown: after scoring one config's metrics,
    # lingering async requests may still be in the 60s sliding TPM window.
    # 120s guarantees they've all expired before the next config's faithfulness
    # burst starts.
    _INTER_CONFIG_COOLDOWN = 120  # seconds

    all_scores: dict[str, dict[str, list[float]]] = {}
    for idx, config in enumerate(configs):
        samples = config_samples[config]
        if not samples:
            continue
        if idx > 0:
            print(f"\n  [inter-config cooldown] sleeping {_INTER_CONFIG_COOLDOWN}s "
                  f"before {config}...")
            time.sleep(_INTER_CONFIG_COOLDOWN)
        is_baseline = config == "baseline"
        all_scores[config] = run_ragas_evaluation(samples, config, is_baseline)

    # --- Compute faithfulness stats ---
    config_stats: dict[str, dict] = {}
    for config in configs:
        faith_scores = all_scores.get(config, {}).get("faithfulness", [])
        config_stats[config] = compute_faithfulness_stats(faith_scores)

    # --- Print summary table ---
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(
        f"\n{'Config':<28} {'Mean':>6} {'SD':>6} {'Median':>8} "
        f"{'HallucinRate':>14} {'HighRisk%':>10} {'n':>5}"
    )
    print("-" * 80)
    for config, stats in config_stats.items():
        label = config.replace("_", " ").title()
        print(
            f"{label:<28} {stats['mean']:>6.3f} {stats['sd']:>6.3f} "
            f"{stats['median']:>8.3f} {stats['hallucination_rate']:>14.3f} "
            f"{stats['pct_high_risk']:>9.1f}% {stats['n']:>5}"
        )

    # --- Format Markdown ---
    md_table = format_results_markdown(
        config_stats=config_stats,
        ebrahim_reference=EBRAHIM_REFERENCE,
        full_metrics=all_scores,
    )

    # --- Save outputs ---
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model": MODEL_NAME,
            "num_questions": len(test_rows),
            "max_questions_cap": max_questions,
            "configs_run": configs,
            "ai_dataset_size": len(ai_data) if ai_data else None,
            "human_dataset_size": len(human_data) if human_data else None,
            "top_k": TOP_K,
            "ragas_metrics": ["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
            "concise_mode": concise,
        },
        "faithfulness_stats": config_stats,
        "all_scores": all_scores,
        "ebrahim_reference": EBRAHIM_REFERENCE,
    }

    suffix = f"_concise" if concise else ""
    json_path = RESULTS_DIR / f"ragas_eval{suffix}_{timestamp}.json"
    md_path = RESULTS_DIR / f"ragas_eval{suffix}_{timestamp}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# RAGAS Evaluation Results\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n")
        f.write(f"**n:** {len(test_rows)} questions  |  **Model:** {MODEL_NAME}\n\n")
        f.write(md_table)

    print(f"\n{'=' * 70}")
    print(f"JSON saved: {json_path}")
    print(f"MD  saved:  {md_path}")
    print("=" * 70)

    return output


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RAGAS evaluation: AI-Generated vs Human-Curated RAG"
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        choices=ALL_CONFIGS,
        default=ALL_CONFIGS,
        help="Which configs to run (default: all three)",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        metavar="N",
        help="Cap test questions for sanity checks (default: all 127)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Resume from checkpoints (skip already-answered questions)",
    )
    parser.add_argument(
        "--concise",
        action="store_true",
        default=False,
        help="Use strict concise prompts (2-3 sentences, grounded only) to reduce verbosity",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_evaluation(
        configs=args.configs,
        max_questions=args.max_questions,
        resume=args.resume,
        concise=args.concise,
    )
