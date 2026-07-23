#!/usr/bin/env python3
"""QuitTxt Data-Generation Autoresearch — Experiment Runner.

Fixed infrastructure. NOT modified by the agent.
Imports config from data_gen_experiment.py, runs one full cycle, logs result.

The cycle:
  1. Load source content (chunks from human KB)
  2. Generate QA pairs using the agent's prompt
  3. Score QA pair quality directly (specificity, tone, groundedness, clinical)
  4. Build ChromaDB from generated pairs → run RAG eval → score faithfulness
  5. Run same RAG eval against human KB baseline
  6. Compute combined score + relative performance
  7. Log everything

Usage:
    cd gemini-protocol/code
    python3 autoresearch/run_data_gen_experiment.py
"""

import importlib
import os
import sys
import time
from pathlib import Path

# Mark this process as an optimization run BEFORE any project import. Anything
# that reaches for the frozen test questions from here raises TestSetLeakError
# instead of silently contaminating the benchmark (shared.question_split).
os.environ["EVO_OPTIMIZING"] = "1"

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from data_gen_prepare import (
    OPENAI_API_KEY,
    build_collection,
    generate_qa_pairs,
    get_best_score,
    get_experiment_count,
    get_source_content_from_human_kb,
    load_test_questions,
    log_result,
    score_faithfulness,
    score_human_baseline,
    score_qa_quality,
)

import chromadb
from chromadb.config import Settings
from openai import OpenAI


# Weights for combined score
W_RAG_FAITHFULNESS = 0.40   # how well the generated KB supports RAG answers
W_SPECIFICITY = 0.20        # clinical detail in generated answers
W_TONE = 0.10               # conversational naturalness of questions
W_GROUNDEDNESS = 0.15       # no hallucination in generated answers
W_CLINICAL = 0.15           # clinical correctness


