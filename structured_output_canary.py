#!/usr/bin/env python3
"""Run expected pass/fail canaries for structured model output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reliability_demo import validate_output


def load_cases(path: Path):
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        case = json.loads(line)
        yield line_no, case


def run_canary(path: Path) -> int:
    failed = False
    for line_no, case in load_cases(path):
        name = case.get("case", f"line_{line_no}")
        expected_valid = case.get("expected_valid")
        if not isinstance(expected_valid, bool):
            print(f"FAIL {name}: expected_valid must be true or false")
            failed = True
            continue
        errors = validate_output(case.get("model_output", ""), set(case.get("source_ids", [])))
        actual_valid = not errors
        if actual_valid == expected_valid:
            print(f"PASS {name}")
            continue
        failed = True
        expected = "valid" if expected_valid else "invalid"
        actual = "valid" if actual_valid else f"invalid ({'; '.join(errors)})"
        print(f"FAIL {name}: expected {expected}, got {actual}")
    return 1 if failed else 0


def self_test() -> None:
    valid = json.dumps(
        {
            "answer": "Use the cited source.",
            "action": "summarize",
            "confidence": 0.9,
            "citations": ["doc:one"],
            "writes": [],
        }
    )
    invalid = json.dumps(
        {
            "answer": "I changed the file.",
            "action": "summarize",
            "confidence": 0.9,
            "citations": ["doc:missing"],
            "writes": ["README.md"],
        }
    )
    assert validate_output(valid, {"doc:one"}) == []
    assert validate_output(invalid, {"doc:one"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("self-test passed")
        return 0
    if not args.path:
        parser.error("path is required unless --self-test is used")
    return run_canary(Path(args.path))


if __name__ == "__main__":
    raise SystemExit(main())
