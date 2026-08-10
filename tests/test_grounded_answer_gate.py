#!/usr/bin/env python3
"""Deterministic contracts for the Citeglass Grounded Answer Gate."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from grounded_answer_gate import (
    CHECK_CODES,
    FIXTURE_SCHEMA_VERSION,
    evaluate_grounded_answer,
    fixture_case_input,
    run_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "grounded_answer_cases.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class GroundedAnswerGateTests(unittest.TestCase):
    def test_fixture_is_frozen_and_complete(self) -> None:
        data = load_fixture()
        self.assertEqual(data["schema_version"], FIXTURE_SCHEMA_VERSION)
        self.assertIs(data["expectations_frozen_before_implementation"], True)
        self.assertGreaterEqual(len(data["cases"]), 13)
        self.assertEqual(run_fixture(FIXTURE, emit=False), 0)

    def test_every_declared_check_is_exercised(self) -> None:
        data = load_fixture()
        seen = set()
        failed = set()
        for item in data["cases"]:
            receipt = evaluate_grounded_answer(fixture_case_input(data, item))
            seen.update(row["code"] for row in receipt["checks"])
            failed.update(receipt["failed_check_codes"])
        self.assertEqual(seen, set(CHECK_CODES))
        self.assertEqual(failed, set(CHECK_CODES) - {"case_schema_valid"})

    def test_only_accepted_case_enters_downstream_context(self) -> None:
        data = load_fixture()
        allowed = []
        for item in data["cases"]:
            receipt = evaluate_grounded_answer(fixture_case_input(data, item))
            if receipt["downstream_context_allowed"]:
                allowed.append(item["case_id"])
            if receipt["status"] != "accepted":
                self.assertIs(receipt["downstream_context_allowed"], False)
        self.assertEqual(allowed, ["valid_source_bound_answer"])

    def test_receipt_does_not_retain_answer_text(self) -> None:
        data = load_fixture()
        for item in data["cases"]:
            case = fixture_case_input(data, item)
            receipt = evaluate_grounded_answer(case)
            serialized = json.dumps(receipt, sort_keys=True)
            self.assertNotIn("answer_text", receipt)
            self.assertNotIn(case["candidate_output"], serialized)
            self.assertIs(receipt["answer_retained"], False)
            self.assertIs(receipt["model_called"], False)
            self.assertIs(receipt["network_used"], False)
            self.assertIs(receipt["state_mutating"], False)

    def test_evaluation_does_not_mutate_input(self) -> None:
        data = load_fixture()
        case = fixture_case_input(data, data["cases"][0])
        original = copy.deepcopy(case)
        evaluate_grounded_answer(case)
        self.assertEqual(case, original)

    def test_malformed_output_is_not_repaired(self) -> None:
        data = load_fixture()
        item = next(case for case in data["cases"] if case["case_id"] == "malformed_structured_output")
        receipt = evaluate_grounded_answer(fixture_case_input(data, item))
        self.assertEqual(receipt["status"], "rejected")
        self.assertIn("candidate_exact_json_object", receipt["failed_check_codes"])
        self.assertFalse(receipt["downstream_context_allowed"])


if __name__ == "__main__":
    unittest.main()
