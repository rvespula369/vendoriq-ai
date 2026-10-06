from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    request_timeout_seconds: int
    max_pages: int
    max_chars_per_page: int


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]

    load_dotenv(
        dotenv_path=project_root / ".env",
        override=False,
    )

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv(
            "OPENAI_MODEL",
            "gpt-6-luna",
        ),
        request_timeout_seconds=int(
            os.getenv(
                "REQUEST_TIMEOUT_SECONDS",
                "15",
            )
        ),
        max_pages=int(
            os.getenv(
                "MAX_PAGES",
                "8",
            )
        ),
        max_chars_per_page=int(
            os.getenv(
                "MAX_CHARS_PER_PAGE",
                "9000",
            )
        ),
    )