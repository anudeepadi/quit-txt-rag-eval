#!/usr/bin/env python3
"""QuitTxt Autoresearch — Experiment Runner.

Fixed infrastructure. NOT modified by the agent.
Imports config from experiment.py, runs one evaluation, logs result.

Usage:
    python3 autoresearch/run_experiment.py
"""

import time
import sys
from pathlib import Path

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from prepare import (
    OPENAI_API_KEY,
    build_collection,
    compute_word_stats,
    get_best_score,
    get_experiment_count,
    get_test_questions,
    load_dataset_for_config,
    log_result,
    score_faithfulness_proxy,
)

import chromadb
from chromadb.config import Settings
from openai import OpenAI


def run_one_experiment() -> None:
    """Execute a single experiment using the current experiment.py config."""

    # ── 1. Load config from experiment.py ──────────────────────
    # Re-import each run so the agent's changes take effect
    import importlib
    import experiment
    importlib.reload(experiment)

    hypothesis = experiment.HYPOTHESIS
    target_config = experiment.TARGET_CONFIG
    temperature = experiment.TEMPERATURE
    max_tokens = experiment.MAX_TOKENS
    top_k = experiment.TOP_K
    rag_template = experiment.RAG_TEMPLATE

    experiment_id = get_experiment_count() + 1
    best_score = get_best_score()

    print("=" * 60)
    print(f"AUTORESEARCH — Experiment #{experiment_id}")
    print(f"Hypothesis: {hypothesis}")
    print(f"Config: {target_config}  |  temp={temperature}  |  "
          f"max_tokens={max_tokens}  |  top_k={top_k}")
    print(f"Current best score: {best_score:.4f}")
    print("=" * 60)

    t0 = time.time()

    # ── 2. Setup ───────────────────────────────────────────────
    print("\nLoading dataset...")
    qa_pairs = load_dataset_for_config(target_config)
    print(f"  {len(qa_pairs):,} QA pairs")

    print("Building ChromaDB collection...")
    chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
    collection = build_collection(chroma_client, target_config, qa_pairs)
    print(f"  {collection.count()} docs indexed")

    test_rows = get_test_questions()
    print(f"  {len(test_rows)} test questions")

    oai_client = OpenAI(api_key=OPENAI_API_KEY)

    # ── 3. Generate answers ────────────────────────────────────
    print("\nGenerating answers...")
    answers = []
    contexts_list = []

    for i, row in enumerate(test_rows, 1):
        question = row["question"]

        # Retrieve
        results = collection.query(query_texts=[question], n_results=top_k)
        contexts = results["documents"][0] if results["documents"] and results["documents"][0] else []

        # Generate
        knowledge = "\n\n".join(contexts)
        system_prompt = rag_template.format(knowledge=knowledge)

        try:
            response = oai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [{i}] ERROR: {e}")
            answer = ""

        answers.append(answer)
        contexts_list.append(contexts)

        if i % 5 == 0:
            print(f"  [{i}/{len(test_rows)}] generated")

    # ── 4. Score with fast proxy ───────────────────────────────
    print("\nScoring with LLM-as-judge proxy...")
    scores = []
    questions = [r["question"] for r in test_rows]

    for i, (q, a, ctx) in enumerate(zip(questions, answers, contexts_list), 1):
        if not a:
            scores.append(0.0)
            continue
        score = score_faithfulness_proxy(oai_client, q, a, ctx)
        scores.append(score)

        if i % 5 == 0:
            print(f"  [{i}/{len(test_rows)}] scored")

    avg_score = sum(scores) / len(scores) if scores else 0.0
    word_stats = compute_word_stats(answers)

    # ── 5. Compare and verdict ─────────────────────────────────
    improved = avg_score > best_score
    verdict = "KEEP" if improved else "DISCARD"

    elapsed = time.time() - t0

    # ── 6. Log result ──────────────────────────────────────────
    log_result(
        experiment_id=experiment_id,
        hypothesis=hypothesis,
        target_config=target_config,
        score=avg_score,
        word_stats=word_stats,
        temperature=temperature,
        max_tokens=max_tokens,
        top_k=top_k,
        verdict=verdict,
    )

    # ── 7. Print summary ──────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"RESULT — Experiment #{experiment_id}")
    print("-" * 60)
    print(f"  Hypothesis:   {hypothesis}")
    print(f"  Config:       {target_config}")
    print(f"  Score:        {avg_score:.4f}  (best: {best_score:.4f})")
    print(f"  Avg words:    {word_stats['avg']} (min={word_stats['min']}, max={word_stats['max']})")
    print(f"  Time:         {elapsed:.1f}s")
    print()

    if improved:
        delta = avg_score - best_score
        print(f"  ★ KEEP — improved by +{delta:.4f}")
        print(f"    New best: {avg_score:.4f}")
    else:
        delta = best_score - avg_score
        print(f"  ✗ DISCARD — worse by -{delta:.4f}")
        print(f"    Best remains: {best_score:.4f}")
        print(f"    Revert experiment.py and try a different hypothesis.")

    print("=" * 60)

    # ── 8. Show per-question breakdown ─────────────────────────
    print("\nPer-question scores:")
    for i, (q, s, a) in enumerate(zip(questions, scores, answers), 1):
        words = len(a.split())
        marker = "✓" if s >= 0.7 else "✗" if s < 0.5 else "~"
        print(f"  {marker} [{i:2d}] {s:.1f}  ({words:2d}w)  {q[:55]}...")

    # Print 2 lowest-scoring answers for debugging
    ranked = sorted(enumerate(zip(questions, answers, scores, contexts_list)), key=lambda x: x[1][2])
    print("\n── Lowest-scoring answers (for debugging) ──")
    for idx, (q, a, s, ctx) in ranked[:2]:
        ctx_words = sum(len(c.split()) for c in ctx)
        print(f"\n  Q: {q}")
        print(f"  A ({len(a.split())}w): {a[:200]}...")
        print(f"  Score: {s:.2f}  |  Context: {ctx_words} words across {len(ctx)} chunks")


if __name__ == "__main__":
    run_one_experiment()
