from __future__ import annotations

import re
from dataclasses import dataclass

from vendoriq.models import RequirementCheck, SourcedFact, VendorExtraction


MATERIAL_ALIASES = {
    "aluminium": {"aluminium", "aluminum", "al"},
    "copper": {"copper", "cu"},
    "stainless steel": {"stainless steel", "ss", "ss304", "ss316", "ss 304", "ss 316"},
    "carbon steel": {"carbon steel", "cs"},
    "mild steel": {"mild steel", "ms"},
    "brass": {"brass"},
    "pvc": {"pvc"},
    "xlpe": {"xlpe"},
}

VARIANT_PHRASES = [
    "long barrel", "short barrel", "double compression", "single compression",
    "heavy duty", "light duty", "tubular", "crimping type", "crimping-type",
    "shear head", "shear-head", "bolted", "inline", "ring type", "ring-type",
    "fork type", "fork-type", "pin type", "pin-type",
]

STOP_WORDS = {
    "and", "or", "the", "a", "an", "for", "of", "to", "in", "on", "with",
    "required", "requirement", "supplier", "vendor", "need", "looking", "qty",
    "quantity", "nos", "no", "pcs", "piece", "pieces",
}

UNIT_PATTERN = r"(?:sq\.?\s*mm|mm(?:2|²)?|cm|m|kv|v|a|amp|amps|w|kw|mw|kg|g|mt|m3/hr|m³/hr|bar|psi|hz|inch|inches|\")"
SPEC_RE = re.compile(rf"\b\d+(?:\.\d+)?\s*{UNIT_PATTERN}\b", re.IGNORECASE)


@dataclass(frozen=True)
class RequirementParts:
    category_tokens: tuple[str, ...]
    materials: tuple[str, ...]
    specifications: tuple[str, ...]
    variants: tuple[str, ...]


def _normal_text(value: str) -> str:
    text = value.lower().replace("²", "2").replace("³", "3")
    text = text.replace("sq. mm", "sqmm").replace("sq.mm", "sqmm").replace("sq mm", "sqmm")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _token(value: str) -> str:
    value = _normal_text(value)
    if value.endswith("ies") and len(value) > 4:
        return value[:-3] + "y"
    if value.endswith("s") and not value.endswith("ss") and len(value) > 3:
        return value[:-1]
    return value


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower().replace("²", "2").replace("³", "3"))


def parse_requirement(requirement: str) -> RequirementParts:
    raw = requirement.lower()
    materials: list[str] = []
    material_words: set[str] = set()
    for canonical, aliases in MATERIAL_ALIASES.items():
        if any(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", raw) for alias in aliases):
            materials.append(canonical)
            for alias in aliases:
                material_words.update(_normal_text(alias).split())

    specifications = tuple(dict.fromkeys(match.group(0).strip() for match in SPEC_RE.finditer(raw)))
    variants = tuple(phrase for phrase in VARIANT_PHRASES if phrase in raw)

    scrubbed = raw
    for spec in specifications:
        scrubbed = scrubbed.replace(spec, " ")
    for phrase in variants:
        scrubbed = scrubbed.replace(phrase, " ")
    for aliases in MATERIAL_ALIASES.values():
        for alias in aliases:
            scrubbed = re.sub(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", " ", scrubbed)

    words = re.findall(r"[a-z][a-z0-9-]*", _normal_text(scrubbed))
    category_tokens = []
    for word in words:
        normalized = _token(word)
        if len(normalized) <= 2 or normalized in STOP_WORDS or normalized in material_words:
            continue
        if normalized not in category_tokens:
            category_tokens.append(normalized)

    return RequirementParts(
        category_tokens=tuple(category_tokens),
        materials=tuple(dict.fromkeys(materials)),
        specifications=specifications,
        variants=tuple(dict.fromkeys(variants)),
    )


def _facts(profile: VendorExtraction) -> list[SourcedFact]:
    facts = list(profile.products) + list(profile.capabilities) + list(profile.company_claims) + list(profile.industries_served)
    facts += list(profile.locations)
    for cert in profile.certifications:
        facts.append(SourcedFact(value=cert.name, source_url=cert.source_url))
    return facts


def _find_evidence(profile: VendorExtraction, needles: list[str], require_all: bool = True) -> tuple[list[str], list[str]]:
    evidence: list[str] = []
    urls: list[str] = []
    for fact in _facts(profile):
        hay = _normal_text(fact.value)
        checks = [_normal_text(item) in hay or _compact(item) in _compact(fact.value) for item in needles]
        matched = all(checks) if require_all else any(checks)
        if matched:
            evidence.append(fact.value)
            if fact.source_url and fact.source_url not in urls:
                urls.append(fact.source_url)
    return evidence[:5], urls[:5]


def _weighted_component(component: str, expected: str, matched_fraction: float, points: int, evidence: list[str], urls: list[str]) -> RequirementCheck:
    awarded = round(points * max(0.0, min(1.0, matched_fraction)))
    status = "verified" if matched_fraction >= 0.999 else "partial" if matched_fraction > 0 else "unverified"
    return RequirementCheck(
        component=component,
        expected=expected,
        status=status,
        points_awarded=awarded,
        points_possible=points,
        evidence=evidence,
        source_urls=urls,
    )


def verify_requirement(profile: VendorExtraction, requirement: str) -> list[RequirementCheck]:
    parts = parse_requirement(requirement)

    component_specs: list[tuple[str, list[str], int]] = []
    if parts.category_tokens:
        component_specs.append(("Product / category", list(parts.category_tokens), 12))
    if parts.materials:
        component_specs.append(("Material", list(parts.materials), 8))
    if parts.specifications:
        component_specs.append(("Size / specification", list(parts.specifications), 12))
    if parts.variants:
        component_specs.append(("Design / variant", list(parts.variants), 8))

    if not component_specs:
        return []

    base_total = sum(points for _, _, points in component_specs)
    scale = 40 / base_total
    checks: list[RequirementCheck] = []

    corpus = " ".join(f.value for f in _facts(profile))
    corpus_norm = _normal_text(corpus)
    corpus_compact = _compact(corpus)

    for component, expected_parts, base_points in component_specs:
        points = round(base_points * scale)
        # Ensure the final component absorbs rounding so the available total remains exactly 40.
        if component == component_specs[-1][0]:
            points = 40 - sum(item.points_possible for item in checks)

        matches: list[bool] = []
        for item in expected_parts:
            if component == "Product / category":
                token = _token(item)
                corpus_tokens = {_token(word) for word in corpus_norm.split()}
                matches.append(token in corpus_tokens)
            else:
                matches.append(_normal_text(item) in corpus_norm or _compact(item) in corpus_compact)

        fraction = sum(matches) / len(matches) if matches else 0.0
        evidence_needles = [part for part, ok in zip(expected_parts, matches) if ok]
        evidence, urls = _find_evidence(profile, evidence_needles, require_all=False) if evidence_needles else ([], [])
        checks.append(
            _weighted_component(
                component,
                ", ".join(expected_parts),
                fraction,
                points,
                evidence,
                urls,
            )
        )

    return checks


def decision_from_checks(checks: list[RequirementCheck]) -> str:
    if not checks:
        return "Insufficient Evidence"
    if all(check.status == "verified" for check in checks):
        return "Exact Match"
    if any(check.status in {"verified", "partial"} for check in checks):
        return "Partial Match"
    return "Insufficient Evidence"
