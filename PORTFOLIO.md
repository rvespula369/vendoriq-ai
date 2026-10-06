# Portfolio Entry — VendorIQ

## VendorIQ — AI Vendor Intelligence & Supplier Analysis Platform

Built an evidence-aware Generative AI procurement application that crawls supplier websites, extracts structured product and capability data, classifies certifications/approvals, decomposes technical procurement requirements, and applies explainable deterministic supplier-fit scoring.

### What makes the project technically significant

- Hybrid deterministic + LLM architecture rather than delegating decisions entirely to a model
- Query-aware crawling that preserves product-specific URL parameters
- Structured Pydantic extraction with source provenance
- Explicit distinction between missing information and negative evidence
- Separate technical capabilities from marketing/company claims
- Component-level technical matching for category, material, size/specification, and design variant
- Explainable 100-point scoring model with procurement follow-up actions
- Prompt-injection-aware handling of scraped web content
- Automated unit tests and Gradio demonstration UI

### Stack

Python, OpenAI Responses API, Pydantic, BeautifulSoup, Requests, Gradio, Pytest

### Interview summary

> I built VendorIQ to show how an enterprise GenAI system should combine probabilistic extraction with deterministic controls. The LLM interprets supplier website text, but Python owns URL handling, technical requirement verification, scoring, and report generation. I also preserve evidence provenance and distinguish unverified information from actual supplier risks.
