#!/usr/bin/env python3
"""Check expected writes and protected-path safety from before/after manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def changed_paths(before: dict[str, str], after: dict[str, str]) -> set[str]:
    paths = set(before) | set(after)
    return {path for path in paths if before.get(path) != after.get(path)}


def is_protected(path: str, protected_prefixes: list[str]) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in protected_prefixes)


def check_case(case: dict) -> list[str]:
    errors: list[str] = []
    before = case.get("before_manifest", {})
    after = case.get("after_manifest", {})
    expected_writes_raw = case.get("expected_writes", [])
    protected_prefixes = case.get("protected_prefixes", [])

    if not isinstance(before, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in before.items()):
        errors.append("before_manifest must map paths to hashes")
        before = {}
    if not isinstance(after, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in after.items()):
        errors.append("after_manifest must map paths to hashes")
        after = {}
    if not isinstance(expected_writes_raw, list) or not all(
        isinstance(item, str) for item in expected_writes_raw
    ):
        errors.append("expected_writes must be a list of paths")
        expected_writes_raw = []
    if not isinstance(protected_prefixes, list) or not all(isinstance(item, str) for item in protected_prefixes):
        errors.append("protected_prefixes must be a list of path prefixes")
        protected_prefixes = []

    expected_writes = set(expected_writes_raw)
    actual_writes = changed_paths(before, after)
    unexpected = sorted(actual_writes - expected_writes)
    missing = sorted(expected_writes - actual_writes)
    protected = sorted(path for path in actual_writes if is_protected(path, protected_prefixes))

    if unexpected:
        errors.append(f"unexpected writes: {', '.join(unexpected)}")
    if missing:
        errors.append(f"expected writes did not happen: {', '.join(missing)}")
    if protected:
        errors.append(f"protected paths changed: {', '.join(protected)}")
    return errors


def load_cases(path: Path):
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            yield line_no, json.loads(line)


def run_cases(path: Path) -> int:
    failed = False
    for line_no, case in load_cases(path):
        name = case.get("case", f"line_{line_no}")
        expected_valid = case.get("expected_valid")
        if not isinstance(expected_valid, bool):
            print(f"FAIL {name}: expected_valid must be true or false")
            failed = True
            continue
        errors = check_case(case)
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
    ok = {
        "before_manifest": {"README.md": "a", "private/context.md": "secret"},
        "after_manifest": {"README.md": "b", "private/context.md": "secret"},
        "expected_writes": ["README.md"],
        "protected_prefixes": ["private"],
    }
    bad = {
        "before_manifest": {"README.md": "a", "private/context.md": "secret"},
        "after_manifest": {"README.md": "b", "private/context.md": "changed"},
        "expected_writes": ["README.md"],
        "protected_prefixes": ["private"],
    }
    assert check_case(ok) == []
    assert check_case(bad)


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
    return run_cases(Path(args.path))


if __name__ == "__main__":
    raise SystemExit(main())
