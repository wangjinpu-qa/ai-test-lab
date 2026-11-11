#!/usr/bin/env python3
"""Reset the local order database through the test-only endpoint."""

from __future__ import annotations

import argparse
import json
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    request = urllib.request.Request(f"{args.base_url.rstrip('/')}/api/test/reset", method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        print(json.dumps(json.loads(response.read().decode("utf-8")), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
