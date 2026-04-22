#!/usr/bin/env python3
"""Large-dataset evaluation of the Exp5 winning config.

Scales the data-gen autoresearch harness from its iteration scale
(N_EVAL=20, N_SOURCE_CHUNKS=5, ~40 generated pairs) up to a full-test-set
evaluation (N_EVAL=150, N_SOURCE_CHUNKS=20, ~160 generated pairs) while
holding the generation prompt fixed to Exp5 (two-pass, temp=0.0).

Separate from `run_data_gen_experiment.py` so it does not pollute the
iteration log with a single, large, non-comparable run.

Results logged to: autoresearch/data_gen_large_results.tsv
"""
from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from data_gen_prepare import (
    OPENAI_API_KEY,
    RESULTS_FILE,  # noqa: F401 — intentionally unused; large run uses its own file
    build_collection,
    generate_qa_pairs,
    get_source_content_from_human_kb,
    load_test_questions,
    score_faithfulness,
    score_human_baseline,
    score_qa_quality,
)

# ── Large-run scale ────────────────────────────────────────────
N_EVAL_LARGE = 150          # full test set
N_SOURCE_CHUNKS_LARGE = 20  # covers ~200 human pairs out of 4431
QA_QUALITY_SAMPLE = 30      # pairs to sample for QA quality scoring

# ── Exp5 winning config (frozen) ───────────────────────────────
HYPOTHESIS = (
    "Large-dataset scale of Exp5 winning config: two-pass fact extraction, "
    "gpt-4o-mini, temp=0.0, 2-3 sentences. "
    f"N_EVAL={N_EVAL_LARGE}, N_SOURCE_CHUNKS={N_SOURCE_CHUNKS_LARGE}."
)
GEN_MODEL = "gpt-4o-mini"
GEN_TEMPERATURE = 0.0
GEN_MAX_TOKENS = 2500
QA_PER_SOURCE = 8

GEN_SYSTEM_PROMPT = (
    "You are a smoking cessation counseling expert generating training data "
    "for a medical AI chatbot used in a healthcare setting.\n\n"
    "TASK: From the provided source content, generate exactly {n} question-answer "
    "pairs using a TWO-PASS approach.\n\n"
    "CRITICAL CONSTRAINT — HEALTHCARE SAFETY:\n"
    "This is a health domain. Do NOT add, infer, or rephrase beyond what the "
    "source explicitly states.\n\n"
    "PASS 1 — FACT EXTRACTION:\n"
    "First, read the source and mentally identify the {n} most important distinct "
    "facts, statistics, medication names, techniques, or clinical findings. Each "
    "fact must be directly stated in the source text.\n\n"
    "PASS 2 — QA PAIR COMPOSITION:\n"
    "For each extracted fact, compose one question-answer pair:\n"
    "- Question: conversational, first-person, like texting a quit-smoking chatbot\n"
    "- Answer: 2-3 sentences using the source's own words. Include specific details "
    "(medication names, dosages, timeframes, percentages) exactly as written in "
    "the source. Do NOT paraphrase clinical terms or numbers.\n\n"
    "RULES:\n"
    "1. Every claim in every answer must trace to a specific sentence in the source.\n"
    "2. Cover {n} DIFFERENT topics — no repeated themes.\n"
    "3. No disclaimers, hedging, or generic advice unless the source says it.\n"
    "4. If the source doesn't contain {n} distinct facts, generate fewer pairs.\n\n"
    'Return a JSON object with key "qa_pairs" containing an array of objects, '
    'each with "question" (string) and "answer" (string) fields only.'
)

RAG_TEMPLATE = (
    "You are a smoking cessation counselor.\n"
    "Answer the question in 2-3 sentences using ONLY facts from the "
    "knowledge base below.\n"
    "Do NOT add information, examples, or details not explicitly stated "
    "in the knowledge base.\n\n"
    "KNOWLEDGE BASE:\n{knowledge}"
)
RAG_TEMPERATURE = 0.3
RAG_MAX_TOKENS = 150
RAG_TOP_K = 3

# Combined-score weights (same as iteration harness)
W_RAG_FAITHFULNESS = 0.40
W_SPECIFICITY = 0.20
W_TONE = 0.10
W_GROUNDEDNESS = 0.15
W_CLINICAL = 0.15

