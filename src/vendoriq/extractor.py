from __future__ import annotations

import json
import re

from openai import OpenAI
from pydantic import ValidationError

from vendoriq.models import VendorExtraction
from vendoriq.prompts import SYSTEM_PROMPT, extraction_prompt


class ExtractionError(RuntimeError):
    pass


def _json_only(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ExtractionError("Model response did not contain a JSON object.")
    return cleaned[start : end + 1]


class OpenAIVendorExtractor:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for AI extraction.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract(self, website: str, pages_text: str) -> VendorExtraction:
        schema = json.dumps(VendorExtraction.model_json_schema(), indent=2)
        prompt = extraction_prompt(website, pages_text, schema)

        response = self.client.responses.create(
            model=self.model,
            instructions=SYSTEM_PROMPT,
            input=prompt,
        )

        try:
            payload = _json_only(response.output_text)
            parsed = VendorExtraction.model_validate_json(payload)
        except (ValidationError, ExtractionError) as exc:
            raise ExtractionError(f"Unable to validate model output: {exc}") from exc

        # The application, not the model, owns the canonical website field.
        return parsed.model_copy(update={"website": website})
