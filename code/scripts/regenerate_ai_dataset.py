#!/usr/bin/env python3
"""Regenerate the AI-generated QA dataset using the autoresearch-optimized prompt.

Applies the Exp5 two-pass source-preserving generation prompt (temp=0.0,
GPT-4o-mini, 2-3 sentences) to the original source excerpts extracted from
the BACKUP of ai_generated_qa.jsonl (the original 5,936-pair dataset with
answer_source_excerpt fields).

Target: ~4,000 pairs for comparable retrieval coverage to human dataset (4,431).

Strategy:
  - Read from ORIGINAL backup (5,936 pairs with answer_source_excerpt)
  - Small chunks (500 chars) for granular fact extraction
  - 12 QA pairs per chunk
  - Dedup threshold 0.85 (less aggressive than 0.75)
  - Per-chunk checkpointing for reliable resume

Usage:
    cd gemini-protocol/code
    python3 scripts/regenerate_ai_dataset.py --dry-run        # show plan, no API calls
    python3 scripts/regenerate_ai_dataset.py                  # full run
    python3 scripts/regenerate_ai_dataset.py --resume         # continue interrupted run
    python3 scripts/regenerate_ai_dataset.py --max-urls 2     # test with 2 URLs
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("regenerate")

# ---------------------------------------------------------------------------
# Path setup & .env loading
# ---------------------------------------------------------------------------
_CODE_ROOT = Path(__file__).parent.parent
_PROJECT_ROOT = _CODE_ROOT.parent

_ENV_PATH = _CODE_ROOT / ".env"
if not _ENV_PATH.exists():
    _ENV_PATH = _PROJECT_ROOT / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not _OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set. Add it to code/.env or export it.")

from openai import OpenAI

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# IMPORTANT: Read source excerpts from the ORIGINAL backup, not the current
# (regenerated) file which lacks answer_source_excerpt fields.
_ORIGINAL_BACKUP = _PROJECT_ROOT / "datasets" / "human-ai" / "backups" / "ai_generated_qa_pre_regen_20260402_033005.jsonl"
_OUTPUT_FILE = _PROJECT_ROOT / "datasets" / "human-ai" / "pass2_temp0.2.jsonl"
_BACKUP_DIR = _PROJECT_ROOT / "datasets" / "human-ai" / "backups"
_CHECKPOINT_DIR = _PROJECT_ROOT / "datasets" / "human-ai" / "regen_checkpoints_v3"
_LOG_FILE = _PROJECT_ROOT / "datasets" / "human-ai" / "regeneration_log.jsonl"

# ---------------------------------------------------------------------------
# Config — tuned for ~4,000 pairs
# ---------------------------------------------------------------------------
CHUNK_SIZE = 500           # small chunks → more granular facts → more pairs
CHUNK_OVERLAP = 50         # small overlap for short chunks
QA_PER_CHUNK = 12          # more pairs per chunk
GEN_TEMPERATURE = 0.2      # slight creativity for pass 2 (pass 1 was 0.0)
GEN_MAX_TOKENS = 4000      # more tokens for 12 pairs
GEN_MODEL = "gpt-4o-mini"
SLEEP_BETWEEN_CHUNKS = 0.3
SLEEP_BETWEEN_URLS = 1.0
DEDUP_THRESHOLD = 0.90     # keep more diverse pairs for multi-pass merge

# ---------------------------------------------------------------------------
# Autoresearch-optimized prompt (Exp5: two-pass extraction, temp=0.0)
# ---------------------------------------------------------------------------
GEN_SYSTEM_PROMPT = """You are a smoking cessation counseling expert generating training data \
for a medical AI chatbot used in a healthcare setting.

TASK: From the provided source content, generate exactly {n} question-answer \
pairs using a TWO-PASS approach.

CRITICAL CONSTRAINT — HEALTHCARE SAFETY:
This is a health domain. Do NOT add, infer, or rephrase beyond what the \
source explicitly states.

PASS 1 — FACT EXTRACTION:
First, read the source and mentally identify the {n} most important distinct \
facts, statistics, medication names, techniques, or clinical findings. Each \
fact must be directly stated in the source text.

