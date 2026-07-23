#!/usr/bin/env python3
"""Generate a cited QA knowledge base from persisted primary web pages.

This is the non-circular Phase 1 generator. It consumes
``datasets/eval-rag/web_source_documents.jsonl`` (raw authority-page text),
never the older model-generated web QA data.

Usage:
  python3 code/scripts/generate_web_source_kb.py --dry-run
  python3 code/scripts/generate_web_source_kb.py --max-pages 1
  python3 code/scripts/generate_web_source_kb.py --resume
"""

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

_CODE_ROOT = Path(__file__).parent.parent
_PROJECT_ROOT = _CODE_ROOT.parent
_ENV_PATH = _CODE_ROOT / ".env"
if not _ENV_PATH.exists():
    _ENV_PATH = _PROJECT_ROOT / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

_SOURCE_CORPUS = _PROJECT_ROOT / "datasets" / "eval-rag" / "web_source_documents.jsonl"
_OUTPUT_FILE = _PROJECT_ROOT / "datasets" / "web-source" / "web_source_generated_qa.jsonl"
_CHECKPOINT_DIR = _PROJECT_ROOT / "datasets" / "web-source" / "generation_checkpoints_grounded_v2"

MODEL = "gpt-4o-mini"
TEMPERATURE = 0.0
CHUNK_SIZE = 1_500
CHUNK_OVERLAP = 150
QA_PER_CHUNK = 8
MAX_TOKENS = 2_500
SLEEP_BETWEEN_CHUNKS = 0.35
VERIFIER_MODEL = "gpt-4o-mini"

# exp_0020's three-pass, fact-forward register-translation mechanism.
SYSTEM_PROMPT = """You are a smoking cessation counseling expert generating training data for a medical AI chatbot used in a healthcare setting.

TASK: From the provided source content, generate exactly {n} question-answer pairs using a THREE-PASS approach.

CRITICAL CONSTRAINT — HEALTHCARE SAFETY:
This is a health domain. Do NOT add, infer, or invent FACTS beyond what the source explicitly states. Numbers, medication names, dosages, timeframes, and percentages are LOCKED — they must appear exactly as written in the source.

PASS 1 — FACT EXTRACTION: identify the {n} most important distinct facts, statistics, medication names, techniques, or clinical findings directly stated in the source.

PASS 2 — GROUNDED DRAFT (internal scaffolding, NOT in output): for each fact, mentally write one plain clinical sentence that preserves every number, dose, timeframe, and percentage verbatim.

PASS 3 — REGISTER TRANSLATION: translate each grounded draft into a real text-message exchange between someone trying to quit and their chatbot counselor. Clinical content is fixed; only the register changes.
- Question: a real person would text about their body, life, or worry, using first or second person. Never academic or textbook phrasing.
- Answer: 2–3 short sentences addressing the person directly. OPEN with the concrete grounded fact; warmth or reassurance may only be a brief trailing clause. Preserve every number, medication name, dosage, timeframe, and percentage exactly.

RULES:
1. Every claim must trace to a specific sentence in the source; translate wording, never content.
2. Tone must not introduce facts, reassurance, or claims unsupported by the source.
3. Cover {n} different topics; do not repeat themes.
4. No disclaimers, hedging, or generic advice unless the source says it.
5. If the source lacks {n} distinct facts, generate fewer pairs.

EVIDENCE REQUIREMENT: For every pair, copy one or more exact source sentences into an "evidence" field. The evidence must support EVERY factual claim in the answer; do not paraphrase it. If no such evidence exists, omit the pair.

Return a JSON object with key "qa_pairs" containing an array of objects, each with "question", "answer", and "evidence" strings only."""

VERIFIER_PROMPT = """You are a strict medical-content grounding verifier.

For each candidate QA pair, approve it ONLY if every factual or clinical claim in its answer is directly supported by the provided source text AND the exact evidence string. Reject it for any unsupported inference, invented reassurance, altered number/dose/timeframe, or evidence that does not support every claim.

Return only JSON in this form: {"approved_indices": [0, 2]}. Omit any index that is not fully supported. If uncertain, reject it."""


