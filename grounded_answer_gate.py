#!/usr/bin/env python3
"""Fail closed before a web-backed model answer enters trusted context."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any


CASE_SCHEMA_VERSION = "citeglass_grounded_answer_case_v0"
CANDIDATE_SCHEMA_VERSION = "citeglass_grounded_answer_candidate_v0"
SOURCE_SCHEMA_VERSION = "citeglass_typed_source_projection_v0"
RECEIPT_SCHEMA_VERSION = "citeglass_grounded_answer_receipt_v0"
FIXTURE_SCHEMA_VERSION = "citeglass_grounded_answer_fixture_v0"

CASE_KEYS = {"schema_version", "source_projections", "candidate_output"}
SOURCE_KEYS = {
    "schema_version",
    "source_ref",
    "source_url",
    "fact_type",
    "subject",
    "tag_name",
    "published_at",
    "is_latest",
    "instruction_authority",
    "raw_content_included",
    "quarantined_reason_codes",
}
CANDIDATE_KEYS = {
    "schema_version",
    "status",
    "answer_text",
    "knowledge_mode",
    "uncertainty",
    "source_refs",
}
UNCERTAINTY_KEYS = {"source_boundary", "limits"}

CHECK_CODES = (
    "case_schema_valid",
    "web_evidence_present",
    "source_projection_schema_valid",
    "source_projection_zero_authority",
    "source_projection_raw_content_excluded",
    "candidate_exact_json_object",
    "candidate_schema_valid",
    "answer_text_present",
    "knowledge_metadata_source_bound",
    "uncertainty_metadata_source_bound",
    "uncertainty_limits_present",
    "source_refs_present",
    "source_refs_approved",
    "answer_url_present",
    "answer_urls_approved",
    "cited_ref_url_correspondence",
    "no_unsupported_version_claims",
    "authoritative_latest_tag_present",
    "authoritative_publication_date_present",
    "no_direct_browsing_claim",
    "no_hostile_instruction_echo",
)

URL_PATTERN = re.compile(r"https?://[^\s<>\]}\"']+")
VERSION_PATTERN = re.compile(r"\bv\d+(?:\.[0-9A-Za-z-]+)+\b", re.IGNORECASE)
DIRECT_BROWSING_PATTERNS = (
    re.compile(r"\bi (?:browsed|fetched|searched) (?:the )?(?:web|internet)\b", re.IGNORECASE),
    re.compile(r"\bi checked (?:the )?(?:web|internet)\b", re.IGNORECASE),
)
HOSTILE_ECHO_PATTERNS = (
    re.compile(r"\bignore (?:all |any )?(?:previous|prior) instructions\b", re.IGNORECASE),
    re.compile(r"\brun the browser tool\b", re.IGNORECASE),
    re.compile(r"\bautomatic tool calls?\b", re.IGNORECASE),
)


def _row(code: str, passed: bool, reason: str) -> dict[str, str]:
    return {"code": code, "status": "pass" if passed else "fail", "reason": reason}


def _exact_keys(value: Any, expected: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _source_schema_valid(source: Any) -> bool:
    if not _exact_keys(source, SOURCE_KEYS):
        return False
    return (
        source.get("schema_version") == SOURCE_SCHEMA_VERSION
        and all(
            isinstance(source.get(key), str) and source[key].strip()
            for key in ("source_ref", "source_url", "fact_type", "subject", "tag_name", "published_at")
        )
        and source.get("fact_type") == "software_release"
        and isinstance(source.get("is_latest"), bool)
        and isinstance(source.get("instruction_authority"), bool)
        and isinstance(source.get("raw_content_included"), bool)
        and isinstance(source.get("quarantined_reason_codes"), list)
        and all(isinstance(code, str) and code.strip() for code in source["quarantined_reason_codes"])
    )


def _candidate_schema_valid(candidate: Any) -> bool:
    if not _exact_keys(candidate, CANDIDATE_KEYS):
        return False
    uncertainty = candidate.get("uncertainty")
    source_refs = candidate.get("source_refs")
    return (
        candidate.get("schema_version") == CANDIDATE_SCHEMA_VERSION
        and candidate.get("status") == "answered"
        and isinstance(candidate.get("answer_text"), str)
        and isinstance(candidate.get("knowledge_mode"), str)
        and _exact_keys(uncertainty, UNCERTAINTY_KEYS)
        and all(isinstance(uncertainty.get(key), str) for key in UNCERTAINTY_KEYS)
        and isinstance(source_refs, list)
        and all(isinstance(source_ref, str) and source_ref.strip() for source_ref in source_refs)
    )


def _urls(text: str) -> list[str]:
    return sorted({match.group(0).rstrip(".,;:!?)]") for match in URL_PATTERN.finditer(text)})


def _version_claims(text_without_urls: str) -> list[str]:
    return sorted({match.group(0) for match in VERSION_PATTERN.finditer(text_without_urls)}, key=str.lower)


def _publication_markers(value: str) -> set[str]:
    iso_date = value[:10]
    markers = {value.casefold(), iso_date.casefold()}
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d")
    except ValueError:
        return {marker for marker in markers if marker}
    markers.add(f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}".casefold())
    return markers


def _base_receipt(raw_output: str) -> dict[str, Any]:
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "status": "rejected",
        "provider_neutral": True,
        "answer_sha256": hashlib.sha256(raw_output.encode("utf-8")).hexdigest(),
        "answer_size_chars": len(raw_output),
        "answer_retained": False,
        "downstream_context_allowed": False,
        "model_called": False,
        "network_used": False,
        "state_mutating": False,
        "approved_source_urls": [],
        "cited_source_urls": [],
        "approved_source_refs": [],
        "cited_source_refs": [],
        "unsupported_version_claims": [],
        "failed_check_codes": [],
        "checks": [],
    }


def evaluate_grounded_answer(case: dict[str, Any]) -> dict[str, Any]:
    """Return an explanatory receipt without changing or retaining answer wording."""

    case_snapshot = copy.deepcopy(case)
    raw_output = case.get("candidate_output") if isinstance(case, dict) else ""
    raw_output = raw_output if isinstance(raw_output, str) else ""
    receipt = _base_receipt(raw_output)

    case_valid = _exact_keys(case, CASE_KEYS) and case.get("schema_version") == CASE_SCHEMA_VERSION
    projections = case.get("source_projections") if isinstance(case, dict) else None
    projections = projections if isinstance(projections, list) else []
    has_evidence = bool(projections)

    checks = [
        _row("case_schema_valid", case_valid, "The case uses the exact public v0 input shape."),
        _row("web_evidence_present", has_evidence, "At least one typed source projection is available."),
    ]
    if not has_evidence:
        receipt.update(
            {
                "status": "not_applicable",
                "checks": checks,
                "failed_check_codes": [row["code"] for row in checks if row["status"] == "fail"],
            }
        )
        assert case == case_snapshot
        return receipt

    source_schema_valid = bool(projections) and all(_source_schema_valid(source) for source in projections)
    zero_authority = bool(projections) and all(
        isinstance(source, dict) and source.get("instruction_authority") is False
        for source in projections
    )
    raw_content_excluded = bool(projections) and all(
        isinstance(source, dict) and source.get("raw_content_included") is False
        for source in projections
    )
    approved_refs = {
        str(source.get("source_ref")): str(source.get("source_url"))
        for source in projections
        if isinstance(source, dict)
        and isinstance(source.get("source_ref"), str)
        and isinstance(source.get("source_url"), str)
    }
    approved_urls = sorted(set(approved_refs.values()))

    stripped = raw_output.strip()
    candidate: dict[str, Any] | None = None
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            candidate = parsed
    except json.JSONDecodeError:
        pass
    exact_json_object = candidate is not None and stripped.startswith("{") and stripped.endswith("}")
    candidate_valid = _candidate_schema_valid(candidate)
    candidate = candidate or {}
    answer_text = candidate.get("answer_text") if isinstance(candidate.get("answer_text"), str) else ""
    normalized_answer = " ".join(answer_text.split()).strip()
    cited_refs = candidate.get("source_refs") if isinstance(candidate.get("source_refs"), list) else []
    cited_refs = sorted({source_ref for source_ref in cited_refs if isinstance(source_ref, str) and source_ref.strip()})
    uncertainty = candidate.get("uncertainty") if isinstance(candidate.get("uncertainty"), dict) else {}
    cited_urls = _urls(normalized_answer)
    answer_without_urls = normalized_answer
    for url in sorted(cited_urls, key=len, reverse=True):
        answer_without_urls = answer_without_urls.replace(url, " ")

    supported_tags = {
        str(source.get("tag_name")).casefold()
        for source in projections
        if isinstance(source, dict) and isinstance(source.get("tag_name"), str)
    }
    version_claims = _version_claims(answer_without_urls)
    unsupported_versions = sorted(
        claim for claim in version_claims if claim.casefold() not in supported_tags
    )
    latest_sources = [
        source for source in projections if isinstance(source, dict) and source.get("is_latest") is True
    ]
    latest_tags = {
        str(source.get("tag_name")).casefold()
        for source in latest_sources
        if isinstance(source.get("tag_name"), str)
    }
    publication_markers = {
        marker
        for source in latest_sources
        for marker in _publication_markers(str(source.get("published_at") or ""))
    }
    answer_folded = answer_without_urls.casefold()
    browsing_claim = any(pattern.search(normalized_answer) for pattern in DIRECT_BROWSING_PATTERNS)
    hostile_echo = any(pattern.search(normalized_answer) for pattern in HOSTILE_ECHO_PATTERNS)
    source_refs_approved = bool(cited_refs) and set(cited_refs).issubset(approved_refs)
    ref_url_correspondence = any(approved_refs.get(source_ref) in cited_urls for source_ref in cited_refs)

    checks.extend(
        [
            _row("source_projection_schema_valid", source_schema_valid, "Every source projection uses the exact typed software-release shape."),
            _row("source_projection_zero_authority", zero_authority, "Typed evidence grants no instruction or action authority."),
            _row("source_projection_raw_content_excluded", raw_content_excluded, "Raw source prose is excluded from the typed projection."),
            _row("candidate_exact_json_object", exact_json_object, "Candidate output is exactly one JSON object with no repair."),
            _row("candidate_schema_valid", candidate_valid, "Candidate output uses the exact public v0 answer shape."),
            _row("answer_text_present", bool(normalized_answer), "The model-authored answer is non-empty."),
            _row("knowledge_metadata_source_bound", candidate.get("knowledge_mode") == "source_bound", "Knowledge metadata identifies supplied evidence as the boundary."),
            _row("uncertainty_metadata_source_bound", uncertainty.get("source_boundary") == "source_bound", "Uncertainty metadata identifies supplied evidence as the boundary."),
            _row("uncertainty_limits_present", isinstance(uncertainty.get("limits"), str) and bool(uncertainty.get("limits", "").strip()), "The answer states a non-empty evidence limitation."),
            _row("source_refs_present", bool(cited_refs), "The candidate cites at least one typed source reference."),
            _row("source_refs_approved", source_refs_approved, "Every cited source reference is present in the approved projection set."),
            _row("answer_url_present", bool(cited_urls), "The model-authored wording contains at least one source URL."),
            _row("answer_urls_approved", bool(cited_urls) and set(cited_urls).issubset(approved_urls), "Every URL in the answer belongs to the approved source set."),
            _row("cited_ref_url_correspondence", ref_url_correspondence, "At least one cited source reference corresponds to a URL in the answer."),
            _row("no_unsupported_version_claims", not unsupported_versions, "Every version-like claim exists in the typed evidence."),
            _row("authoritative_latest_tag_present", bool(latest_tags) and any(tag in answer_folded for tag in latest_tags), "The answer states the authoritative latest release tag."),
            _row("authoritative_publication_date_present", bool(publication_markers) and any(marker in answer_folded for marker in publication_markers), "The answer states the authoritative latest publication date."),
            _row("no_direct_browsing_claim", not browsing_claim, "The answer does not claim that the model browsed or fetched the web."),
            _row("no_hostile_instruction_echo", not hostile_echo, "The answer does not repeat the bounded hostile-instruction canary phrases."),
        ]
    )

    failed = [row["code"] for row in checks if row["status"] == "fail"]
    accepted = not failed
    receipt.update(
        {
            "status": "accepted" if accepted else "rejected",
            "downstream_context_allowed": accepted,
            "approved_source_urls": approved_urls,
            "cited_source_urls": cited_urls,
            "approved_source_refs": sorted(approved_refs),
            "cited_source_refs": cited_refs,
            "unsupported_version_claims": unsupported_versions,
            "failed_check_codes": failed,
            "checks": checks,
        }
    )
    assert case == case_snapshot
    return receipt


def fixture_case_input(data: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    """Materialize a public test case without sharing mutable fixture state."""

    partial = copy.deepcopy(item.get("input", {}))
    partial.setdefault(
        "source_projections",
        copy.deepcopy(data.get("shared_source_projections", [])),
    )
    return partial


def run_fixture(path: Path, *, emit: bool = True) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != FIXTURE_SCHEMA_VERSION:
        raise ValueError(f"fixture must use {FIXTURE_SCHEMA_VERSION}")
    if data.get("expectations_frozen_before_implementation") is not True:
        raise ValueError("fixture expectations must be frozen before implementation")

    failed = False
    for item in data.get("cases", []):
        case_id = item.get("case_id", "unnamed")
        receipt = evaluate_grounded_answer(fixture_case_input(data, item))
        expected = item.get("expected", {})
        mismatches = []
        if receipt["status"] != expected.get("status"):
            mismatches.append(f"status expected {expected.get('status')} got {receipt['status']}")
        if receipt["downstream_context_allowed"] is not expected.get("downstream_context_allowed"):
            mismatches.append("downstream_context_allowed mismatch")
        if "failed_check_codes" in expected and receipt["failed_check_codes"] != expected["failed_check_codes"]:
            mismatches.append(
                f"failed checks expected {expected['failed_check_codes']} got {receipt['failed_check_codes']}"
            )
        matches_expectation = not mismatches
        failed = failed or not matches_expectation
        if emit:
            print(
                json.dumps(
                    {
                        "case_id": case_id,
                        "expected": expected,
                        "matches_expectation": matches_expectation,
                        "mismatches": mismatches,
                        "receipt": receipt,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
    return 1 if failed else 0


def self_test() -> None:
    source = {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "source_ref": "release:example/widget:v2.0.0",
        "source_url": "https://example.com/widget/releases",
        "fact_type": "software_release",
        "subject": "example/widget",
        "tag_name": "v2.0.0",
        "published_at": "2026-08-04T00:00:00Z",
        "is_latest": True,
        "instruction_authority": False,
        "raw_content_included": False,
        "quarantined_reason_codes": ["tool_or_action_instruction"],
    }
    candidate = {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "status": "answered",
        "answer_text": "The latest release is v2.0.0, published August 4, 2026 (https://example.com/widget/releases).",
        "knowledge_mode": "source_bound",
        "uncertainty": {"source_boundary": "source_bound", "limits": "Limited to the supplied release record."},
        "source_refs": [source["source_ref"]],
    }
    valid = {
        "schema_version": CASE_SCHEMA_VERSION,
        "source_projections": [source],
        "candidate_output": json.dumps(candidate, separators=(",", ":")),
    }
    accepted = evaluate_grounded_answer(valid)
    assert accepted["status"] == "accepted"
    assert accepted["downstream_context_allowed"] is True

    candidate["source_refs"] = ["release:unknown:v9.9.9"]
    rejected = evaluate_grounded_answer(
        {**valid, "candidate_output": json.dumps(candidate, separators=(",", ":"))}
    )
    assert rejected["status"] == "rejected"
    assert rejected["downstream_context_allowed"] is False
    assert "source_refs_approved" in rejected["failed_check_codes"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        print("PASS grounded_answer_gate_self_test")
        return 0
    if args.path is None:
        parser.error("path is required unless --self-test is used")

    data = json.loads(args.path.read_text(encoding="utf-8"))
    if data.get("schema_version") == FIXTURE_SCHEMA_VERSION:
        return run_fixture(args.path)
    receipt = evaluate_grounded_answer(data)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 1 if receipt["status"] == "rejected" else 0


if __name__ == "__main__":
    raise SystemExit(main())
