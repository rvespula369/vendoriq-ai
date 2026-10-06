from __future__ import annotations

from vendoriq.models import ScoreBreakdown, VendorExtraction
from vendoriq.requirement import decision_from_checks, verify_requirement


CERTIFICATION_POINTS = {
    "quality_certification": 6,
    "product_listing": 4,
    "test_validation": 3,
    "regulatory_conformity": 2,
    "other": 1,
}


def score_vendor(profile: VendorExtraction, requirement: str) -> ScoreBreakdown:
    checks = verify_requirement(profile, requirement)
    requirement_score = sum(check.points_awarded for check in checks)

    # Only technical/manufacturing capabilities belong in profile.capabilities after extraction.
    capability_score = min(20, 5 * min(4, len(profile.capabilities)))

    certification_score = min(
        15,
        sum(CERTIFICATION_POINTS.get(cert.category, 1) for cert in profile.certifications),
    )
    industry_score = min(10, 2 * min(5, len(profile.industries_served)))

    # Transparency is based on independently inspectable information, not generic marketing claims.
    transparency_score = 0
    if profile.company_name.strip() and profile.locations:
        transparency_score += 3
    if any(contact.email or contact.phone for contact in profile.contacts):
        transparency_score += 2
    if len(profile.products) >= 2:
        transparency_score += 3
    if profile.capabilities:
        transparency_score += 3
    if any(cert.source_url for cert in profile.certifications):
        transparency_score += 2
    if profile.industries_served:
        transparency_score += 2

    rationale: list[str] = []
    for check in checks:
        rationale.append(
            f"{check.component}: {check.status} ({check.points_awarded}/{check.points_possible}) — expected {check.expected}."
        )
    if profile.certifications:
        rationale.append(f"Found {len(profile.certifications)} classified certification/approval record(s).")
    else:
        rationale.append("No certifications or approvals were verified from the analyzed pages.")
    if profile.missing_information:
        rationale.append(f"{len(profile.missing_information)} important information area(s) remain unverified.")
    if profile.explicit_risk_indicators:
        rationale.append(f"Found {len(profile.explicit_risk_indicators)} explicit risk indicator(s); these require human review.")

    total = requirement_score + capability_score + certification_score + industry_score + transparency_score
    return ScoreBreakdown(
        requirement_match=min(40, requirement_score),
        capability_evidence=capability_score,
        certifications=certification_score,
        industry_relevance=industry_score,
        business_transparency=min(15, transparency_score),
        total=min(100, total),
        rationale=rationale,
        requirement_checks=checks,
    )


def recommendation_for(score: ScoreBreakdown) -> tuple[str, list[str], str]:
    decision = decision_from_checks(score.requirement_checks)
    unverified = [check for check in score.requirement_checks if check.status != "verified"]

    actions: list[str] = []
    for check in unverified:
        actions.append(f"Request technical evidence for {check.component.lower()}: {check.expected}.")
    actions.extend([
        "Obtain the current technical datasheet/drawing for the proposed item.",
        "Obtain current quotation, delivery lead time, and commercial terms.",
        "Verify applicable quality/test certificates against authoritative documents before approval.",
    ])
    # Preserve order while removing duplicates.
    actions = list(dict.fromkeys(actions))

    if decision == "Exact Match" and score.total >= 75:
        recommendation = "Strong technical candidate for the next procurement review stage, subject to document, commercial, capacity, and compliance verification."
    elif decision == "Partial Match":
        recommendation = "Conditional match: the vendor appears relevant, but one or more required technical attributes remain unverified from the analyzed pages."
    else:
        recommendation = "Insufficient website evidence to confirm the requested item. Request technical documentation or perform manual supplier qualification before shortlisting."

    return decision, actions, recommendation