LARGE_RESULTS_FILE = Path(__file__).parent / "data_gen_large_results.tsv"
LARGE_TSV_HEADER = (
    "timestamp\thypothesis\tgen_model\t"
    "n_eval\tn_source_chunks\tn_pairs_generated\tavg_answer_words\t"
    "rag_faithfulness\tqa_specificity\tqa_tone\tqa_groundedness\tqa_clinical\t"
    "combined_score\thuman_baseline\trelative_pct\telapsed_s\n"
)


def log_large_result(row_values: dict) -> None:
    """Append one large-run result row."""
    if not LARGE_RESULTS_FILE.exists():
        LARGE_RESULTS_FILE.write_text(LARGE_TSV_HEADER)
    fields = [
        row_values["timestamp"],
        row_values["hypothesis"],
        row_values["gen_model"],
        str(row_values["n_eval"]),
        str(row_values["n_source_chunks"]),
        str(row_values["n_pairs_generated"]),
        f"{row_values['avg_answer_words']:.1f}",
        f"{row_values['rag_faithfulness']:.4f}",
        f"{row_values['qa_specificity']:.4f}",
        f"{row_values['qa_tone']:.4f}",
        f"{row_values['qa_groundedness']:.4f}",
        f"{row_values['qa_clinical']:.4f}",
        f"{row_values['combined_score']:.4f}",
        f"{row_values['human_baseline']:.4f}",
        f"{row_values['relative_pct']:.1f}",
        f"{row_values['elapsed_s']:.1f}",
    ]
    with open(LARGE_RESULTS_FILE, "a") as f:
        f.write("\t".join(fields) + "\n")