def run_one_experiment() -> None:
    """Execute a single data-generation experiment."""

    # ── 1. Load config ────────────────────────────────────────
    import data_gen_experiment as cfg
    importlib.reload(cfg)

    hypothesis = cfg.HYPOTHESIS
    gen_model = cfg.GEN_MODEL
    gen_temp = cfg.GEN_TEMPERATURE
    gen_max_tokens = cfg.GEN_MAX_TOKENS
    qa_per_source = cfg.QA_PER_SOURCE
    gen_prompt = cfg.GEN_SYSTEM_PROMPT
    rag_template = cfg.RAG_TEMPLATE
    rag_temp = cfg.RAG_TEMPERATURE
    rag_max_tokens = cfg.RAG_MAX_TOKENS
    rag_top_k = cfg.RAG_TOP_K

    exp_id = get_experiment_count() + 1
    best_score = get_best_score()

    print("=" * 70)
    print(f"DATA-GEN AUTORESEARCH — Experiment #{exp_id}")
    print(f"Hypothesis: {hypothesis}")
    print(f"Gen model: {gen_model}  |  temp={gen_temp}  |  "
          f"max_tokens={gen_max_tokens}  |  qa_per_source={qa_per_source}")
    print(f"Current best combined score: {best_score:.4f}")
    print("=" * 70)

    t0 = time.time()
    oai_client = OpenAI(api_key=OPENAI_API_KEY)
    chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

    # ── 2. Load source content ────────────────────────────────
    print("\nLoading source content chunks...")
    source_chunks = get_source_content_from_human_kb()
    print(f"  {len(source_chunks)} chunks loaded")

    # ── 3. Generate QA pairs ──────────────────────────────────
    print("\nGenerating QA pairs with agent's prompt...")
    all_generated = []
    chunk_sources = []  # track which source each pair came from

    for i, chunk in enumerate(source_chunks, 1):
        pairs = generate_qa_pairs(
            oai_client=oai_client,
            source_content=chunk["content"],
            system_prompt=gen_prompt,
            n_pairs=qa_per_source,
            model=gen_model,
            temperature=gen_temp,
            max_tokens=gen_max_tokens,
        )
        print(f"  Chunk [{i}/{len(source_chunks)}]: generated {len(pairs)} pairs")
        for p in pairs:
            p["_source_content"] = chunk["content"]  # for quality scoring
        all_generated.extend(pairs)

    if not all_generated:
        print("\n✗ NO PAIRS GENERATED — prompt may be broken. Fix and retry.")
        return

    n_pairs = len(all_generated)
    avg_answer_words = sum(len(p["answer"].split()) for p in all_generated) / n_pairs
    print(f"\n  Total generated: {n_pairs} pairs  |  Avg answer length: {avg_answer_words:.1f} words")

    # ── 4. Score QA quality directly ──────────────────────────
    print("\nScoring QA pair quality (specificity, tone, groundedness, clinical)...")
    quality_scores = {"specificity": [], "conversational_tone": [], "groundedness": [], "clinical_accuracy": []}

    # Score a sample (up to 15 pairs for speed)
    sample = all_generated[:15]
    for i, pair in enumerate(sample, 1):
        qs = score_qa_quality(
            oai_client, pair["question"], pair["answer"],
            pair.get("_source_content", ""),
        )
        for k in quality_scores:
            quality_scores[k].append(qs[k])
        if i % 5 == 0:
            print(f"  [{i}/{len(sample)}] scored")

    avg_quality = {k: sum(v) / len(v) if v else 0.5 for k, v in quality_scores.items()}
    print(f"  Specificity: {avg_quality['specificity']:.3f}  |  "
          f"Tone: {avg_quality['conversational_tone']:.3f}  |  "
          f"Groundedness: {avg_quality['groundedness']:.3f}  |  "
          f"Clinical: {avg_quality['clinical_accuracy']:.3f}")

    # ── 5. RAG evaluation with generated KB ───────────────────
    print("\nBuilding ChromaDB from generated pairs...")
    # Strip internal metadata before indexing
    clean_pairs = [{"question": p["question"], "answer": p["answer"]} for p in all_generated]
    gen_collection = build_collection(chroma_client, "gen_experiment", clean_pairs)
    print(f"  {gen_collection.count()} docs indexed")

    test_questions = load_test_questions()
    print(f"  {len(test_questions)} test questions")

    print("\nRunning RAG evaluation with generated KB...")
    rag_scores = []
    rag_answers = []

    for i, row in enumerate(test_questions, 1):
        question = row["question"]

        # Retrieve from generated KB
        results = gen_collection.query(query_texts=[question], n_results=rag_top_k)
        contexts = results["documents"][0] if results["documents"] and results["documents"][0] else []

        # Generate RAG answer
        knowledge = "\n\n".join(contexts)
        system_prompt = rag_template.format(knowledge=knowledge)

        try:
            response = oai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=rag_temp,
                max_tokens=rag_max_tokens,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [{i}] RAG ERROR: {e}")
            answer = ""

        rag_answers.append(answer)

        if answer:
            score = score_faithfulness(oai_client, question, answer, contexts)
            rag_scores.append(score)
        else:
            rag_scores.append(0.0)

        if i % 5 == 0:
            print(f"  [{i}/{len(test_questions)}] evaluated")

    avg_rag_faithfulness = sum(rag_scores) / len(rag_scores) if rag_scores else 0.0
    print(f"\n  RAG Faithfulness (generated KB): {avg_rag_faithfulness:.4f}")

    # ── 6. Human KB baseline ──────────────────────────────────
    print("\nRunning human KB baseline for comparison...")
    human_baseline = score_human_baseline(
        oai_client, chroma_client, test_questions,
        rag_template, rag_temp, rag_max_tokens, rag_top_k,
    )
    print(f"  Human KB faithfulness: {human_baseline:.4f}")

    relative_pct = (avg_rag_faithfulness / human_baseline * 100) if human_baseline > 0 else 0.0

    # ── 7. Combined score ─────────────────────────────────────
    combined = (
        W_RAG_FAITHFULNESS * avg_rag_faithfulness
        + W_SPECIFICITY * avg_quality["specificity"]
        + W_TONE * avg_quality["conversational_tone"]
        + W_GROUNDEDNESS * avg_quality["groundedness"]
        + W_CLINICAL * avg_quality["clinical_accuracy"]
    )

    improved = combined > best_score
    verdict = "KEEP" if improved else "DISCARD"

    elapsed = time.time() - t0

    # ── 8. Log result ─────────────────────────────────────────
    log_result(
        experiment_id=exp_id,
        hypothesis=hypothesis,
        gen_model=gen_model,
        rag_faithfulness=avg_rag_faithfulness,
        qa_quality=avg_quality,
        combined_score=combined,
        human_baseline=human_baseline,
        relative_pct=relative_pct,
        n_pairs=n_pairs,
        avg_answer_words=avg_answer_words,
        gen_temperature=gen_temp,
        gen_max_tokens=gen_max_tokens,
        qa_per_source=qa_per_source,
        verdict=verdict,
    )

    # ── 9. Print summary ──────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"RESULT — Data-Gen Experiment #{exp_id}")
    print("-" * 70)
    print(f"  Hypothesis:       {hypothesis}")
    print(f"  Gen model:        {gen_model}")
    print(f"  Pairs generated:  {n_pairs}")
    print(f"  Avg answer words: {avg_answer_words:.1f}")
    print()
    print(f"  RAG Faithfulness: {avg_rag_faithfulness:.4f}")
    print(f"  QA Specificity:   {avg_quality['specificity']:.4f}")
    print(f"  QA Tone:          {avg_quality['conversational_tone']:.4f}")
    print(f"  QA Groundedness:  {avg_quality['groundedness']:.4f}")
    print(f"  QA Clinical:      {avg_quality['clinical_accuracy']:.4f}")
    print(f"  ─────────────────────────────────────")
    print(f"  COMBINED SCORE:   {combined:.4f}  (best: {best_score:.4f})")
    print(f"  Human baseline:   {human_baseline:.4f}")
    print(f"  Relative to human: {relative_pct:.1f}%")
    print(f"  Time:             {elapsed:.1f}s")
    print()

    if improved:
        delta = combined - best_score
        print(f"  ★ KEEP — improved by +{delta:.4f}")
        print(f"    New best: {combined:.4f}")
    else:
        delta = best_score - combined
        print(f"  ✗ DISCARD — worse by -{delta:.4f}")
        print(f"    Best remains: {best_score:.4f}")
        print(f"    Revert data_gen_experiment.py and try a different hypothesis.")

    print("=" * 70)

    # ── 10. Per-question RAG breakdown ────────────────────────
    print("\nPer-question RAG faithfulness scores:")
    for i, (row, s, a) in enumerate(zip(test_questions, rag_scores, rag_answers), 1):
        words = len(a.split()) if a else 0
        marker = "✓" if s >= 0.7 else "✗" if s < 0.5 else "~"
        print(f"  {marker} [{i:2d}] {s:.2f}  ({words:2d}w)  {row['question'][:55]}...")

    # Show 2 sample generated pairs for inspection
    print("\n── Sample generated QA pairs ──")
    for pair in all_generated[:3]:
        print(f"\n  Q: {pair['question']}")
        print(f"  A: {pair['answer'][:200]}...")


if __name__ == "__main__":
    run_one_experiment()
