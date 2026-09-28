"""Turn the student's pasted box (text or a URL) into posting text.

One box, two possible contents (PRD §5.1). URL fetching is a convenience,
not a promise: most job boards either block scraping outright or serve a
JavaScript shell with no readable text in the initial response, so a failed
or too-short fetch falls back to one friendly line rather than an error.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

URL_PATTERN = re.compile(r"^https?://\S+$")

MIN_FETCHED_CHARS = 400
MAX_POSTING_CHARS = 15_000

FETCH_FALLBACK_MESSAGE = "That site didn't let me read the posting. Paste the text instead."

_USER_AGENT = "Mozilla/5.0 (compatible; SenSymJobExplainer/1.0)"


@dataclass
class IngestResult:
    text: str = ""
    truncated: bool = False
    error: str | None = None


def is_url(raw_input: str) -> bool:
    return bool(URL_PATTERN.match(raw_input.strip()))


def ingest(raw_input: str) -> IngestResult:
    """Detect text vs. URL, fetch if needed, normalize, and cap the length."""
    raw_input = (raw_input or "").strip()
    if not raw_input:
        return IngestResult(error="Paste a job posting, or a link to one, first.")

    if is_url(raw_input):
        try:
            text = _fetch_and_clean(raw_input)
        except Exception:
            return IngestResult(error=FETCH_FALLBACK_MESSAGE)
        if len(text) < MIN_FETCHED_CHARS:
            return IngestResult(error=FETCH_FALLBACK_MESSAGE)
    else:
        text = _normalize_whitespace(raw_input)

    return _cap(text)


def _fetch_and_clean(url: str) -> str:
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(url, timeout=15, headers={"User-Agent": _USER_AGENT})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    # Keep the largest block of paragraph-like text rather than the whole
    # page: nav crumbs, cookie banners, and related-jobs rails otherwise
    # dilute the posting itself.
    blocks = [b.get_text(separator="\n").strip() for b in soup.find_all(["article", "main", "body"])]
    blocks = [b for b in blocks if b]
    text = max(blocks, key=len) if blocks else soup.get_text(separator="\n")

    return _normalize_whitespace(text)


def _normalize_whitespace(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def _cap(text: str) -> IngestResult:
    if len(text) <= MAX_POSTING_CHARS:
        return IngestResult(text=text, truncated=False)
    return IngestResult(text=text[:MAX_POSTING_CHARS], truncated=True)
