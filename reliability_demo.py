#!/usr/bin/env python3
"""Validate synthetic local-model JSON output before trusting it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_ACTIONS = {"summarize", "route", "ask_clarifying_question"}


def validate_output(raw: str, source_ids: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc.msg}"]

    if not isinstance(data, dict):
        return ["model output must be a JSON object"]
    if not isinstance(data.get("answer"), str) or not data["answer"].strip():
        errors.append("answer must be non-empty text")
    if data.get("action") not in ALLOWED_ACTIONS:
        errors.append(f"action must be one of {sorted(ALLOWED_ACTIONS)}")
    confidence = data.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence must be a number from 0 to 1")
    citations = data.get("citations")
    if not isinstance(citations, list) or not all(isinstance(item, str) for item in citations):
        errors.append("citations must be a list of source IDs")
    else:
        unknown = sorted(set(citations) - source_ids)
        if unknown:
            errors.append(f"citations not in source set: {', '.join(unknown)}")
    writes = data.get("writes")
    if writes != []:
        errors.append("writes must be an empty list in this no-write example")
    return errors


def iter_cases(path: Path):
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        case = json.loads(line)
        yield line_no, case


def run_file(path: Path) -> int:
    failed = False
    for line_no, case in iter_cases(path):
        name = case.get("case", f"line_{line_no}")
        source_ids = set(case.get("source_ids", []))
        errors = validate_output(case.get("model_output", ""), source_ids)
        if errors:
            failed = True
            print(f"FAIL {name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {name}")
    return 1 if failed else 0


def self_test() -> None:
    good = json.dumps(
        {
            "answer": "Use the public README as the source of truth.",
            "action": "summarize",
            "confidence": 0.82,
            "citations": ["doc:readme"],
            "writes": [],
        }
    )
    bad = json.dumps(
        {
            "answer": "I updated the file.",
            "action": "summarize",
            "confidence": 0.9,
            "citations": ["doc:missing"],
            "writes": ["README.md"],
        }
    )
    assert validate_output(good, {"doc:readme"}) == []
    assert validate_output(bad, {"doc:readme"})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        print("self-test passed")
        return 0
    if not args.path:
        parser.error("path is required unless --self-test is used")
    return run_file(Path(args.path))


if __name__ == "__main__":
    raise SystemExit(main())