def run_large_experiment() -> None:
    print("=" * 70)
    print("LARGE-DATASET RUN — Exp5 winning config")
    print(f"  N_EVAL={N_EVAL_LARGE}  |  N_SOURCE_CHUNKS={N_SOURCE_CHUNKS_LARGE}  "
          f"|  QA_PER_SOURCE={QA_PER_SOURCE}")
    print(f"  Gen model: {GEN_MODEL}  |  temp={GEN_TEMPERATURE}")
    print("=" * 70)

    t0 = time.time()
    oai_client = OpenAI(api_key=OPENAI_API_KEY)
    chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

    # 1. Source chunks
    print("\nLoading source content chunks...")
    source_chunks = get_source_content_from_human_kb(n_chunks=N_SOURCE_CHUNKS_LARGE)
    print(f"  {len(source_chunks)} chunks loaded")

    # 2. Generate QA pairs
    print("\nGenerating QA pairs...")
    all_generated: list[dict] = []
    for i, chunk in enumerate(source_chunks, 1):
        pairs = generate_qa_pairs(
            oai_client=oai_client,
            source_content=chunk["content"],
            system_prompt=GEN_SYSTEM_PROMPT,
            n_pairs=QA_PER_SOURCE,
            model=GEN_MODEL,
            temperature=GEN_TEMPERATURE,
            max_tokens=GEN_MAX_TOKENS,
        )
        for p in pairs:
            p["_source_content"] = chunk["content"]
        all_generated.extend(pairs)
        print(f"  Chunk [{i:2d}/{len(source_chunks)}]: {len(pairs)} pairs  "
              f"(cumulative: {len(all_generated)})")

    if not all_generated:
        print("\n✗ NO PAIRS GENERATED — abort.")
        return

    n_pairs = len(all_generated)
    avg_answer_words = sum(len(p["answer"].split()) for p in all_generated) / n_pairs
    print(f"\n  Total: {n_pairs} pairs  |  Avg answer: {avg_answer_words:.1f} words")

    # 3. QA quality sample
    print(f"\nScoring QA quality on first {QA_QUALITY_SAMPLE} pairs...")
    quality_scores = {k: [] for k in (
        "specificity", "conversational_tone", "groundedness", "clinical_accuracy"
    )}
    sample = all_generated[:QA_QUALITY_SAMPLE]
    for i, pair in enumerate(sample, 1):
        qs = score_qa_quality(
            oai_client, pair["question"], pair["answer"],
            pair.get("_source_content", ""),
        )
        for k in quality_scores:
            quality_scores[k].append(qs[k])
        if i % 10 == 0:
            print(f"  [{i:2d}/{len(sample)}] scored")
    avg_quality = {k: sum(v) / len(v) for k, v in quality_scores.items()}
    print(f"  Specificity: {avg_quality['specificity']:.3f}  "
          f"Tone: {avg_quality['conversational_tone']:.3f}  "
          f"Grounded: {avg_quality['groundedness']:.3f}  "
          f"Clinical: {avg_quality['clinical_accuracy']:.3f}")

    # 4. RAG eval on generated KB
    print("\nIndexing generated KB in ChromaDB...")
    clean_pairs = [{"question": p["question"], "answer": p["answer"]} for p in all_generated]
    gen_collection = build_collection(chroma_client, "large_gen", clean_pairs)
    print(f"  {gen_collection.count()} docs indexed")

    test_questions = load_test_questions(max_rows=N_EVAL_LARGE)
    print(f"  {len(test_questions)} test questions loaded")

    print(f"\nRunning RAG eval on generated KB ({len(test_questions)} questions)...")
    rag_scores: list[float] = []
    for i, row in enumerate(test_questions, 1):
        question = row["question"]
        results = gen_collection.query(query_texts=[question], n_results=RAG_TOP_K)
        contexts = results["documents"][0] if results["documents"] and results["documents"][0] else []
        knowledge = "\n\n".join(contexts)
        system_prompt = RAG_TEMPLATE.format(knowledge=knowledge)
        try:
            response = oai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=RAG_TEMPERATURE,
                max_tokens=RAG_MAX_TOKENS,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [{i}] RAG ERROR: {e}")
            answer = ""
        if answer:
            rag_scores.append(score_faithfulness(oai_client, question, answer, contexts))
        else:
            rag_scores.append(0.0)
        if i % 20 == 0:
            running = sum(rag_scores) / len(rag_scores)
            print(f"  [{i:3d}/{len(test_questions)}] evaluated  "
                  f"(running avg: {running:.4f})")

    avg_rag_faithfulness = sum(rag_scores) / len(rag_scores)
    print(f"\n  RAG faithfulness (generated KB): {avg_rag_faithfulness:.4f}")

    # 5. Human baseline on same 150 questions
    print(f"\nHuman KB baseline ({len(test_questions)} questions)...")
    human_baseline = score_human_baseline(
        oai_client, chroma_client, test_questions,
        RAG_TEMPLATE, RAG_TEMPERATURE, RAG_MAX_TOKENS, RAG_TOP_K,
    )
    print(f"  Human KB faithfulness: {human_baseline:.4f}")
    relative_pct = (avg_rag_faithfulness / human_baseline * 100) if human_baseline > 0 else 0.0

    combined = (
        W_RAG_FAITHFULNESS * avg_rag_faithfulness
        + W_SPECIFICITY * avg_quality["specificity"]
        + W_TONE * avg_quality["conversational_tone"]
        + W_GROUNDEDNESS * avg_quality["groundedness"]
        + W_CLINICAL * avg_quality["clinical_accuracy"]
    )

    elapsed = time.time() - t0

    log_large_result({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hypothesis": HYPOTHESIS,
        "gen_model": GEN_MODEL,
        "n_eval": N_EVAL_LARGE,
        "n_source_chunks": N_SOURCE_CHUNKS_LARGE,
        "n_pairs_generated": n_pairs,
        "avg_answer_words": avg_answer_words,
        "rag_faithfulness": avg_rag_faithfulness,
        "qa_specificity": avg_quality["specificity"],
        "qa_tone": avg_quality["conversational_tone"],
        "qa_groundedness": avg_quality["groundedness"],
        "qa_clinical": avg_quality["clinical_accuracy"],
        "combined_score": combined,
        "human_baseline": human_baseline,
        "relative_pct": relative_pct,
        "elapsed_s": elapsed,
    })

    print("\n" + "=" * 70)
    print("LARGE-DATASET RESULT")
    print("-" * 70)
    print(f"  Pairs generated:   {n_pairs}")
    print(f"  Avg answer words:  {avg_answer_words:.1f}")
    print(f"  RAG Faithfulness:  {avg_rag_faithfulness:.4f}")
    print(f"  Specificity:       {avg_quality['specificity']:.4f}")
    print(f"  Tone:              {avg_quality['conversational_tone']:.4f}")
    print(f"  Groundedness:      {avg_quality['groundedness']:.4f}")
    print(f"  Clinical:          {avg_quality['clinical_accuracy']:.4f}")
    print(f"  Combined:          {combined:.4f}")
    print(f"  Human baseline:    {human_baseline:.4f}")
    print(f"  Relative to human: {relative_pct:.1f}%")
    print(f"  Elapsed:           {elapsed:.1f}s")
    print(f"  Log file:          {LARGE_RESULTS_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    run_large_experiment()