PASS 2 — QA PAIR COMPOSITION:
For each extracted fact, compose one question-answer pair:
- Question: conversational, first-person, like texting a quit-smoking chatbot
- Answer: 2-3 sentences using the source's own words. Include specific details \
(medication names, dosages, timeframes, percentages) exactly as written in \
the source. Do NOT paraphrase clinical terms or numbers.

RULES:
1. Every claim in every answer must trace to a specific sentence in the source.
2. Cover {n} DIFFERENT topics — no repeated themes.
3. No disclaimers, hedging, or generic advice unless the source says it.
4. If the source doesn't contain {n} distinct facts, generate fewer pairs.

Return a JSON object with key "qa_pairs" containing an array of objects, \
each with "question" (string) and "answer" (string) fields only."""


# ---------------------------------------------------------------------------
# Source reconstruction from original dataset
# ---------------------------------------------------------------------------
def load_source_excerpts(dataset_path: Path) -> list[dict]:
    """Load original dataset and reconstruct source content from excerpts.

    Returns a list of dicts, one per source_url, with:
      - url, source, category: metadata from the original pairs
      - content: concatenated unique excerpts (the reconstructed source)
      - n_excerpts: number of unique excerpts found
      - n_original_pairs: number of original pairs for this URL
    """
    log.info("Loading source excerpts from: %s", dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Original backup not found: {dataset_path}\n"
            f"Expected the pre-regeneration backup with answer_source_excerpt fields."
        )

    pairs: list[dict] = []
    with open(dataset_path) as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))

    log.info("Loaded %d pairs from backup", len(pairs))

    # Verify answer_source_excerpt exists
    has_excerpt = sum(1 for p in pairs if p.get("answer_source_excerpt"))
    log.info("Pairs with answer_source_excerpt: %d / %d (%.1f%%)",
             has_excerpt, len(pairs), 100 * has_excerpt / len(pairs) if pairs else 0)

    if has_excerpt < len(pairs) * 0.5:
        raise ValueError(
            f"Only {has_excerpt}/{len(pairs)} pairs have answer_source_excerpt. "
            f"Are you reading the correct backup file?"
        )

    # Group by URL, preserving order of first appearance
    url_order: list[str] = []
    by_url: dict[str, dict] = {}
    for p in pairs:
        url = p["source_url"]
        if url not in by_url:
            url_order.append(url)
            by_url[url] = {
                "url": url,
                "source": p["source"],
                "category": p.get("category", "general"),
                "excerpts": [],
                "seen_excerpts": set(),
                "n_original_pairs": 0,
            }
        by_url[url]["n_original_pairs"] += 1
        excerpt = p.get("answer_source_excerpt", "").strip()
        if excerpt and excerpt not in by_url[url]["seen_excerpts"]:
            by_url[url]["excerpts"].append(excerpt)
            by_url[url]["seen_excerpts"].add(excerpt)

    # Build result
    sources: list[dict] = []
    for url in url_order:
        info = by_url[url]
        content = "\n\n".join(info["excerpts"])
        sources.append({
            "url": info["url"],
            "source": info["source"],
            "category": info["category"],
            "content": content,
            "n_excerpts": len(info["excerpts"]),
            "n_original_pairs": info["n_original_pairs"],
        })

    return sources


# ---------------------------------------------------------------------------
# Content chunking
# ---------------------------------------------------------------------------
def chunk_content(content: str) -> list[str]:
    """Split content into overlapping chunks for focused QA generation."""
    chunks: list[str] = []
    start = 0
    while start < len(content):
        end = start + CHUNK_SIZE

        # Try to break at a paragraph boundary
        if end < len(content):
            newline_pos = content.rfind("\n", start + CHUNK_SIZE // 2, end + 100)
            if newline_pos > start:
                end = newline_pos

        chunk = content[start:end].strip()
        if len(chunk) > 30:  # skip tiny trailing chunks
            chunks.append(chunk)

        start = end - CHUNK_OVERLAP

    return chunks


# ---------------------------------------------------------------------------
# QA generation with optimized prompt
# ---------------------------------------------------------------------------
def generate_qa_pairs(
    client: OpenAI,
    content: str,
    source_info: dict,
    chunk_idx: int,
    total_chunks: int,
) -> list[dict]:
    """Generate QA pairs from a content chunk using the optimized prompt."""
    formatted_prompt = GEN_SYSTEM_PROMPT.format(n=QA_PER_CHUNK)

    try:
        t0 = time.time()
        resp = client.chat.completions.create(
            model=GEN_MODEL,
            messages=[
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": f"Source content:\n\n{content}"},
            ],
            temperature=GEN_TEMPERATURE,
            max_tokens=GEN_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        elapsed = time.time() - t0

        raw = json.loads(resp.choices[0].message.content)
        pairs = (
            raw if isinstance(raw, list)
            else raw.get("qa_pairs", raw.get("pairs", raw.get("questions", [])))
        )

        timestamp = datetime.now().isoformat()
        result: list[dict] = []
        for p in pairs:
            q = str(p.get("question", "")).strip()
            a = str(p.get("answer", "")).strip()
            if len(q) > 10 and len(a) > 20:
                result.append({
                    "question": q,
                    "answer": a,
                    "source": source_info["source"],
                    "source_url": source_info["url"],
                    "category": source_info["category"],
                    "topic": source_info["category"],
                    "generation_method": "autoresearch_exp5_two_pass",
                    "created_at": timestamp,
                })

        tokens_used = resp.usage.total_tokens if resp.usage else 0
        log.info("    Chunk [%d/%d]: %d pairs | %.1fs | %d tokens | %d chars input",
                 chunk_idx, total_chunks, len(result), elapsed, tokens_used, len(content))
        return result

    except Exception as e:
        log.error("    Chunk [%d/%d] GENERATION ERROR: %s", chunk_idx, total_chunks, e)
        return []


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------
def word_overlap(a: str, b: str) -> float:
    """Fraction of words in `a` that also appear in `b`."""
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa:
        return 0.0
    return len(wa & wb) / len(wa)


def deduplicate(pairs: list[dict]) -> list[dict]:
    """Remove near-duplicate questions by word overlap."""
    kept: list[dict] = []
    kept_questions: list[str] = []
    for p in pairs:
        q = p["question"]
        is_dup = any(
            word_overlap(q, kq) >= DEDUP_THRESHOLD for kq in kept_questions
        )
        if not is_dup:
            kept.append(p)
            kept_questions.append(q)
    return kept


# ---------------------------------------------------------------------------
# Per-chunk checkpointing (finer granularity than per-URL)
# ---------------------------------------------------------------------------
def _chunk_key(url: str, chunk_idx: int) -> str:
    raw = f"{url}__chunk_{chunk_idx}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _url_checkpoint_path(url: str) -> Path:
    key = hashlib.md5(url.encode()).hexdigest()[:12]
    return _CHECKPOINT_DIR / f"url_{key}.json"


def load_url_checkpoint(url: str) -> Optional[dict]:
    """Load checkpoint for a URL. Returns dict with 'pairs' and 'completed_chunks'."""
    p = _url_checkpoint_path(url)
    if p.exists():
        return json.loads(p.read_text())
    return None


def save_url_checkpoint(url: str, pairs: list[dict], completed_chunks: int, total_chunks: int) -> None:
    """Save checkpoint after each chunk completes."""
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    _url_checkpoint_path(url).write_text(json.dumps({
        "url": url,
        "completed_chunks": completed_chunks,
        "total_chunks": total_chunks,
        "n_pairs": len(pairs),
        "pairs": pairs,
        "updated_at": datetime.now().isoformat(),
    }, indent=2))


def append_log(entry: dict) -> None:
    """Append a structured log entry to the log file."""
    with open(_LOG_FILE, "a") as f:
        f.write(json.dumps({**entry, "timestamp": datetime.now().isoformat()}) + "\n")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def regenerate(
    max_urls: Optional[int] = None,
    resume: bool = False,
    dry_run: bool = False,
) -> Optional[Path]:
    """Regenerate the AI dataset with the optimized prompt."""

    # Load source content from ORIGINAL backup excerpts
    all_sources = load_source_excerpts(_ORIGINAL_BACKUP)
    sources = all_sources[:max_urls] if max_urls else all_sources

    log.info("=" * 70)
    log.info("AI DATASET REGENERATION — Autoresearch Exp5 Optimized Prompt")
    log.info("=" * 70)
    log.info("  Source backup: %s", _ORIGINAL_BACKUP)
    log.info("  Output:        %s", _OUTPUT_FILE)
    log.info("  Model:         %s", GEN_MODEL)
    log.info("  Temperature:   %s", GEN_TEMPERATURE)
    log.info("  Prompt:        Two-pass fact extraction (source-preserving)")
    log.info("  QA/chunk:      %d", QA_PER_CHUNK)
    log.info("  Chunk size:    %d chars", CHUNK_SIZE)
    log.info("  Dedup thresh:  %.2f", DEDUP_THRESHOLD)
    log.info("  Sources:       %d (from original dataset excerpts)", len(sources))
    log.info("  Resume:        %s", resume)
    log.info("  Dry run:       %s", dry_run)
    log.info("")

    total_source_chars = 0
    total_chunks_est = 0
    for i, src in enumerate(sources, 1):
        n_chunks = len(chunk_content(src["content"]))
        total_chunks_est += n_chunks
        total_source_chars += len(src["content"])
        log.info("  [%d] %s: %d excerpts, %s chars, ~%d chunks (from %d original pairs)",
                 i, src["source"], src["n_excerpts"],
                 f"{len(src['content']):,}", n_chunks, src["n_original_pairs"])

    log.info("")
    log.info("  TOTAL: %s chars source, ~%d chunks, ~%d pairs before dedup",
             f"{total_source_chars:,}", total_chunks_est, total_chunks_est * QA_PER_CHUNK)

    if dry_run:
        log.info("  Exiting dry run.")
        return None

    # Back up current output file
    if _OUTPUT_FILE.exists():
        _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = _BACKUP_DIR / f"ai_generated_qa_pre_regen_{ts}.jsonl"
        shutil.copy2(_OUTPUT_FILE, backup_path)
        log.info("  Backed up current file to: %s", backup_path)

    # Log run start
    append_log({
        "event": "run_start",
        "config": {
            "model": GEN_MODEL, "temperature": GEN_TEMPERATURE,
            "chunk_size": CHUNK_SIZE, "qa_per_chunk": QA_PER_CHUNK,
            "dedup_threshold": DEDUP_THRESHOLD, "n_sources": len(sources),
            "total_chunks_est": total_chunks_est, "resume": resume,
        },
    })

    client = OpenAI(api_key=_OPENAI_API_KEY)
    all_pairs: list[dict] = []
    stats = {"processed": 0, "cached": 0, "resumed_partial": 0,
             "total_chunks": 0, "total_api_calls": 0, "errors": 0}
    run_start = time.time()

    for i, src in enumerate(sources, 1):
        url = src["url"]
        log.info("")
        log.info("[%d/%d] %s", i, len(sources), src["source"])
        log.info("  URL: %s", url)
        log.info("  Reconstructed: %s chars from %d unique excerpts",
                 f"{len(src['content']):,}", src["n_excerpts"])

        content = src["content"]
        if len(content) < 30:
            log.warning("  SKIP — insufficient source content (%d chars)", len(content))
            continue

        chunks = chunk_content(content)
        n_chunks = len(chunks)
        log.info("  Split into %d chunks", n_chunks)
        stats["total_chunks"] += n_chunks

        # Resume: check for existing checkpoint
        url_pairs: list[dict] = []
        start_chunk = 0

        if resume:
            checkpoint = load_url_checkpoint(url)
            if checkpoint is not None:
                completed = checkpoint["completed_chunks"]
                if completed >= n_chunks:
                    # Fully completed
                    url_pairs = checkpoint["pairs"]
                    log.info("  CACHED — %d pairs (all %d chunks done)", len(url_pairs), n_chunks)
                    all_pairs.extend(url_pairs)
                    stats["cached"] += 1
                    continue
                else:
                    # Partially completed — resume from where we left off
                    url_pairs = checkpoint["pairs"]
                    start_chunk = completed
                    log.info("  RESUMING from chunk %d/%d (%d pairs so far)",
                             start_chunk + 1, n_chunks, len(url_pairs))
                    stats["resumed_partial"] += 1

        # Generate QA pairs per chunk
        for j in range(start_chunk, n_chunks):
            chunk = chunks[j]
            pairs = generate_qa_pairs(client, chunk, src, j + 1, n_chunks)
            url_pairs.extend(pairs)
            stats["total_api_calls"] += 1

            if not pairs:
                stats["errors"] += 1

            # Save checkpoint after each chunk
            save_url_checkpoint(url, url_pairs, j + 1, n_chunks)

            time.sleep(SLEEP_BETWEEN_CHUNKS)

        all_pairs.extend(url_pairs)
        stats["processed"] += 1
        log.info("  Total for URL: %d pairs", len(url_pairs))

        # Log per-URL completion
        append_log({
            "event": "url_complete",
            "url": url,
            "source": src["source"],
            "n_chunks": n_chunks,
            "n_pairs": len(url_pairs),
        })

        if i < len(sources):
            time.sleep(SLEEP_BETWEEN_URLS)

    # Deduplicate
    before = len(all_pairs)
    all_pairs = deduplicate(all_pairs)
    after = len(all_pairs)
    log.info("")
    log.info("Deduplication: %d → %d pairs (%d removed, %.1f%%)",
             before, after, before - after,
             100 * (before - after) / before if before else 0)

    # Assign sequential IDs
    for idx, pair in enumerate(all_pairs, 1):
        pair["id"] = f"ai_{idx:05d}"

    # Save
    _OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for p in all_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # Also copy to code/data/ for RAGAS evaluation
    ragas_copy = _CODE_ROOT / "data" / "ai_generated" / "ai_generated_qa.jsonl"
    ragas_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_OUTPUT_FILE, ragas_copy)

    # Summary
    elapsed = time.time() - run_start
    avg_words = (
        sum(len(p["answer"].split()) for p in all_pairs) / len(all_pairs)
        if all_pairs else 0
    )

    log.info("")
    log.info("=" * 70)
    log.info("REGENERATION COMPLETE")
    log.info("=" * 70)
    log.info("  Time elapsed:    %.1f min", elapsed / 60)
    log.info("  URLs processed:  %d", stats["processed"])
    log.info("  URLs cached:     %d", stats["cached"])
    log.info("  URLs resumed:    %d", stats["resumed_partial"])
    log.info("  Total chunks:    %d", stats["total_chunks"])
    log.info("  API calls:       %d", stats["total_api_calls"])
    log.info("  Errors:          %d", stats["errors"])
    log.info("  Total QA pairs:  %d (before dedup: %d)", after, before)
    log.info("  Avg answer len:  %.1f words", avg_words)
    log.info("  Saved to:        %s", _OUTPUT_FILE)
    log.info("  RAGAS copy:      %s", ragas_copy)
    log.info("")
    log.info("Next step: run the full RAGAS evaluation:")
    log.info("  cd %s && python3 scripts/ragas_evaluation.py --concise", _CODE_ROOT)

    # Log run completion
    append_log({
        "event": "run_complete",
        "elapsed_min": round(elapsed / 60, 1),
        "stats": stats,
        "total_pairs_before_dedup": before,
        "total_pairs_after_dedup": after,
        "avg_answer_words": round(avg_words, 1),
    })

    return _OUTPUT_FILE


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--max-urls", type=int, default=None,
        help="Process only the first N URLs (for testing)",
    )
    parser.add_argument(
        "--resume", action="store_true", default=False,
        help="Resume from per-chunk checkpoints (skip completed chunks)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Show plan without making API calls",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    regenerate(
        max_urls=args.max_urls,
        resume=args.resume,
        dry_run=args.dry_run,
    )
