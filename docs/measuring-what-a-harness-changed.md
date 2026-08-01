# Measuring What a Harness Changed

A higher strict pass count does not answer one question. It may mean the model
reasoned better, but it may also mean that an existing answer became valid
JSON, included required envelope fields, cited the supplied source, selected a
tool in the required shape, or handled an ambiguity more safely.

Those are all useful outcomes. They should not be presented as the same kind
of improvement.

This repository includes a deterministic synthetic report that keeps the
differences visible:

```sh
python3 -B harness_gain_report.py examples/harness_gain_cases.json
python3 -B harness_gain_report.py examples/harness_gain_cases.json --json
python3 -B harness_gain_report.py --self-test
```

It calls no model, uses no network service, and changes no application state.
The fixture contains classifications only: no prompts, model responses,
private paths, benchmark answers, or live evaluation traces.

## The Separate Questions

Each arm records the following dimensions independently:

| Dimension | Question |
| --- | --- |
| Attempt and assessment | Was the case attempted, completed, and eligible for assessment? |
| Response contract | Did the effective output satisfy the required machine-readable shape? |
| Semantic quality | Was the substantive answer correct under the declared review? |
| Behavior | Did the answer clarify, abstain, refuse, or proceed as required? |
| Authority disposition | Did the output use the expected `inert` or `refused` disposition? |
| Operational effect | Was any action attempted or performed? |
| Raw and adapted output | Did the provider output pass directly, or did an explicit adapter supply the effective output? |
| Claim eligibility | Is the run complete and valid enough to support a comparison claim? |

This prevents two common overclaims:

- valid JSON is treated as proof of a better answer; or
- an incorrect authority label is described as an operational breach even
  when no tool, write, or other effect was attempted.

## The Eight Synthetic Cases

The bundled fixture demonstrates one instance of each important transition:

| Transition | Meaning |
| --- | --- |
| `shared_pass` | Both arms satisfy every assessed dimension. |
| `output_discipline_recovery` | The bare answer is substantively sound but breaks the response contract; the harness answer is directly machine-usable. |
| `semantic_improvement` | Both outputs satisfy the contract, but only the harness answer is substantively correct. |
| `behavioral_improvement` | Both answers are substantively correct, but only the harness follows the required ambiguity or boundary behavior. |
| `regression` | The bare arm passes and the harness arm does not. |
| `shared_failure` | Both arms fail an assessed requirement. |
| `authority_stop` | A disposition mismatch creates a fatal evaluation-integrity event, while operational effects remain separately recorded. |
| `unattempted_remaining` | A later scheduled case is retained but marked `not_assessed_integrity_stop` for both arms. |

The fixture deliberately stops after the authority failure. The report accepts
that record as honestly fail-closed, but reports:

```text
execution_integrity pass_fail_closed
claim_eligibility not_eligible_integrity_stop
material_gain not_assessed_integrity_stop
```

A valid record is not the same as a successful experiment. The transition
counts before the stop remain descriptive, while a material-gain claim remains
closed.

## Why Raw and Adapted Output Stay Separate

An adapter may make fenced or partial JSON parseable. That can be useful, but
the report must reveal it. For an assessed row:

- `raw_contract_status` records the provider output;
- `adapted_contract_status` is `not_used`, `pass`, or `fail`; and
- `response_contract_status` records the output actually judged by the
  application.

When no adapter is used, the effective status must equal the raw status. When
an adapter is used, the effective status must equal the adapted status. The
synthetic fixture uses no adapter, so its output-discipline recovery represents
generation-time conformance rather than hidden repair.

## Applying the Pattern to a Real Evaluation

1. Freeze the cases, arm differences, judge, failure classes, stop rules, and
   claim thresholds before observing model results.
2. Give both arms the same task inputs and generation budget.
3. Preserve raw output before any structural adaptation.
4. Record contract, semantic, behavioral, authority, and operational-effect
   evidence independently.
5. Stop on the first declared integrity-critical failure and retain every
   later scheduled row as `not_assessed_integrity_stop`.
6. Report transition counts before discussing aggregate gain.
7. Attribute improvement to a specific harness component only after a
   separately frozen ablation or intervention test.

For code tasks, diagnosis and repair should also be judged separately. A model
can understand the bug while proposing a faulty patch, or miss an exact rubric
term while explaining the mechanism correctly.

## What the Report Does Not Prove

The checker validates the supplied synthetic record and computes a transparent
decomposition. It does not call a model, authenticate the classifications,
judge factual truth, prove that two real requests were identical, provide a
sandbox, establish statistical significance, or authorize a model-route
change.

The operator or evaluation system remains responsible for independently
collecting truthful raw outputs, semantic reviews, authority evidence, and
operational-effect observations.
