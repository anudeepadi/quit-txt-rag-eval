#!/usr/bin/env python3
"""Build a web-scraped Q&A dataset from authoritative smoking cessation sources.

Pipeline:
  1. Load URLs from data/source_web_links.json (skip PDFs)
  2. Fetch full page content (up to 10,000 chars per page)
  3. Use GPT-4o-mini to generate 8 specific, detailed Q&A pairs per page
  4. Save per-URL checkpoints to avoid re-scraping on restart
  5. Merge, deduplicate, and save to data/web_scraped_qa.jsonl

Usage:
  python3 scripts/build_web_dataset.py               # full run
  python3 scripts/build_web_dataset.py --max-urls 5  # test with 5 URLs
  python3 scripts/build_web_dataset.py --resume       # skip already-done URLs
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent
_URLS_FILE = _ROOT / "data" / "source_web_links.json"
_CHECKPOINT_DIR = _ROOT / "data" / "web_scraped_dataset" / "checkpoints"
_OUTPUT_FILE = _ROOT / "data" / "web_scraped_qa.jsonl"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_MAX_CHARS = 10_000          # characters per page kept for GPT context
_QA_PER_PAGE = 8             # Q&A pairs to generate per page
_SLEEP_BETWEEN_URLS = 2.5    # seconds between HTTP requests (polite)
_REQUEST_TIMEOUT = 15        # seconds

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# GPT prompt — explicit about specificity to avoid the vague-answer failure
# mode seen in the existing AI-generated dataset
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a smoking cessation counseling expert generating \
training data for a medical AI chatbot.

From the provided web content, generate exactly {n} question-answer pairs.

STRICT RULES:
1. Questions must be phrased as a patient would naturally ask — conversational,
   first-person, the kind of thing someone would type into a chat app.
2. Answers must be SPECIFIC: include actual facts, named medications, dosages,
   timeframes, percentages, techniques, or step-by-step guidance drawn directly
   from the source text. Do NOT write generic advice.
3. Each answer must be 3-5 sentences and contain enough clinical detail that a
   clinician could verify it against the source.
4. Cover DIFFERENT topics/aspects across the {n} pairs — do not repeat the
   same theme with different wording.
5. Answers must be grounded ONLY in the provided content — add nothing from
   outside the source text.

Return a JSON object with key "qa_pairs" containing an array of {n} objects,
each with "question" (string) and "answer" (string) fields only."""


# ---------------------------------------------------------------------------
# Step 1: URL loading and filtering
# ---------------------------------------------------------------------------

def _load_urls(max_urls: int | None = None) -> list[str]:
    data = json.loads(_URLS_FILE.read_text())
    urls = data.get("urls", data) if isinstance(data, dict) else data
    # Drop PDFs — can't extract clean text from binary PDF with requests+BS4
    html_urls = [u for u in urls if not u.lower().endswith(".pdf")]
    dropped = len(urls) - len(html_urls)
    if dropped:
        print(f"  Skipped {dropped} PDF URLs (not scrape-able with HTML parser)")
    if max_urls:
        html_urls = html_urls[:max_urls]
    return html_urls


# ---------------------------------------------------------------------------
# Step 2: Content fetching (higher limit than shared/web_scraper.py)
# ---------------------------------------------------------------------------

