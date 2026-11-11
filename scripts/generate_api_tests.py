#!/usr/bin/env python3
"""Generate a reviewed API-test draft from an OpenAPI URL or local file."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.api_assistant import ApiAssistant


def load_spec(source: str) -> dict:
    if source.startswith("http://") or source.startswith("https://"):
        with urllib.request.urlopen(source, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(source).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="OpenAPI URL or JSON file")
    parser.add_argument("--output", default="artifacts/generated_api_tests.py")
    args = parser.parse_args()
    result = ApiAssistant().generate_tests(load_spec(args.spec))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "# AI-generated draft. Review business expectations before merging.\n\n"
        + result["result"].get("code", "# No code generated\n"),
        encoding="utf-8",
    )
    metadata = output.with_suffix(".json")
    metadata.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote draft: {output}")
    print(f"Wrote metadata: {metadata}")
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
