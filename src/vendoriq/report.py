from __future__ import annotations

from collections import defaultdict

from vendoriq.models import SourcedFact, VendorAssessment


CERT_LABELS = {
    "quality_certification": "Quality Certifications",
    "product_listing": "Product Approvals / Listings",
    "test_validation": "Testing / Validation References",
    "regulatory_conformity": "Regulatory / Conformity Claims",
    "other": "Other Certification / Approval References",
}

STATUS_ICON = {
    "verified": "✅ Verified",
    "partial": "⚠️ Partial",
    "unverified": "⚠️ Unverified",
}


def _bullets(items: list[str]) -> str:
    if not items:
        return "- Not verified from analyzed pages"

    return "\n".join(
        f"- {item}"
        for item in items
    )


def _source_link(url: str | None) -> str:
    return f" ([source]({url}))" if url else ""


def _fact_bullets(
    items: list[SourcedFact],
) -> str:
    if not items:
        return "- Not verified from analyzed pages"

    return "\n".join(
        f"- {item.value}{_source_link(item.source_url)}"
        for item in items
    )


def _requirement_table(
    assessment: VendorAssessment,
) -> str:
    checks = assessment.score.requirement_checks

    if not checks:
        return (
            "No structured procurement requirement "
            "could be derived from the supplied text."
        )

    rows = [
        "| Requirement component | Expected | Status | Score | Evidence |",
        "|---|---|---|---:|---|",
    ]

    for check in checks:
        evidence = (
            "; ".join(check.evidence[:2])
            if check.evidence
            else "Not found in analyzed evidence"
        )

        rows.append(
            f"| {check.component} | "
            f"{check.expected} | "
            f"{STATUS_ICON[check.status]} | "
            f"{check.points_awarded}/"
            f"{check.points_possible} | "
            f"{evidence} |"
        )

    return "\n".join(rows)


def _certification_sections(
    assessment: VendorAssessment,
) -> str:
    grouped = defaultdict(list)

    for cert in assessment.vendor.certifications:
        grouped[cert.category].append(
            f"{cert.name}"
            f"{_source_link(cert.source_url)}"
        )

    sections = []

    order = [
        "quality_certification",
        "product_listing",
        "test_validation",
        "regulatory_conformity",
        "other",
    ]

    for key in order:
        if grouped[key]:
            sections.append(
                f"### {CERT_LABELS[key]}\n"
                f"{_bullets(grouped[key])}"
            )

    if not sections:
        return "- Not verified from analyzed pages"

    return "\n\n".join(sections)


def _contacts(
    assessment: VendorAssessment,
) -> list[str]:
    contacts = []

    for contact in assessment.vendor.contacts:
        bits = [
            value
            for value in [
                contact.email,
                contact.phone,
                contact.address,
            ]
            if value
        ]

        if bits:
            contacts.append(
                " | ".join(bits)
                + _source_link(contact.source_url)
            )

    return contacts


def _evidence_sources(
    assessment: VendorAssessment,
) -> list[str]:
    urls: list[str] = []

    vendor = assessment.vendor

    fact_lists = [
        vendor.products,
        vendor.capabilities,
        vendor.company_claims,
        vendor.technical_disclaimers,
        vendor.industries_served,
        vendor.locations,
        vendor.explicit_risk_indicators,
    ]

    for facts in fact_lists:
        for fact in facts:
            if (
                fact.source_url
                and fact.source_url not in urls
            ):
                urls.append(fact.source_url)

    for cert in vendor.certifications:
        if (
            cert.source_url
            and cert.source_url not in urls
        ):
            urls.append(cert.source_url)

    for contact in vendor.contacts:
        if (
            contact.source_url
            and contact.source_url not in urls
        ):
            urls.append(contact.source_url)

    return urls