def load_sources(max_pages: int | None) -> list[dict]:
    if not _SOURCE_CORPUS.exists():
        raise FileNotFoundError(f"Source corpus missing: {_SOURCE_CORPUS}")
    sources = [
        json.loads(line) for line in _SOURCE_CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    valid = [source for source in sources if source.get("url") and source.get("content")]
    if not valid:
        raise ValueError(f"No usable source documents in {_SOURCE_CORPUS}")
    return valid[:max_pages] if max_pages else valid


def chunk_content(content: str) -> list[str]:
    """Split a page into overlapping, paragraph-aware generation chunks."""
    chunks: list[str] = []
    start = 0
    while start < len(content):
        end = min(start + CHUNK_SIZE, len(content))
        if end < len(content):
            paragraph_end = content.rfind("\n", start + CHUNK_SIZE // 2, end)
            if paragraph_end > start:
                end = paragraph_end
        chunk = content[start:end].strip()
        if len(chunk) >= 200:
            chunks.append(chunk)
        if end >= len(content):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def checkpoint_path(url: str) -> Path:
    return _CHECKPOINT_DIR / f"{hashlib.sha256(url.encode()).hexdigest()[:16]}.json"


def load_checkpoint(url: str) -> dict | None:
    path = checkpoint_path(url)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def save_checkpoint(url: str, pairs: list[dict], completed_chunks: int, total_chunks: int) -> None:
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_path(url).write_text(json.dumps({
        "url": url,
        "pairs": pairs,
        "completed_chunks": completed_chunks,
        "total_chunks": total_chunks,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_pairs(client: OpenAI, content: str, source: dict, chunk_number: int, total_chunks: int) -> list[dict]:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(n=QA_PER_CHUNK)},
            {"role": "user", "content": f"Source URL: {source['url']}\n\nSource content:\n\n{content}"},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        response_format={"type": "json_object"},
    )
    raw = json.loads(response.choices[0].message.content)
    candidates = raw if isinstance(raw, list) else raw.get("qa_pairs", raw.get("pairs", []))
    now = datetime.now(timezone.utc).isoformat()
    pairs = []
    for candidate in candidates:
        question = str(candidate.get("question", "")).strip()
        answer = str(candidate.get("answer", "")).strip()
        evidence = str(candidate.get("evidence", "")).strip()
        # This deterministic gate prevents a generated citation from pointing to
        # text outside the source chunk. It does not judge entailment by itself,
        # but makes every retained pair independently auditable.
        normalized_evidence = " ".join(evidence.split())
        normalized_content = " ".join(content.split())
        if (
            len(question) > 10
            and len(answer) > 20
            and len(normalized_evidence) >= 20
            and normalized_evidence in normalized_content
        ):
            pairs.append({
                "question": question,
                "answer": answer,
                "evidence": evidence,
                "source_url": source["url"],
                "source_content_sha256": source["content_sha256"],
                "source_chunk_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "source_fetch_method": source.get("fetch_method", "unknown"),
                "chunk_number": chunk_number,
                "total_chunks": total_chunks,
                "generation_method": "exp_0020_three_pass_register_translation",
                "generation_model": MODEL,
                "created_at": now,
            })
    print(f"    chunk {chunk_number}/{total_chunks}: {len(pairs)} grounded pairs")
    return pairs


def verify_pairs(client: OpenAI, content: str, pairs: list[dict]) -> list[dict]:
    """Fail closed unless an independent pass approves every answer claim."""
    if not pairs:
        return []
    candidates = [
        {"index": index, "question": pair["question"], "answer": pair["answer"], "evidence": pair["evidence"]}
        for index, pair in enumerate(pairs)
    ]
    response = client.chat.completions.create(
        model=VERIFIER_MODEL,
        messages=[
            {"role": "system", "content": VERIFIER_PROMPT},
            {"role": "user", "content": "SOURCE TEXT:\n" + content + "\n\nCANDIDATES:\n" + json.dumps(candidates)},
        ],
        temperature=0.0,
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    raw = json.loads(response.choices[0].message.content)
    approved = {
        index for index in raw.get("approved_indices", [])
        if isinstance(index, int) and 0 <= index < len(pairs)
    }
    verified = []
    for index, pair in enumerate(pairs):
        if index in approved:
            pair["grounding_verifier"] = "approved"
            pair["grounding_verifier_model"] = VERIFIER_MODEL
            verified.append(pair)
    print(f"      verifier: approved {len(verified)}/{len(pairs)}")
    return verified


def word_overlap(first: str, second: str) -> float:
    first_words, second_words = set(first.lower().split()), set(second.lower().split())
    return len(first_words & second_words) / len(first_words) if first_words else 0.0


def deduplicate(pairs: list[dict], threshold: float = 0.9) -> list[dict]:
    kept: list[dict] = []
    for pair in pairs:
        if not any(word_overlap(pair["question"], existing["question"]) >= threshold for existing in kept):
            kept.append(pair)
    return kept


def generate(max_pages: int | None, resume: bool, dry_run: bool) -> Path | None:
    sources = load_sources(max_pages)
    planned_chunks = sum(len(chunk_content(source["content"])) for source in sources)
    print(f"Sources: {len(sources)} | chunks: {planned_chunks} | planned pairs: ≤{planned_chunks * QA_PER_CHUNK}")
    print(f"Output: {_OUTPUT_FILE}")
    if dry_run:
        return None

    client = OpenAI()
    generated: list[dict] = []
    for page_index, source in enumerate(sources, 1):
        chunks = chunk_content(source["content"])
        checkpoint = load_checkpoint(source["url"]) if resume else None
        pairs = checkpoint["pairs"] if checkpoint else []
        start_chunk = checkpoint["completed_chunks"] if checkpoint else 0
        print(f"[{page_index}/{len(sources)}] {source['url']} ({len(chunks)} chunks; resume={start_chunk})")
        for chunk_index in range(start_chunk, len(chunks)):
            try:
                candidates = generate_pairs(client, chunks[chunk_index], source, chunk_index + 1, len(chunks))
                pairs.extend(verify_pairs(client, chunks[chunk_index], candidates))
            except Exception as exc:
                print(f"    chunk {chunk_index + 1}/{len(chunks)} failed: {exc}")
            save_checkpoint(source["url"], pairs, chunk_index + 1, len(chunks))
            time.sleep(SLEEP_BETWEEN_CHUNKS)
        generated.extend(pairs)

    before = len(generated)
    generated = deduplicate(generated)
    for index, pair in enumerate(generated, 1):
        pair["id"] = f"web_source_{index:05d}"
    _OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _OUTPUT_FILE.open("w", encoding="utf-8") as handle:
        for pair in generated:
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"Saved {len(generated)} pairs ({before - len(generated)} duplicates removed) to {_OUTPUT_FILE}")
    return _OUTPUT_FILE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate(args.max_pages, args.resume, args.dry_run)
