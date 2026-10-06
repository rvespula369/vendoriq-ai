from __future__ import annotations

import gradio as gr

from vendoriq.config import load_settings
from vendoriq.service import analyze_vendor_markdown


settings = load_settings()


def run_analysis(website: str, requirement: str) -> str:
    if not website.strip():
        return "Please enter a supplier website URL."
    try:
        return analyze_vendor_markdown(website.strip(), requirement.strip(), settings)
    except Exception as exc:
        return f"## Analysis failed\n\n`{type(exc).__name__}: {exc}`\n\nCheck the URL, API configuration, and whether the target site allows automated requests."


with gr.Blocks(title="VendorIQ") as demo:
    gr.Markdown(
        """
# VendorIQ
### AI Vendor Intelligence & Supplier Analysis
Enter a supplier website and a procurement requirement. VendorIQ crawls relevant pages, extracts evidence-backed vendor data, and applies a deterministic suitability score.
"""
    )
    with gr.Row():
        website = gr.Textbox(label="Supplier website", placeholder="https://example.com")
        requirement = gr.Textbox(label="Procurement requirement", placeholder="e.g. 300 sq.mm aluminium long barrel cable lugs")
    analyze = gr.Button("Analyze Vendor", variant="primary")
    output = gr.Markdown()
    analyze.click(fn=run_analysis, inputs=[website, requirement], outputs=output)


if __name__ == "__main__":
    demo.launch()