def _fetch_page(url: str) -> dict:
    """Fetch and clean HTML content from a single URL.

    Returns a dict with keys: url, content, success, error.
    Content is stripped of boilerplate and truncated to _MAX_CHARS.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "form", "noscript"]):
            tag.decompose()

        raw = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 30]
        content = "\n".join(lines)

        if len(content) > _MAX_CHARS:
            content = content[:_MAX_CHARS]

        if len(content) < 200:
            return {"url": url, "content": None, "success": False,
                    "error": "Content too short after cleaning"}

        return {"url": url, "content": content, "success": True, "error": None}

    except Exception as exc:
        return {"url": url, "content": None, "success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Step 3: Q&A generation via GPT-4o-mini
# ---------------------------------------------------------------------------

def _generate_qa(client: OpenAI, content: str, url: str) -> list[dict]:
    """Call GPT-4o-mini to produce Q&A pairs from page content."""
    domain = url.split("/")[2]
    user_msg = f"Source URL: {url}\n\nContent:\n{content}"

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": _SYSTEM_PROMPT.format(n=_QA_PER_PAGE)},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=2500,
        response_format={"type": "json_object"},
    )

    raw = json.loads(resp.choices[0].message.content)
    # GPT sometimes nests under different keys
    pairs = (raw if isinstance(raw, list)
             else raw.get("qa_pairs", raw.get("pairs", raw.get("questions", []))))

    result = []
    for p in pairs:
        q = str(p.get("question", "")).strip()
        a = str(p.get("answer", "")).strip()
        if len(q) > 10 and len(a) > 20:
            result.append({"question": q, "answer": a,
                           "source": domain, "url": url})
    return result


# ---------------------------------------------------------------------------
# Checkpointing helpers
# ---------------------------------------------------------------------------

def _url_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _checkpoint_path(url: str) -> Path:
    return _CHECKPOINT_DIR / f"{_url_key(url)}.json"


def _load_checkpoint(url: str) -> list[dict] | None:
    p = _checkpoint_path(url)
    if p.exists():
        data = json.loads(p.read_text())
        # Checkpoint is saved as {"url": ..., "pairs": [...]}
        return data.get("pairs", data) if isinstance(data, dict) else data
    return None


def _save_checkpoint(url: str, pairs: list[dict]) -> None:
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    _checkpoint_path(url).write_text(
        json.dumps({"url": url, "pairs": pairs}, indent=2)
    )


# ---------------------------------------------------------------------------
# Step 5: Deduplication
# ---------------------------------------------------------------------------

def _word_overlap(a: str, b: str) -> float:
    """Fraction of words in `a` that also appear in `b` (case-insensitive)."""
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa:
        return 0.0
    return len(wa & wb) / len(wa)


def _deduplicate(pairs: list[dict], threshold: float = 0.75) -> list[dict]:
    """Remove near-duplicate questions by word-overlap similarity."""
    kept: list[dict] = []
    kept_questions: list[str] = []
    for p in pairs:
        q = p["question"]
        is_dup = any(_word_overlap(q, kq) >= threshold for kq in kept_questions)
        if not is_dup:
            kept.append(p)
            kept_questions.append(q)
    return kept


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def build(max_urls: int | None = None, resume: bool = False) -> Path:
    client = OpenAI()
    urls = _load_urls(max_urls)
    print(f"\nURLs to process: {len(urls)}")

    all_pairs: list[dict] = []
    processed = skipped = failed = 0

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] {url}")

        # Resume: reuse checkpoint if it exists
        if resume:
            cached = _load_checkpoint(url)
            if cached is not None:
                print(f"  CACHED — {len(cached)} pairs")
                all_pairs.extend(cached)
                skipped += 1
                continue

        # Fetch page
        fetch = _fetch_page(url)
        if not fetch["success"]:
            print(f"  FETCH FAIL — {fetch['error']}")
            failed += 1
            time.sleep(_SLEEP_BETWEEN_URLS)
            continue

        content_len = len(fetch["content"])
        print(f"  Fetched {content_len:,} chars")

        # Generate Q&A
        try:
            pairs = _generate_qa(client, fetch["content"], url)
            print(f"  Generated {len(pairs)} Q&A pairs")
        except Exception as exc:
            print(f"  GPT FAIL — {exc}")
            failed += 1
            time.sleep(_SLEEP_BETWEEN_URLS)
            continue

        _save_checkpoint(url, pairs)
        all_pairs.extend(pairs)
        processed += 1

        # Polite delay between requests
        if i < len(urls):
            time.sleep(_SLEEP_BETWEEN_URLS)

    # Deduplicate
    before = len(all_pairs)
    all_pairs = _deduplicate(all_pairs)
    after = len(all_pairs)
    print(f"\nDeduplication: {before} → {after} pairs "
          f"({before - after} removed)")

    # Save final JSONL
    _OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for p in all_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"\n{'='*60}")
    print(f"Done.  processed={processed}  cached={skipped}  failed={failed}")
    print(f"Total Q&A pairs: {after}")
    print(f"Saved to: {_OUTPUT_FILE}")

    return _OUTPUT_FILE


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--max-urls", type=int, default=None,
                   help="Process only the first N URLs (useful for testing)")
    p.add_argument("--resume", action="store_true",
                   help="Skip URLs that already have a checkpoint file")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    build(max_urls=args.max_urls, resume=args.resume)
