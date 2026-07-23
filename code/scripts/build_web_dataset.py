#!/usr/bin/env python3
"""Build a web-source corpus and Q&A dataset from authority sources.

Pipeline:
  1. Recover URLs from the existing web Q&A dataset when the original list is absent
  2. Fetch and persist cleaned primary-page content (up to 10,000 chars per page)
  3. Use GPT-4o-mini to generate 8 specific, detailed Q&A pairs per page
  4. Save per-URL checkpoints to avoid re-scraping on restart
  5. Merge, deduplicate, and save to data/web_scraped_qa.jsonl

Usage:
  python3 scripts/build_web_dataset.py               # full run
  python3 scripts/build_web_dataset.py --max-urls 5  # test with 5 URLs
  python3 scripts/build_web_dataset.py --resume       # skip already-done URLs
  python3 scripts/build_web_dataset.py --source-only  # rebuild raw source corpus only
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
_PROJECT_ROOT = _ROOT.parent
_URLS_FILE = _ROOT / "data" / "source_web_links.json"
_CHECKPOINT_DIR = _ROOT / "data" / "web_scraped_dataset" / "checkpoints"
_OUTPUT_FILE = _ROOT / "data" / "web_scraped_qa.jsonl"
_EXISTING_WEB_QA_FILE = _PROJECT_ROOT / "datasets" / "eval-rag" / "web_scraped_qa.jsonl"
_RAW_SOURCE_OUTPUT_FILE = _PROJECT_ROOT / "datasets" / "eval-rag" / "web_source_documents.jsonl"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_MAX_CHARS = 10_000          # characters per page kept for GPT context
_QA_PER_PAGE = 8             # Q&A pairs to generate per page
_SLEEP_BETWEEN_URLS = 2.5    # seconds between HTTP requests (polite)
_REQUEST_TIMEOUT = 15        # seconds
_BROWSER_TIMEOUT_MS = 30_000 # browser fallback navigation timeout

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
    """Load source URLs, recovering them from existing QA data if necessary."""
    if _URLS_FILE.exists():
        data = json.loads(_URLS_FILE.read_text())
        urls = data.get("urls", data) if isinstance(data, dict) else data
    elif _EXISTING_WEB_QA_FILE.exists():
        urls = []
        seen: set[str] = set()
        with _EXISTING_WEB_QA_FILE.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                url = record.get("url")
                if isinstance(url, str) and url and url not in seen:
                    seen.add(url)
                    urls.append(url)
        if not urls:
            raise ValueError(f"No URLs found in {_EXISTING_WEB_QA_FILE}")
        print(f"  Recovered {len(urls)} URLs from {_EXISTING_WEB_QA_FILE}")
    else:
        raise FileNotFoundError(
            f"Neither {_URLS_FILE} nor {_EXISTING_WEB_QA_FILE} is available"
        )
    # Drop PDFs — can't extract clean text from binary PDF with requests+BS4
    html_urls = [u for u in urls if not u.lower().endswith(".pdf")]
    dropped = len(urls) - len(html_urls)
    if dropped:
        print(f"  Skipped {dropped} PDF URLs (not scrape-able with HTML parser)")
    if max_urls:
        html_urls = html_urls[:max_urls]
    return html_urls


def _load_source_documents() -> dict[str, dict]:
    """Return prior source records indexed by URL, if a corpus already exists."""
    if not _RAW_SOURCE_OUTPUT_FILE.exists():
        return {}
    records: dict[str, dict] = {}
    with _RAW_SOURCE_OUTPUT_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if isinstance(record.get("url"), str):
                    # Corpus format before browser fallback did not record this;
                    # those records were necessarily fetched by requests.
                    record.setdefault("fetch_method", "requests")
                    records[record["url"]] = record
    return records


def _write_source_documents(records: list[dict]) -> Path:
    """Persist raw source records deterministically for reproducible generation."""
    _RAW_SOURCE_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _RAW_SOURCE_OUTPUT_FILE.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return _RAW_SOURCE_OUTPUT_FILE


def build_source_corpus(max_urls: int | None = None, resume: bool = False) -> Path:
    """Fetch authority pages and save the raw generation corpus with provenance.

    This deliberately makes no model calls.  Each record contains only the
    cleaned primary-source text and metadata needed to trace generated content
    back to a public URL.
    """
    urls = _load_urls(max_urls)
    prior_records = _load_source_documents() if resume else {}
    records: list[dict] = []
    fetched = cached = failed = 0

    for index, url in enumerate(urls, 1):
        print(f"[{index}/{len(urls)}] {url}")
        cached_record = prior_records.get(url)
        if cached_record and cached_record.get("content"):
            records.append(cached_record)
            cached += 1
            continue

        fetch = _fetch_page(url)
        if not fetch["success"]:
            print(f"  FETCH FAIL — {fetch['error']}")
            failed += 1
        else:
            content = fetch["content"]
            records.append({
                "url": url,
                "content": content,
                "char_count": len(content),
                "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "fetch_method": fetch["fetch_method"],
            })
            fetched += 1
            print(f"  Saved {len(content):,} chars")

        if index < len(urls):
            time.sleep(_SLEEP_BETWEEN_URLS)

    output = _write_source_documents(records)
    print(f"Done. fetched={fetched} cached={cached} failed={failed}")
    print(f"Source pages: {len(records)}")
    print(f"Saved to: {output}")
    return output


# ---------------------------------------------------------------------------
# Step 2: Content fetching (higher limit than shared/web_scraper.py)
# ---------------------------------------------------------------------------

def _clean_page_content(html: str) -> str:
    """Remove boilerplate from HTML and retain the bounded article text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "noscript"]):
        tag.decompose()
    raw = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in raw.splitlines() if len(line.strip()) > 30]
    return "\n".join(lines)[:_MAX_CHARS]


def _fetch_page_in_browser(url: str) -> dict:
    """Render a public page in stealth Chromium after a plain HTTP failure."""
    try:
        from cloakbrowser import launch_context

        context = launch_context(
            headless=True,
            locale="en-US",
            timezone="America/Chicago",
        )
        try:
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=_BROWSER_TIMEOUT_MS)
            page.wait_for_timeout(1_000)
            if response is not None and response.status >= 400:
                raise requests.HTTPError(f"Browser received HTTP {response.status}")
            content = _clean_page_content(page.content())
        finally:
            context.close()

        if len(content) < 200:
            return {"url": url, "content": None, "success": False,
                    "error": "Browser-rendered content too short after cleaning"}
        return {"url": url, "content": content, "success": True, "error": None,
                "fetch_method": "cloakbrowser"}
    except Exception as exc:
        return {"url": url, "content": None, "success": False,
                "error": f"browser fallback failed: {exc}"}


def _fetch_page(url: str) -> dict:
    """Fetch and clean a public page, with browser rendering as a fallback."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        content = _clean_page_content(resp.text)
        if len(content) < 200:
            return {"url": url, "content": None, "success": False,
                    "error": "Content too short after cleaning"}
        return {"url": url, "content": content, "success": True, "error": None,
                "fetch_method": "requests"}
    except Exception as exc:
        browser_result = _fetch_page_in_browser(url)
        if browser_result["success"]:
            return browser_result
        return {"url": url, "content": None, "success": False,
                "error": f"requests failed: {exc}; {browser_result['error']}"}


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
    p.add_argument("--source-only", action="store_true",
                   help="Fetch and persist raw source pages without generating Q&A")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.source_only:
        build_source_corpus(max_urls=args.max_urls, resume=args.resume)
    else:
        build(max_urls=args.max_urls, resume=args.resume)
