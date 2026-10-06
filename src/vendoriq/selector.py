from __future__ import annotations

from urllib.parse import urlparse

from vendoriq.scraper import DiscoveredLink


HIGH_VALUE_TERMS = {
    "about": 6,
    "company": 4,
    "profile": 4,
    "product": 7,
    "products": 7,
    "catalog": 6,
    "solution": 5,
    "capability": 7,
    "capabilities": 7,
    "manufacturing": 7,
    "facility": 5,
    "facilities": 5,
    "quality": 6,
    "certification": 7,
    "certifications": 7,
    "industry": 5,
    "industries": 5,
    "sector": 4,
    "contact": 3,
    "location": 3,
}

LOW_VALUE_TERMS = {
    "privacy": -10,
    "cookie": -10,
    "terms": -10,
    "login": -8,
    "signin": -8,
    "cart": -8,
    "blog": -2,
    "news": -1,
    "career": -2,
    "jobs": -2,
}


PAGE_CATEGORIES = {
    "about": (
        "about",
        "company",
        "profile",
        "who we are",
    ),
    "products": (
        "product",
        "products",
        "catalog",
        "terminal",
        "lug",
        "connector",
    ),
    "capabilities": (
        "capability",
        "capabilities",
        "manufacturing",
        "facility",
        "facilities",
        "plant",
        "process",
        "technology",
    ),
    "quality": (
        "quality",
        "certif",
        "approval",
        "testing",
        "test",
        "compliance",
        "iso",
        "ul",
        "rohs",
        "cpri",
    ),
    "industries": (
        "industry",
        "industries",
        "sector",
        "application",
        "applications",
        "markets",
    ),
    "contact": (
        "contact",
        "location",
        "address",
        "reach us",
    ),
}


CATEGORY_PRIORITY = [
    "about",
    "products",
    "capabilities",
    "quality",
    "industries",
    "contact",
]


def _link_text(link: DiscoveredLink) -> str:
    parsed = urlparse(link.url)

    return (
        f"{parsed.path} "
        f"{parsed.query} "
        f"{link.anchor_text}"
    ).lower().replace("-", " ").replace("_", " ")


def score_link(link: DiscoveredLink) -> int:
    haystack = _link_text(link)

    score = 0

    for term, weight in HIGH_VALUE_TERMS.items():
        if term in haystack:
            score += weight

    for term, weight in LOW_VALUE_TERMS.items():
        if term in haystack:
            score += weight

    depth = len(
        [
            segment
            for segment in urlparse(link.url).path.split("/")
            if segment
        ]
    )

    score -= max(0, depth - 2)

    return score


def classify_link(link: DiscoveredLink) -> str | None:
    haystack = _link_text(link)

    best_category = None
    best_hits = 0

    for category, terms in PAGE_CATEGORIES.items():
        hits = sum(
            1
            for term in terms
            if term in haystack
        )

        if hits > best_hits:
            best_hits = hits
            best_category = category

    return best_category


def select_relevant_links(
    links: list[DiscoveredLink],
    limit: int = 7,
) -> list[DiscoveredLink]:

    ranked = sorted(
        links,
        key=lambda item: (
            score_link(item),
            item.url,
        ),
        reverse=True,
    )

    useful = [
        item
        for item in ranked
        if score_link(item) > 0
    ]

    selected: list[DiscoveredLink] = []
    selected_urls: set[str] = set()

    # First ensure page-type diversity.
    for category in CATEGORY_PRIORITY:

        category_links = [
            link
            for link in useful
            if classify_link(link) == category
            and link.url not in selected_urls
        ]

        if category_links:
            best = category_links[0]

            selected.append(best)
            selected_urls.add(best.url)

        if len(selected) >= limit:
            return selected

    # Fill remaining capacity with highest-ranked useful pages.
    for link in useful:

        if link.url in selected_urls:
            continue

        selected.append(link)
        selected_urls.add(link.url)

        if len(selected) >= limit:
            break

    return selected