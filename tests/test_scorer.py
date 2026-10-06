from vendoriq.models import CertificationRecord, ContactInfo, SourcedFact, VendorExtraction
from vendoriq.requirement import decision_from_checks, parse_requirement, verify_requirement
from vendoriq.scorer import score_vendor


def sample_profile() -> VendorExtraction:
    return VendorExtraction(
        company_name="Acme Cables",
        website="https://acme.example",
        summary="Manufacturer of aluminium electrical cable accessories.",
        products=[
            SourcedFact(value="Aluminium tubular crimping-type lugs", source_url="https://acme.example/products"),
            SourcedFact(value="Cable glands", source_url="https://acme.example/products"),
        ],
        capabilities=[
            SourcedFact(value="Electrical cable accessory manufacturing", source_url="https://acme.example/about")
        ],
        company_claims=[
            SourcedFact(value="States a commitment to on-time delivery", source_url="https://acme.example/quality")
        ],
        industries_served=[
            SourcedFact(value="Electrical infrastructure", source_url="https://acme.example/industries")
        ],
        certifications=[
            CertificationRecord(
                name="ISO 9001:2015",
                category="quality_certification",
                source_url="https://acme.example/certifications",
            )
        ],
        locations=[SourcedFact(value="Hyderabad, India", source_url="https://acme.example/contact")],
        contacts=[ContactInfo(email="sales@example.com", source_url="https://acme.example/contact")],
    )


def test_requirement_parser_separates_specific_attributes():
    parts = parse_requirement("300 sq.mm aluminium long barrel cable lugs")
    assert parts.materials == ("aluminium",)
    assert "300 sq.mm" in parts.specifications
    assert "long barrel" in parts.variants
    assert "cable" in parts.category_tokens
    assert "lug" in parts.category_tokens


def test_specific_requirement_does_not_get_full_match_without_size_and_variant():
    checks = verify_requirement(sample_profile(), "300 sq.mm aluminium long barrel cable lugs")
    by_component = {check.component: check for check in checks}

    assert by_component["Product / category"].status == "verified"
    assert by_component["Material"].status == "verified"
    assert by_component["Size / specification"].status == "unverified"
    assert by_component["Design / variant"].status == "unverified"
    assert sum(check.points_awarded for check in checks) < 40
    assert decision_from_checks(checks) == "Partial Match"


def test_exact_requirement_can_reach_full_technical_match():
    profile = sample_profile()
    profile.products.append(
        SourcedFact(
            value="300 sq.mm aluminium long barrel cable lug",
            source_url="https://acme.example/products/300",
        )
    )
    checks = verify_requirement(profile, "300 sq.mm aluminium long barrel cable lugs")
    assert all(check.status == "verified" for check in checks)
    assert sum(check.points_awarded for check in checks) == 40


def test_company_claims_are_not_counted_as_capabilities():
    profile = sample_profile()
    profile.capabilities = []
    score = score_vendor(profile, "aluminium cable lugs")
    assert score.capability_evidence == 0


def test_certifications_are_weighted_by_category():
    profile = sample_profile()
    profile.certifications.extend([
        CertificationRecord(name="UL Listed", category="product_listing", source_url="https://acme.example/certs"),
        CertificationRecord(name="CPRI", category="test_validation", source_url="https://acme.example/certs"),
        CertificationRecord(name="RoHS", category="regulatory_conformity", source_url="https://acme.example/certs"),
    ])
    score = score_vendor(profile, "aluminium cable lugs")
    assert score.certifications == 15


def test_missing_certification_is_not_treated_as_a_risk():
    profile = VendorExtraction(
        company_name="Unknown Co",
        website="https://unknown.example",
        summary="Industrial supplier.",
        missing_information=["Quality certifications not verified"],
    )
    score = score_vendor(profile, "industrial pump")
    assert score.certifications == 0
    assert profile.explicit_risk_indicators == []
