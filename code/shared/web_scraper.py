"""Web scraper utilities for WebRAG evaluation.

Provides sequential URL fetching using requests + BeautifulSoup with
no acceleration libraries, matching the approach described in Ibrahim's
WebRAG methodology. Intended for latency benchmarking where realistic
cold-scrape timing is required.

Source URLs are the same 5 authoritative smoking cessation sources
used in proper_web_rag_comparison.py.
"""

import time
from typing import Optional

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Source URLs — 5 authoritative smoking cessation sources
# ---------------------------------------------------------------------------

SOURCE_URLS = [
    "https://smokefree.gov/challenges-when-quitting/withdrawal/managing-nicotine-withdrawal",
    "https://www.cdc.gov/tobacco/campaign/tips/quit-smoking/7-common-withdrawal-symptoms/index.html",
    "https://www.mayoclinic.org/diseases-conditions/nicotine-dependence/diagnosis-treatment/drc-20351590",
    "https://www.cancer.org/cancer/risk-prevention/tobacco/guide-quitting-smoking/nicotine-replacement-therapy.html",
    "https://www.lung.org/quit-smoking/i-want-to-quit/what-to-expect",
]

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_MAX_CHARS_PER_URL = 3000


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fetch_url(url: str, timeout: int = 15) -> dict:
    """Fetch and clean content from a single URL.

    Strips script, style, nav, footer, and header elements before
    extracting text. Truncates to 3000 characters to keep token usage
    manageable.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds (default 15).

    Returns:
        Dict with keys:
            url (str): The fetched URL.
            content (str | None): Cleaned text, or None on failure.
            fetch_time_s (float): Wall-clock fetch time in seconds.
            success (bool): True if content was retrieved.
            error (str | None): Error message on failure, else None.
    """
    start = time.perf_counter()
    try:
        response = requests.get(url, headers=_DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove boilerplate elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        raw_text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        if len(clean_text) > _MAX_CHARS_PER_URL:
            clean_text = clean_text[:_MAX_CHARS_PER_URL] + "..."

        elapsed = time.perf_counter() - start
        return {
            "url": url,
            "content": clean_text,
            "fetch_time_s": round(elapsed, 4),
            "success": True,
            "error": None,
        }

    except Exception as exc:
        elapsed = time.perf_counter() - start
        return {
            "url": url,
            "content": None,
            "fetch_time_s": round(elapsed, 4),
            "success": False,
            "error": str(exc),
        }


def fetch_all_urls(
    urls: Optional[list[str]] = None,
    sleep: float = 1.0,
) -> tuple[list[dict], float]:
    """Fetch all URLs sequentially with a polite sleep between requests.

    Args:
        urls: List of URLs to fetch. Defaults to SOURCE_URLS if None.
        sleep: Seconds to sleep between requests (default 1.0).

    Returns:
        Tuple of (results, total_time_s) where:
            results: List of fetch_url() dicts, one per URL.
            total_time_s: Wall-clock time for the entire batch (float).
    """
    if urls is None:
        urls = SOURCE_URLS

    batch_start = time.perf_counter()
    results = []

    for i, url in enumerate(urls):
        result = fetch_url(url)
        results.append(result)
        status = "OK" if result["success"] else "FAIL"
        print(
            f"  [{i + 1}/{len(urls)}] {status} ({result['fetch_time_s']:.2f}s) {url}"
        )
        if i < len(urls) - 1:
            time.sleep(sleep)

    total_time = time.perf_counter() - batch_start
    successes = sum(1 for r in results if r["success"])
    print(f"  Fetched {successes}/{len(urls)} URLs in {total_time:.2f}s")
    return results, round(total_time, 4)


def build_web_context(
    fetched: list[dict],
    max_chars: int = 12000,
) -> str:
    """Concatenate successful fetch results into a single context string.

    Joins content from each successful URL with a separator. Truncates
    the total combined context to max_chars to avoid token overflow.

    Args:
        fetched: List of fetch_url() result dicts.
        max_chars: Maximum total characters in the combined context.

    Returns:
        Single string combining all successful web content.
    """
    parts = []
    for r in fetched:
        if r["success"] and r["content"]:
            source_label = r["url"].split("/")[2]  # domain only for readability
            parts.append(f"[Source: {source_label}]\n{r['content']}")

    combined = "\n\n".join(parts)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "..."
    return combined
