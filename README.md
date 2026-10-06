# VendorIQ — AI Vendor Intelligence & Supplier Analysis

VendorIQ is a Generative AI application that turns public supplier websites into structured procurement intelligence. It crawls relevant pages, extracts evidence-backed vendor facts, verifies technical requirement components, classifies certifications/approvals, and applies an explainable deterministic suitability score.

## Version 0.2 highlights

- Preserves meaningful product query parameters instead of dropping them from URLs
- Deduplicates analyzed pages
- Splits procurement requirements into product/category, material, specification, and design/variant components
- Produces `Exact Match`, `Partial Match`, or `Insufficient Evidence` decisions
- Keeps company/marketing claims separate from verified technical capabilities
- Classifies ISO, UL, test-lab references, CE/RoHS, and other evidence separately
- Adds source URLs to extracted products, capabilities, industries, locations, and certifications
- Uses a more granular business-transparency score
- Generates concrete procurement follow-up actions for unverified requirements

## Why I built this

Supplier discovery usually requires manually browsing product, quality, facility, certification, and contact pages. VendorIQ demonstrates a hybrid AI architecture: an LLM interprets unstructured website content while conventional Python owns crawling, URL normalization, validation, technical matching, scoring, and report generation.

## Key capabilities

- Same-domain website crawling and query-aware URL normalization
- Deterministic ranking of product, capability, quality and certification pages
- AI extraction through the OpenAI Responses API
- Pydantic validation of model output
- Evidence URLs and explicit missing-information tracking
- Requirement decomposition and technical attribute verification
- Deterministic 100-point suitability scoring
- Certification/approval taxonomy
- Gradio portfolio UI
- Unit tests for URL handling, page selection, matching, scoring and reporting

## Architecture

```text
Supplier URL
    -> crawler
    -> query-aware URL normalization
    -> relevant page selector
    -> cleaned evidence
    -> LLM structured extraction
    -> Pydantic validation
    -> deterministic requirement verification
    -> deterministic scoring
    -> evidence-aware VendorIQ report
```

See [`docs/architecture.md`](docs/architecture.md) for the detailed design.

## AI engineering decisions

### 1. The LLM does not own the supplier score
The model interprets unstructured content. Python applies transparent scoring rules, keeping the decision path inspectable and testable.

### 2. Missing information is not negative information
If a website does not mention a required size, capacity, or certification, VendorIQ marks it as **unverified**. It does not infer that the supplier lacks it.

### 3. Technical capabilities are separate from company claims
Statements such as “committed to quality” or “time-bound delivery” are not manufacturing capabilities. VendorIQ stores them separately from verified technical/process capabilities.

### 4. Certifications are not all the same
VendorIQ classifies evidence as quality certification, product listing, test/validation reference, regulatory/conformity claim, or other.

### 5. Website content is untrusted data
The extraction prompt instructs the LLM to treat scraped text as source data rather than executable instructions, reducing prompt-injection risk.

### 6. Evidence provenance is retained
Important extracted facts carry the analyzed source URL so a reviewer can verify them.

## Technical requirement model

For a requirement such as:

```text
300 sq.mm aluminium long barrel cable lugs
```

VendorIQ verifies separately:

| Component | Example | Base weight |
|---|---|---:|
| Product/category | cable lugs | 12 |
| Material | aluminium | 8 |
| Size/specification | 300 sq.mm | 12 |
| Design/variant | long barrel | 8 |
| **Total** |  | **40** |

If a requirement omits one of these categories, the available weights are normalized to remain out of 40.

## Overall scoring model

| Dimension | Weight |
|---|---:|
| Technical requirement match | 40 |
| Technical capability evidence | 20 |
| Certifications / approvals | 15 |
| Industry relevance | 10 |
| Business transparency | 15 |
| **Total** | **100** |

The score is a research aid, not an automated supplier approval decision.

## Tech stack

- Python 3.11+
- OpenAI Responses API
- Pydantic
- Requests
- BeautifulSoup
- Gradio
- Pytest

## Setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Create `.env` from `.env.example` and add a **private** API key. Never commit `.env`.

Run tests:

```powershell
python -m pytest -q
```

Run the app:

```powershell
$env:PYTHONPATH="src"
python app.py
```

## Example use case

**Supplier website:** cable-accessory manufacturer  
**Requirement:** `300 sq.mm aluminium long barrel cable lugs`

A strong output should distinguish:

- aluminium cable lug family: verified
- 300 sq.mm: verified or unverified based on source evidence
- long-barrel construction: verified or unverified based on source evidence

It must not treat generic product-family evidence as proof of exact technical compliance.

## Portfolio learning outcomes

This project demonstrates:

- prompt design and context construction
- API-based LLM integration
- unstructured-to-structured extraction
- evidence provenance
- schema validation
- web scraping and content cleaning
- deterministic + probabilistic system design
- procurement requirement decomposition
- explainable scoring
- hallucination controls
- prompt-injection awareness
- testable business logic
- simple AI application deployment

## Current limitations

- JavaScript-heavy sites may require a browser-based crawler.
- Requirement parsing uses deterministic domain heuristics and does not yet cover every engineering unit/material taxonomy.
- The page selector is heuristic rather than embedding-based.
- Supplier claims still require human verification against authoritative documents.
- No authentication or persistent database is included in the MVP.

## Roadmap

- Browser crawler for dynamic sites
- Embedding-based page ranking
- PDF/datasheet/certificate ingestion
- Vendor comparison dashboard
- Export to PDF/Excel
- Azure deployment and telemetry
- Human approval workflow
- Configurable organization-specific scoring policies

## Disclaimer

VendorIQ is a portfolio/research project. It must not be used as the sole basis for supplier onboarding, compliance, financial, safety, or legal decisions.
