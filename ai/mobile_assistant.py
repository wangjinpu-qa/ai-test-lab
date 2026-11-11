"""AI helper for Appium element suggestions."""

from __future__ import annotations

from typing import Any, Dict

from .client import AiClient


class MobileAssistant:
    def __init__(self, client: AiClient | None = None):
        self.client = client or AiClient()

    def find_element(self, instruction: str, page_source: str = "", screenshot_path: str = "") -> Dict[str, Any]:
        return self.client.chat_json(
            "find_mobile_element",
            {
                "instruction": instruction,
                "page_source": page_source,
                "screenshot_path": screenshot_path,
            },
        ).as_dict()
