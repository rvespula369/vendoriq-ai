from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0 Safari/537.36"
    )
}

SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:")
SKIP_SUFFIXES = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".zip", ".rar", ".7z", ".mp4", ".mp3", ".css", ".js",
)
TRACKING_QUERY_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "msclkid", "ref", "referrer",
}


@dataclass(frozen=True)
class PageDocument:
    url: str
    title: str
    text: str


@dataclass(frozen=True)
class DiscoveredLink:
    url: str
    anchor_text: str


def normalize_url(url: str, base_url: str | None = None) -> str:
    """Create a crawl-safe canonical URL while preserving business-critical query parameters."""
    candidate = urljoin(base_url, url) if base_url else url
    parsed = urlparse(candidate.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]
    query = urlencode(filtered_query, doseq=True)

    # Fragments are client-side anchors and do not identify a different crawl target.
    return urlunparse((scheme, netloc, path, "", query, ""))


def same_domain(url: str, root_url: str) -> bool:
    a = urlparse(url).netloc.lower().removeprefix("www.")
    b = urlparse(root_url).netloc.lower().removeprefix("www.")
    return bool(a and b and a == b)


def should_skip_url(url: str) -> bool:
    lowered = url.lower()
    if lowered.startswith(SKIP_SCHEMES):
        return True
    path = urlparse(lowered).path
    return path.endswith(SKIP_SUFFIXES)


def fetch_page(url: str, timeout: int = 15, max_chars: int = 9000) -> PageDocument:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise ValueError(f"Unsupported content type: {content_type or 'unknown'}")

    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else url

    if soup.body:
        for tag in soup.body(["script", "style", "noscript", "svg", "img", "input", "form"]):
            tag.decompose()
        text = soup.body.get_text("\n", strip=True)
    else:
        text = soup.get_text("\n", strip=True)

    return PageDocument(url=normalize_url(response.url or url), title=title, text=text[:max_chars])


def discover_links(url: str, timeout: int = 15) -> list[DiscoveredLink]:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    seen: set[str] = set()
    links: list[DiscoveredLink] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href or should_skip_url(href):
            continue
        full_url = normalize_url(href, response.url or url)
        if not same_domain(full_url, url) or full_url in seen:
            continue
        seen.add(full_url)
        links.append(DiscoveredLink(url=full_url, anchor_text=anchor.get_text(" ", strip=True)))
    return links
