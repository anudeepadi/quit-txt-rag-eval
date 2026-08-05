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

import hashlib
import importlib
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

# Mark this process as an optimization run BEFORE any project import. Anything
# that reaches for the frozen test questions from here raises TestSetLeakError
# instead of silently contaminating the benchmark (shared.question_split).
os.environ["EVO_OPTIMIZING"] = "1"

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from data_gen_prepare import (
    HUMAN_KB_PATH,
    OPENAI_API_KEY,
    RANDOM_SEED,
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
from evo_agent import Run
from openai import OpenAI


# Weights for combined score
W_RAG_FAITHFULNESS = 0.40   # how well the generated KB supports RAG answers
W_SPECIFICITY = 0.20        # clinical detail in generated answers
W_TONE = 0.10               # conversational naturalness of questions
W_GROUNDEDNESS = 0.15       # no hallucination in generated answers
W_CLINICAL = 0.15           # clinical correctness

# Dataset artifacts live OUTSIDE code/ and datasets/ so the harness_integrity
# gate's pathspecs never see them (docs/dataset_generation_protocol.md).
_ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "generated_artifacts"


def _count_duplicates(pairs: list[dict]) -> tuple[int, int]:
    """Manifest counters A2: exact + fuzzy question duplicates (count-only).

    Exact = identical after lowercasing/whitespace-collapse. Fuzzy = Jaccard
    >= 0.9 on question token sets, counted among non-exact-duplicate pairs.
    Reporting only — nothing is filtered (epoch-4 comparability).
    """
    normalized = [" ".join(p["question"].lower().split()) for p in pairs]
    seen: set[str] = set()
    exact = 0
    survivors: list[set[str]] = []
    for text in normalized:
        if text in seen:
            exact += 1
            continue
        seen.add(text)
        survivors.append(set(text.split()))

    fuzzy = 0
    for i in range(len(survivors)):
        a = survivors[i]
        for j in range(i + 1, len(survivors)):
            b = survivors[j]
            union = len(a | b)
            if union and len(a & b) / union >= 0.9:
                fuzzy += 1
                break  # count each question at most once
    return exact, fuzzy


def _write_dataset_artifacts(
    all_generated: list[dict],
    gen_stats: dict,
    avg_quality: dict,
    n_chunks: int,
    hypothesis: str,
    gen_model: str,
    gen_temp: float,
    gen_max_tokens: int,
    qa_per_source: int,
    gen_prompt: str,
) -> None:
    """Persist the generated KB with provenance + the version manifest.

    Dataset-generation protocol §2 and §4. Score-neutral: runs after scoring,
    writes outside the gate's pathspecs, and never mutates the pair list the
    benchmark used.
    """
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(_ARTIFACTS_DIR / "generated_kb.jsonl", "w", encoding="utf-8") as f:
        for p in all_generated:
            f.write(json.dumps({
                "question": p["question"],
                "answer": p["answer"],
                "source_id": p.get("_source_id", ""),
                "source_sha256": p.get("_source_sha256", ""),
                "source_excerpt": p.get("_source_content", "")[:300],
            }, ensure_ascii=False) + "\n")

    dup_exact, dup_fuzzy = _count_duplicates(all_generated)
    try:
        import subprocess
        harness_commit = subprocess.run(
            ["git", "-C", str(Path(__file__).parent), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        harness_commit = "unknown"

    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "harness_commit": harness_commit,
        "hypothesis": hypothesis,
        "source_snapshot": {
            "file": "datasets/human-rag/human_curated_qa.jsonl",
            "sha256": hashlib.sha256(HUMAN_KB_PATH.read_bytes()).hexdigest(),
            "n_chunks": n_chunks,
        },
        "model": gen_model,
        "parameters": {
            "temperature": gen_temp,
            "max_tokens": gen_max_tokens,
            "qa_per_source": qa_per_source,
        },
        "system_prompt": gen_prompt,
        "counts": {
            "n_raw": gen_stats.get("n_raw", 0),
            "n_rejected_wellformed": gen_stats.get("n_rejected_wellformed", 0),
            "n_chunks_failed": gen_stats.get("n_chunks_failed", 0),
            "n_duplicate_exact": dup_exact,
            "n_duplicate_fuzzy": dup_fuzzy,
            "n_kept": len(all_generated),
        },
        "quality_sample": {"n": 15, **avg_quality},
    }
    with open(_ARTIFACTS_DIR / "dataset_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n  Dataset artifacts written: {_ARTIFACTS_DIR} "
          f"(kept={len(all_generated)}, dup_exact={dup_exact}, dup_fuzzy={dup_fuzzy})")


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
    run = Run()
    # max_retries: transport errors (429/5xx) must not count as task failures
    oai_client = OpenAI(api_key=OPENAI_API_KEY, max_retries=5)
    chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

    # ── 2. Load source content ────────────────────────────────
    print("\nLoading source content chunks...")
    source_chunks = get_source_content_from_human_kb()
    print(f"  {len(source_chunks)} chunks loaded")

    # ── 3. Generate QA pairs ──────────────────────────────────
    print("\nGenerating QA pairs with agent's prompt...")
    all_generated = []
    chunk_sources = []  # track which source each pair came from
    chunk_stats = []    # per-chunk generation counts, attached to run_meta trace

    # Chunks are independent — generate in parallel (444 chunks at full
    # source parity would take ~45 min serially). Results are collected
    # in chunk order so KB construction stays deterministic.
    # gen_stats: manifest counters (dataset-generation protocol). Concurrent
    # increments are safe under the GIL for these int bumps, and exact
    # ordering doesn't matter for counts.
    gen_stats: dict = {}

    def _gen_for_chunk(chunk):
        return generate_qa_pairs(
            oai_client=oai_client,
            source_content=chunk["content"],
            system_prompt=gen_prompt,
            n_pairs=qa_per_source,
            model=gen_model,
            temperature=gen_temp,
            max_tokens=gen_max_tokens,
            stats=gen_stats,
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        per_chunk_pairs = list(pool.map(_gen_for_chunk, source_chunks))

    for i, (chunk, pairs) in enumerate(zip(source_chunks, per_chunk_pairs), 1):
        if i % 50 == 0 or i == len(source_chunks):
            print(f"  Chunk [{i}/{len(source_chunks)}]: generated {len(pairs)} pairs")
        chunk_stats.append({"chunk": i, "n_pairs": len(pairs),
                            "source_excerpt": chunk["content"][:300]})
        for p in pairs:
            p["_source_content"] = chunk["content"]  # for quality scoring
            # Provenance (protocol §2): pin each pair to its exact source text.
            p["_source_id"] = f"chunk_{i:03d}"
            p["_source_sha256"] = hashlib.sha256(chunk["content"].encode("utf-8")).hexdigest()
        all_generated.extend(pairs)

    # Fail-loud guard: a rate-limit storm makes whole chunks silently yield
    # zero pairs, so the benchmark would score a truncated KB as if it were
    # the hypothesis's fault. Above 5% chunk-call failures the measurement is
    # invalid — abort so the run FAILS visibly instead of committing garbage.
    n_chunks_failed = gen_stats.get("n_chunks_failed", 0)
    if n_chunks_failed > 0.05 * len(source_chunks):
        raise RuntimeError(
            f"generation measurement invalid: {n_chunks_failed}/{len(source_chunks)} "
            "chunk calls failed (rate-limit storm?). Re-run serially — do not "
            "score a truncated KB."
        )
    if n_chunks_failed:
        print(f"  WARNING: {n_chunks_failed} chunk call(s) failed — within the 5% "
              "tolerance, recorded in the manifest.")

    if not all_generated:
        print("\n✗ NO PAIRS GENERATED — prompt may be broken. Fix and retry.")
        raise RuntimeError("no QA pairs generated — generation prompt broken")

    n_pairs = len(all_generated)
    avg_answer_words = sum(len(p["answer"].split()) for p in all_generated) / n_pairs
    print(f"\n  Total generated: {n_pairs} pairs  |  Avg answer length: {avg_answer_words:.1f} words")

    # ── 4. Score QA quality directly ──────────────────────────
    print("\nScoring QA pair quality (specificity, tone, groundedness, clinical)...")
    quality_scores = {"specificity": [], "conversational_tone": [], "groundedness": [], "clinical_accuracy": []}

    # Score a seeded random sample of 15 (first-N sampling let weak pairs
    # hide past the cutoff when pair counts grew — epoch-3 fix)
    _rng = random.Random(RANDOM_SEED)
    sample = _rng.sample(all_generated, min(15, len(all_generated)))
    for i, pair in enumerate(sample, 1):
        qs = score_qa_quality(
            oai_client, pair["question"], pair["answer"],
            pair.get("_source_content", ""),
        )
        for k in quality_scores:
            quality_scores[k].append(qs[k])
        pair_avg = sum(qs.values()) / len(qs)
        run.report(
            f"qa_pair_{i:02d}",
            score=pair_avg,
            summary=(f"spec={qs['specificity']:.2f} tone={qs['conversational_tone']:.2f} "
                     f"ground={qs['groundedness']:.2f} clin={qs['clinical_accuracy']:.2f}"),
            question=pair["question"],
            answer=pair["answer"][:500],
            source_excerpt=pair.get("_source_content", "")[:300],
            **qs,
        )
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
            score = 0.0
            rag_scores.append(0.0)

        run.report(
            f"rag_q_{i:02d}",
            score=score,
            summary=f"faithfulness={score:.2f} ({len(answer.split())}w)",
            failure_reason=None if answer else "empty_answer_after_retries",
            question=question,
            answer=answer[:500],
            n_contexts=len(contexts),
        )

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

    # Combined score is a weighted composite, not a mean of task scores —
    # pass it to finish() explicitly. run_meta trace carries the breakdown
    # for future readers (orchestrator / verifier / ideator); report() is
    # required because log()-only tasks are never flushed to trace files.
    run.report(
        "run_meta",
        score=combined,
        summary=(f"combined={combined:.4f} human={human_baseline:.4f} "
                 f"relative={relative_pct:.1f}%"),
        rag_faithfulness=avg_rag_faithfulness,
        qa_quality=avg_quality,
        human_baseline=human_baseline,
        relative_pct=relative_pct,
        n_pairs_generated=n_pairs,
        avg_answer_words=avg_answer_words,
        hypothesis=hypothesis,
        gen_model=gen_model,
        gen_temperature=gen_temp,
        qa_per_source=qa_per_source,
        chunk_stats=chunk_stats,
    )
    run.finish(score=combined)

    # ── 7b. Dataset artifacts (provenance + manifest) ─────────
    _write_dataset_artifacts(
        all_generated=all_generated,
        gen_stats=gen_stats,
        avg_quality=avg_quality,
        n_chunks=len(source_chunks),
        hypothesis=hypothesis,
        gen_model=gen_model,
        gen_temp=gen_temp,
        gen_max_tokens=gen_max_tokens,
        qa_per_source=qa_per_source,
        gen_prompt=gen_prompt,
    )

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
