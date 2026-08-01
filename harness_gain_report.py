#!/usr/bin/env python3
"""Decompose synthetic bare-versus-harness results without claiming a winner."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any


FIXTURE_SCHEMA = "harness_gain_fixture_v0"
REPORT_SCHEMA = "harness_gain_report_v0"
ARM_IDS = ("bare_model", "guided_harness")
ROOT_FIELDS = {
    "schema_version",
    "fixture_id",
    "model_called",
    "network_used",
    "state_mutating",
    "arms",
    "cases",
}
CASE_FIELDS = {"case_id", "sequence", "expected_transition", "arms"}
ARM_FIELDS = {
    "attempt_status",
    "assessment_status",
    "response_contract_status",
    "semantic_status",
    "behavior_status",
    "authority_expected",
    "authority_actual",
    "authority_contract_status",
    "operational_effect_status",
    "raw_contract_status",
    "adapted_contract_status",
}
PASS_FAIL = {"pass", "fail"}
AUTHORITY_VALUES = {"inert", "refused"}
TRANSITIONS = (
    "shared_pass",
    "output_discipline_recovery",
    "semantic_improvement",
    "behavioral_improvement",
    "regression",
    "shared_failure",
    "authority_stop",
    "unattempted_remaining",
    "mixed_change",
)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_fixture(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("fixture must be a JSON object")
    return value


def _check_exact_fields(value: dict[str, Any], expected: set[str], path: str, errors: list[str]) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
    if unknown:
        errors.append(f"{path}: unknown fields: {', '.join(unknown)}")


def _validate_assessed_arm(arm: dict[str, Any], path: str, errors: list[str]) -> None:
    if arm.get("attempt_status") != "completed":
        errors.append(f"{path}.attempt_status must be completed")
    if arm.get("assessment_status") != "assessed":
        errors.append(f"{path}.assessment_status must be assessed")

    for field in ("response_contract_status", "semantic_status", "behavior_status", "raw_contract_status"):
        if arm.get(field) not in PASS_FAIL:
            errors.append(f"{path}.{field} must be pass or fail")

    adapted = arm.get("adapted_contract_status")
    if adapted not in PASS_FAIL | {"not_used"}:
        errors.append(f"{path}.adapted_contract_status must be pass, fail, or not_used")
    elif adapted == "not_used" and arm.get("response_contract_status") != arm.get("raw_contract_status"):
        errors.append(f"{path}: effective contract status must equal raw status when no adapter is used")
    elif adapted in PASS_FAIL and arm.get("response_contract_status") != adapted:
        errors.append(f"{path}: effective contract status must equal the adapted status")

    expected = arm.get("authority_expected")
    actual = arm.get("authority_actual")
    if expected not in AUTHORITY_VALUES:
        errors.append(f"{path}.authority_expected must be inert or refused")
    if actual not in AUTHORITY_VALUES:
        errors.append(f"{path}.authority_actual must be inert or refused")
    authority_status = arm.get("authority_contract_status")
    if authority_status not in PASS_FAIL:
        errors.append(f"{path}.authority_contract_status must be pass or fail")
    elif expected in AUTHORITY_VALUES and actual in AUTHORITY_VALUES:
        required = "pass" if expected == actual else "fail"
        if authority_status != required:
            errors.append(f"{path}.authority_contract_status must be {required} for the declared dispositions")

    if arm.get("operational_effect_status") not in {"none", "attempted", "performed"}:
        errors.append(f"{path}.operational_effect_status must be none, attempted, or performed")


def _validate_unattempted_arm(arm: dict[str, Any], path: str, errors: list[str]) -> None:
    if arm.get("attempt_status") != "not_attempted":
        errors.append(f"{path}.attempt_status must be not_attempted after an integrity stop")
    if arm.get("assessment_status") != "not_assessed_integrity_stop":
        errors.append(f"{path}.assessment_status must be not_assessed_integrity_stop")
    for field in (
        "response_contract_status",
        "semantic_status",
        "behavior_status",
        "authority_expected",
        "authority_actual",
        "authority_contract_status",
        "operational_effect_status",
        "raw_contract_status",
        "adapted_contract_status",
    ):
        if arm.get(field) != "not_assessed":
            errors.append(f"{path}.{field} must be not_assessed after an integrity stop")


def _overall_pass(arm: dict[str, Any]) -> bool:
    return all(
        arm.get(field) == "pass"
        for field in (
            "response_contract_status",
            "semantic_status",
            "behavior_status",
            "authority_contract_status",
        )
    )


def classify_transition(case: dict[str, Any]) -> str:
    arms = case.get("arms", {})
    bare = arms.get(ARM_IDS[0], {})
    harness = arms.get(ARM_IDS[1], {})
    attempts = {bare.get("attempt_status"), harness.get("attempt_status")}
    if attempts == {"not_attempted"}:
        return "unattempted_remaining"
    if "fail" in {bare.get("authority_contract_status"), harness.get("authority_contract_status")}:
        return "authority_stop"

    bare_pass = _overall_pass(bare)
    harness_pass = _overall_pass(harness)
    if bare_pass and harness_pass:
        return "shared_pass"
    if (
        bare.get("response_contract_status") == "fail"
        and bare.get("semantic_status") == "pass"
        and bare.get("behavior_status") == "pass"
        and bare.get("authority_contract_status") == "pass"
        and harness_pass
    ):
        return "output_discipline_recovery"
    if (
        bare.get("response_contract_status") == "pass"
        and bare.get("semantic_status") == "fail"
        and bare.get("behavior_status") == "pass"
        and bare.get("authority_contract_status") == "pass"
        and harness_pass
    ):
        return "semantic_improvement"
    if (
        bare.get("response_contract_status") == "pass"
        and bare.get("semantic_status") == "pass"
        and bare.get("behavior_status") == "fail"
        and bare.get("authority_contract_status") == "pass"
        and harness_pass
    ):
        return "behavioral_improvement"
    if bare_pass and not harness_pass:
        return "regression"
    if not bare_pass and not harness_pass:
        return "shared_failure"
    return "mixed_change"


def validate_fixture(fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _check_exact_fields(fixture, ROOT_FIELDS, "fixture", errors)
    if fixture.get("schema_version") != FIXTURE_SCHEMA:
        errors.append(f"fixture.schema_version must be {FIXTURE_SCHEMA}")
    if not isinstance(fixture.get("fixture_id"), str) or not fixture.get("fixture_id", "").strip():
        errors.append("fixture.fixture_id must be non-empty text")
    for field in ("model_called", "network_used", "state_mutating"):
        if fixture.get(field) is not False:
            errors.append(f"fixture.{field} must be false for this no-model example")
    if fixture.get("arms") != list(ARM_IDS):
        errors.append(f"fixture.arms must be {list(ARM_IDS)}")

    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("fixture.cases must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    stop_seen = False
    for index, case in enumerate(cases, start=1):
        path = f"fixture.cases[{index - 1}]"
        if not isinstance(case, dict):
            errors.append(f"{path} must be an object")
            continue
        _check_exact_fields(case, CASE_FIELDS, path, errors)
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{path}.case_id must be non-empty text")
        elif case_id in seen_ids:
            errors.append(f"{path}.case_id is duplicated: {case_id}")
        else:
            seen_ids.add(case_id)
        if case.get("sequence") != index:
            errors.append(f"{path}.sequence must be {index}")
        if case.get("expected_transition") not in TRANSITIONS:
            errors.append(f"{path}.expected_transition is invalid")

        arms = case.get("arms")
        if not isinstance(arms, dict):
            errors.append(f"{path}.arms must be an object")
            continue
        if set(arms) != set(ARM_IDS):
            errors.append(f"{path}.arms must contain exactly {', '.join(ARM_IDS)}")
            continue

        attempts = set()
        arms_valid = True
        for arm_id in ARM_IDS:
            arm = arms[arm_id]
            arm_path = f"{path}.arms.{arm_id}"
            if not isinstance(arm, dict):
                errors.append(f"{arm_path} must be an object")
                arms_valid = False
                continue
            _check_exact_fields(arm, ARM_FIELDS, arm_path, errors)
            attempts.add(arm.get("attempt_status"))
        if not arms_valid:
            continue
        if len(attempts) != 1:
            errors.append(f"{path}: both arms must have the same attempt status")
            continue

        not_attempted = attempts == {"not_attempted"}
        for arm_id in ARM_IDS:
            arm = arms[arm_id]
            arm_path = f"{path}.arms.{arm_id}"
            if not isinstance(arm, dict):
                continue
            if not_attempted:
                _validate_unattempted_arm(arm, arm_path, errors)
            else:
                _validate_assessed_arm(arm, arm_path, errors)

        transition = classify_transition(case)
        if transition != case.get("expected_transition"):
            errors.append(
                f"{path}: expected transition {case.get('expected_transition')}, computed {transition}"
            )
        if stop_seen and transition != "unattempted_remaining":
            errors.append(f"{path}: no arm may be attempted after an authority integrity stop")
        if not stop_seen and transition == "unattempted_remaining":
            errors.append(f"{path}: an unattempted row requires an earlier authority integrity stop")
        if transition == "authority_stop":
            stop_seen = True
    return errors


def build_report(fixture: dict[str, Any]) -> dict[str, Any]:
    errors = validate_fixture(fixture)
    if errors:
        return {
            "schema_version": REPORT_SCHEMA,
            "fixture_id": fixture.get("fixture_id"),
            "record_valid": False,
            "execution_integrity_status": "fail",
            "claim_eligibility": {
                "status": "invalid_record",
                "material_gain": "not_assessed_invalid_record",
            },
            "errors": errors,
        }

    cases = fixture["cases"]
    transitions = [classify_transition(case) for case in cases]
    transition_counts = Counter(transitions)
    stop_index = next((index for index, item in enumerate(transitions) if item == "authority_stop"), None)
    assessed = [case for case, transition in zip(cases, transitions) if transition != "unattempted_remaining"]
    unassessed_count = len(cases) - len(assessed)

    arm_metrics: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        rows = [case["arms"][arm_id] for case in assessed]
        arm_metrics[arm_id] = {
            "assessed_case_count": len(rows),
            "full_pass_count": sum(_overall_pass(row) for row in rows),
            "response_contract_pass_count": sum(row["response_contract_status"] == "pass" for row in rows),
            "semantic_pass_count": sum(row["semantic_status"] == "pass" for row in rows),
            "behavior_pass_count": sum(row["behavior_status"] == "pass" for row in rows),
            "authority_contract_failure_count": sum(row["authority_contract_status"] == "fail" for row in rows),
            "raw_contract_pass_count": sum(row["raw_contract_status"] == "pass" for row in rows),
            "adapted_output_used_count": sum(row["adapted_contract_status"] != "not_used" for row in rows),
            "adapted_contract_pass_count": sum(row["adapted_contract_status"] == "pass" for row in rows),
            "adapted_contract_failure_count": sum(row["adapted_contract_status"] == "fail" for row in rows),
            "operational_effect_counts": dict(
                Counter(row["operational_effect_status"] for row in rows)
            ),
        }

    stopped = stop_index is not None
    return {
        "schema_version": REPORT_SCHEMA,
        "fixture_id": fixture["fixture_id"],
        "record_valid": True,
        "execution_integrity_status": "pass_fail_closed" if stopped else "pass_complete",
        "comparison": {
            "scheduled_case_count": len(cases),
            "assessed_pair_count": len(assessed),
            "unassessed_integrity_stop_count": unassessed_count,
            "complete": not stopped,
            "stop_reason": "authority_contract_failure" if stopped else None,
            "stop_case_id": cases[stop_index]["case_id"] if stopped else None,
        },
        "transition_counts": {transition: transition_counts.get(transition, 0) for transition in TRANSITIONS},
        "arms": arm_metrics,
        "claim_eligibility": {
            "status": "not_eligible_integrity_stop" if stopped else "eligible_for_descriptive_comparison",
            "material_gain": "not_assessed_integrity_stop" if stopped else "not_claimed",
            "reason": (
                "The record stopped correctly after an authority-contract failure, so later rows are unassessed."
                if stopped
                else "All scheduled pairs were assessed; any gain claim still needs an independently justified rubric."
            ),
        },
        "activity": {
            "model_called": fixture["model_called"],
            "network_used": fixture["network_used"],
            "state_mutating": fixture["state_mutating"],
        },
        "errors": [],
    }


def print_report(report: dict[str, Any], label: str) -> None:
    if not report["record_valid"]:
        print(f"FAIL harness_gain_fixture {label}")
        for error in report["errors"]:
            print(f"  - {error}")
        return
    comparison = report["comparison"]
    print(f"PASS harness_gain_fixture {label}")
    print(f"execution_integrity {report['execution_integrity_status']}")
    print(
        "comparison "
        f"{comparison['assessed_pair_count']}/{comparison['scheduled_case_count']} assessed; "
        f"{comparison['unassessed_integrity_stop_count']} not_assessed_integrity_stop"
    )
    print(f"claim_eligibility {report['claim_eligibility']['status']}")
    print(f"material_gain {report['claim_eligibility']['material_gain']}")
    for transition in TRANSITIONS:
        count = report["transition_counts"][transition]
        if count:
            print(f"transition {transition}={count}")


def default_fixture_path() -> Path:
    return Path(__file__).with_name("examples") / "harness_gain_cases.json"


def self_test() -> None:
    fixture = load_fixture(default_fixture_path())
    report = build_report(fixture)
    assert report["record_valid"] is True
    assert report["execution_integrity_status"] == "pass_fail_closed"
    assert report["claim_eligibility"]["material_gain"] == "not_assessed_integrity_stop"
    expected = {
        "shared_pass",
        "output_discipline_recovery",
        "semantic_improvement",
        "behavioral_improvement",
        "regression",
        "shared_failure",
        "authority_stop",
        "unattempted_remaining",
    }
    assert {key for key, count in report["transition_counts"].items() if count} == expected
    assert all(report["transition_counts"][key] == 1 for key in expected)
    print("PASS public_fixture")
    print("PASS transition_taxonomy")
    print("PASS fail_closed_stop")

    attempted_after_stop = copy.deepcopy(fixture)
    attempted_after_stop["cases"][-1] = copy.deepcopy(attempted_after_stop["cases"][0])
    attempted_after_stop["cases"][-1]["case_id"] = "attempted_after_stop"
    attempted_after_stop["cases"][-1]["sequence"] = 8
    attempted_after_stop["cases"][-1]["expected_transition"] = "shared_pass"
    attempted_report = build_report(attempted_after_stop)
    assert attempted_report["record_valid"] is False
    assert any(
        "no arm may be attempted after an authority integrity stop" in error
        for error in attempted_report["errors"]
    )
    print("PASS post_stop_attempt_rejected")

    adapted_output = copy.deepcopy(fixture)
    adapted_arm = adapted_output["cases"][0]["arms"][ARM_IDS[1]]
    adapted_arm["raw_contract_status"] = "fail"
    adapted_arm["adapted_contract_status"] = "pass"
    adapted_report = build_report(adapted_output)
    assert adapted_report["record_valid"] is True
    assert adapted_report["arms"][ARM_IDS[1]]["raw_contract_pass_count"] == 6
    assert adapted_report["arms"][ARM_IDS[1]]["response_contract_pass_count"] == 7
    assert adapted_report["arms"][ARM_IDS[1]]["adapted_output_used_count"] == 1
    assert adapted_report["arms"][ARM_IDS[1]]["adapted_contract_pass_count"] == 1
    print("PASS raw_adapted_separation")

    wrong_reason = copy.deepcopy(fixture)
    wrong_reason["cases"][-1]["arms"][ARM_IDS[1]]["assessment_status"] = "not_assessed_runtime_failure"
    wrong_reason_report = build_report(wrong_reason)
    assert wrong_reason_report["record_valid"] is False
    assert any(
        "assessment_status must be not_assessed_integrity_stop" in error
        for error in wrong_reason_report["errors"]
    )
    print("PASS post_stop_reason_enforced")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("PASS self_test")
        return 0
    if not args.path:
        parser.error("path is required unless --self-test is used")
    try:
        fixture = load_fixture(Path(args.path))
    except ValueError as exc:
        print(f"FAIL harness_gain_fixture: {exc}")
        return 1
    report = build_report(fixture)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report, Path(args.path).name)
    return 0 if report["record_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
