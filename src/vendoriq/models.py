from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


CertificationCategory = Literal[
    "quality_certification",
    "product_listing",
    "test_validation",
    "regulatory_conformity",
    "other",
]

RequirementStatus = Literal[
    "verified",
    "partial",
    "unverified",
]


class SourcedFact(BaseModel):
    value: str = Field(
        description=(
            "Concise factual value supported "
            "by the source page"
        )
    )

    source_url: str | None = Field(
        default=None,
        description=(
            "Exact analyzed page URL supporting "
            "this fact, when available"
        ),
    )


class CertificationRecord(BaseModel):
    name: str
    category: CertificationCategory = "other"
    source_url: str | None = None


class ContactInfo(BaseModel):
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    source_url: str | None = None


class VendorExtraction(BaseModel):
    company_name: str
    website: str
    summary: str

    products: list[SourcedFact] = Field(
        default_factory=list
    )

    capabilities: list[SourcedFact] = Field(
        default_factory=list
    )

    company_claims: list[SourcedFact] = Field(
        default_factory=list
    )

    technical_disclaimers: list[SourcedFact] = Field(
        default_factory=list
    )

    industries_served: list[SourcedFact] = Field(
        default_factory=list
    )

    certifications: list[CertificationRecord] = Field(
        default_factory=list
    )

    locations: list[SourcedFact] = Field(
        default_factory=list
    )

    contacts: list[ContactInfo] = Field(
        default_factory=list
    )

    missing_information: list[str] = Field(
        default_factory=list
    )

    explicit_risk_indicators: list[SourcedFact] = Field(
        default_factory=list
    )


class RequirementCheck(BaseModel):
    component: str
    expected: str
    status: RequirementStatus

    points_awarded: int = Field(
        ge=0
    )

    points_possible: int = Field(
        ge=0
    )

    evidence: list[str] = Field(
        default_factory=list
    )

    source_urls: list[str] = Field(
        default_factory=list
    )


class ScoreBreakdown(BaseModel):
    requirement_match: int = Field(
        ge=0,
        le=40,
    )

    capability_evidence: int = Field(
        ge=0,
        le=20,
    )

    certifications: int = Field(
        ge=0,
        le=15,
    )

    industry_relevance: int = Field(
        ge=0,
        le=10,
    )

    business_transparency: int = Field(
        ge=0,
        le=15,
    )

    total: int = Field(
        ge=0,
        le=100,
    )

    rationale: list[str] = Field(
        default_factory=list
    )

    requirement_checks: list[RequirementCheck] = Field(
        default_factory=list
    )


class VendorAssessment(BaseModel):
    vendor: VendorExtraction
    requirement: str
    decision: str
    score: ScoreBreakdown
    recommendation: str

    recommended_actions: list[str] = Field(
        default_factory=list
    )

    pages_analyzed: list[str]