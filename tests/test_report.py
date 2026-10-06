from vendoriq.models import ScoreBreakdown, SourcedFact, VendorAssessment, VendorExtraction
from vendoriq.report import render_markdown


def test_report_contains_decision_and_technical_verification():
    vendor = VendorExtraction(
        company_name="Acme",
        website="https://acme.example",
        summary="Supplier.",
        products=[SourcedFact(value="Aluminium cable lugs", source_url="https://acme.example/products")],
    )
    assessment = VendorAssessment(
        vendor=vendor,
        requirement="300 sq.mm aluminium long barrel cable lugs",
        decision="Partial Match",
        score=ScoreBreakdown(
            requirement_match=20,
            capability_evidence=0,
            certifications=0,
            industry_relevance=0,
            business_transparency=3,
            total=23,
        ),
        recommendation="Conditional match.",
        recommended_actions=["Request datasheet."],
        pages_analyzed=["https://acme.example"],
    )
    report = render_markdown(assessment)
    assert "Overall decision" in report
    assert "Partial Match" in report
    assert "Technical Requirement Verification" in report
    assert "Recommended Procurement Actions" in report
