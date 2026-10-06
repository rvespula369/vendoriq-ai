from __future__ import annotations

from vendoriq.config import Settings
from vendoriq.extractor import OpenAIVendorExtractor
from vendoriq.models import VendorAssessment
from vendoriq.report import render_markdown
from vendoriq.scorer import recommendation_for, score_vendor
from vendoriq.scraper import discover_links, fetch_page, normalize_url
from vendoriq.selector import select_relevant_links


def _format_pages(pages) -> str:
    chunks = []
    for page in pages:
        chunks.append(f"SOURCE URL: {page.url}\nPAGE TITLE: {page.title}\nCONTENT:\n{page.text}")
    return "\n\n---\n\n".join(chunks)


def _unique_pages(pages):
    unique = []
    seen: set[str] = set()
    for page in pages:
        canonical = normalize_url(page.url)
        if canonical in seen:
            continue
        seen.add(canonical)
        unique.append(page)
    return unique


def analyze_vendor(website: str, requirement: str, settings: Settings) -> VendorAssessment:
    root = normalize_url(website)
    home = fetch_page(root, settings.request_timeout_seconds, settings.max_chars_per_page)
    links = discover_links(root, settings.request_timeout_seconds)
    selected = select_relevant_links(links, limit=max(0, settings.max_pages - 1))

    pages = [home]
    seen = {normalize_url(home.url)}
    for link in selected:
        canonical = normalize_url(link.url)
        if canonical in seen:
            continue
        try:
            page = fetch_page(canonical, settings.request_timeout_seconds, settings.max_chars_per_page)
        except Exception:
            # One bad page should not fail the entire supplier analysis.
            continue
        canonical_page = normalize_url(page.url)
        if canonical_page in seen:
            continue
        seen.add(canonical_page)
        pages.append(page)

    pages = _unique_pages(pages)
    extractor = OpenAIVendorExtractor(settings.openai_api_key or "", settings.openai_model)
    profile = extractor.extract(root, _format_pages(pages))
    score = score_vendor(profile, requirement)
    decision, actions, recommendation = recommendation_for(score)

    return VendorAssessment(
        vendor=profile,
        requirement=requirement.strip(),
        decision=decision,
        score=score,
        recommendation=recommendation,
        recommended_actions=actions,
        pages_analyzed=[page.url for page in pages],
    )


def analyze_vendor_markdown(website: str, requirement: str, settings: Settings) -> str:
    return render_markdown(analyze_vendor(website, requirement, settings))
