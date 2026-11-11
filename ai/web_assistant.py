"""AI helper for Playwright locator suggestions."""

from __future__ import annotations

from typing import Any, Dict

from .client import AiClient


class WebAssistant:
    def __init__(self, client: AiClient | None = None):
        self.client = client or AiClient()

    def suggest_locator(self, dom: str, failed_locator: str, page_url: str = "") -> Dict[str, Any]:
        return self.client.chat_json(
            "suggest_locator",
            {"dom": dom, "failed_locator": failed_locator, "page_url": page_url},
        ).as_dict()