def _evidence_coverage(
    assessment: VendorAssessment,
) -> tuple[int, str]:

    vendor = assessment.vendor
    checks = assessment.score.requirement_checks

    def find_requirement_status(
        keyword: str,
    ) -> str:

        for check in checks:
            if keyword.lower() in check.component.lower():
                return check.status

        return "unverified"

    items = [
        (
            "Product / category",
            find_requirement_status("product"),
        ),
        (
            "Material",
            find_requirement_status("material"),
        ),
        (
            "Size / specification",
            find_requirement_status("size"),
        ),
        (
            "Design / variant",
            find_requirement_status("design"),
        ),
        (
            "Certifications / approvals",
            "verified"
            if vendor.certifications
            else "unverified",
        ),
        (
            "Technical capabilities",
            "verified"
            if vendor.capabilities
            else "unverified",
        ),
        (
            "Industries served",
            "verified"
            if vendor.industries_served
            else "unverified",
        ),
        (
            "Company identity",
            "verified"
            if (
                vendor.company_name.strip()
                and (
                    vendor.locations
                    or vendor.contacts
                )
            )
            else "unverified",
        ),
    ]

    weights = {
        "verified": 1.0,
        "partial": 0.5,
        "unverified": 0.0,
    }

    achieved = sum(
        weights.get(status, 0.0)
        for _, status in items
    )

    percentage = round(
        achieved / len(items) * 100
    )

    labels = {
        "verified": "✅ Verified",
        "partial": "⚠️ Partial",
        "unverified": "⚠️ Unverified",
    }

    rows = [
        "| Evidence area | Coverage |",
        "|---|---|",
    ]

    for name, status in items:
        rows.append(
            f"| {name} | {labels[status]} |"
        )

    return percentage, "\n".join(rows)


def render_markdown(
    assessment: VendorAssessment,
) -> str:

    vendor = assessment.vendor
    score = assessment.score

    coverage_percentage, coverage_table = (
        _evidence_coverage(assessment)
    )

    return f"""# VendorIQ Assessment — {vendor.company_name}

**Website:** {vendor.website}  
**Procurement requirement:** {assessment.requirement or 'Not specified'}  
**Overall decision:** **{assessment.decision}**  
**Suitability score:** **{score.total}/100**  
**Evidence coverage:** **{coverage_percentage}%**

## 1. Technical Requirement Verification
{_requirement_table(assessment)}

## 2. Evidence Coverage
{coverage_table}

## 3. Executive Summary
{vendor.summary}

## 4. Products
{_fact_bullets(vendor.products)}

## 5. Verified Technical / Manufacturing Capabilities
{_fact_bullets(vendor.capabilities)}

## 6. Company / Commercial Claims
{_fact_bullets(vendor.company_claims)}

## 7. Technical Disclaimers
{_fact_bullets(vendor.technical_disclaimers)}

## 8. Certifications, Approvals & Testing
{_certification_sections(assessment)}

## 9. Industries Served
{_fact_bullets(vendor.industries_served)}

## 10. Locations
{_fact_bullets(vendor.locations)}

## 11. Contact Information
{_bullets(_contacts(assessment))}

## 12. Missing / Unverified Information
{_bullets(vendor.missing_information)}

## 13. Explicit Risk Indicators
{_fact_bullets(vendor.explicit_risk_indicators)}

## 14. Score Breakdown
- Technical requirement match: {score.requirement_match}/40
- Technical capability evidence: {score.capability_evidence}/20
- Certifications / approvals: {score.certifications}/15
- Industry relevance: {score.industry_relevance}/10
- Business transparency: {score.business_transparency}/15

## 15. Recommendation
{assessment.recommendation}

### Recommended Procurement Actions
{_bullets(assessment.recommended_actions)}

## 16. Scoring Rationale
{_bullets(score.rationale)}

## 17. Evidence Sources
{_bullets(_evidence_sources(assessment))}

## 18. Pages Analyzed
{_bullets(assessment.pages_analyzed)}

> VendorIQ is a research-assistance tool. Supplier qualification,
> commercial decisions, compliance checks, and onboarding should
> include human verification and authoritative documents.
"""