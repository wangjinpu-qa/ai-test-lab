#!/usr/bin/env python3
"""Diagnose a saved failure context without changing source code."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.api_assistant import ApiAssistant


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON failure context")
    parser.add_argument("--output", default="artifacts/failure-diagnosis.json")
    args = parser.parse_args()
    context = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = ApiAssistant().diagnose_failure(context)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
