# Local Model Reliability Example

Try small Python checks that accept or reject supplied example answers before
an application uses them. You can test citations, JSON structure and protected
files without installing or calling a model. All the examples are synthetic.

## Try The Grounded Answer Check

The experimental Citeglass Grounded Answer Gate checks one complete boundary:
typed source facts enter, a model-authored JSON answer is evaluated unchanged,
and only an answer with approved citations, truthful source metadata, supported
release facts, and zero instruction authority may enter downstream context.

With Python 3, run this from the repository root. The examples and their
expected decisions are fixed, so you can compare the result:

```sh
python3 grounded_answer_gate.py examples/grounded_answer_cases.json
```

The valid case is accepted. Missing citations, invented URLs or versions,
incorrect release facts, false metadata, browsing claims, hostile-instruction
echoes, raw source content, malformed JSON, and unknown fields are rejected.
Every result includes a machine-readable receipt from
`evaluate_grounded_answer(case)` with `downstream_context_allowed` set
explicitly. The fixture command emits one NDJSON record per case with that
receipt and its frozen expected decision. The gate hashes but does not retain
the answer text.

<!-- toolkit-trust-card:placement -->

<!-- toolkit-trust-card:start -->
> **Public contract:** Experimental pattern · about 5 min · Python 3 · no model · no network
>
> **Operation:** Read-only check; examples may use temporary files
>
> **A pass establishes:** The frozen synthetic cases accept only the source-bound answer and reject missing or unapproved citations, unsupported release facts, false metadata, hostile echoes, raw source content, and malformed shapes before downstream context is allowed.
>
> **It does not establish:** The gate calls no model or network, covers only the declared software-release fact profile and canaries, and does not establish source truth, general semantic correctness, live-model quality, or external adoption.
>
> **First check:** `python3 grounded_answer_gate.py examples/grounded_answer_cases.json`
<!-- toolkit-trust-card:end -->

Read [Prevent Ungrounded Web Answers From Entering Trusted Context](docs/prevent-ungrounded-web-answers.md)
for the integration shape, receipt interpretation, Gemma/LiteRT-LM placement,
threat boundary, and limitations.

The demo does not call a model. It reads sample local-model output, parses the
structured JSON, checks citations against the supplied source IDs, and rejects
write requests. This keeps the example deterministic and public-safe.

## What The Examples Show

An answer can look plausible while citing an unknown source or asking to write
a file it should not change. These checks give the application a way to reject
those outputs. A passing synthetic example shows that the declared rule worked
for that case; it does not show that a live model answers well or that a source
is true.

## Learn The Build Order

A harness is the code around a model that prepares inputs, checks outputs and
records results. If you are building your first one, read
[Build Your First Local Model Harness: From API Call to Evidence](docs/build-your-first-local-model-harness.md)
for a 20-to-30-minute walkthrough: check the response format, compare changed
files, and record what failed before considering a model comparison. It uses this repository's existing synthetic
checks and does not call a model or network service.

When a harness raises the pass count, use
[Measuring What a Harness Changed](docs/measuring-what-a-harness-changed.md)
to separate output-discipline recovery, semantic improvement, behavioral
improvement, regressions, authority stops, and claim eligibility.
For the downstream decision boundary, see [Claim Eligibility for Agent
Evaluations](docs/claim-eligibility-for-agent-evaluations.md), which keeps
evidence, eligible wording, and promotion authority separate.

## Try The Other Checks

```sh
python3 grounded_answer_gate.py examples/grounded_answer_cases.json
python3 reliability_demo.py examples/model_outputs.jsonl
python3 structured_output_canary.py examples/canary_outputs.jsonl
python3 protected_path_proof.py examples/protected_path_cases.jsonl
python3 harness_gain_report.py examples/harness_gain_cases.json
python3 reliability_demo.py --self-test
```

Expected result:

```text
PASS helpful_summary
PASS ask_for_source
```

Canary output:

```text
PASS valid_summary_with_citation
PASS invalid_unknown_citation
PASS invalid_write_request
PASS invalid_non_json
```

Protected-path output:

```text
PASS valid_expected_write_only
PASS invalid_unexpected_write
PASS invalid_protected_path_change
PASS invalid_missing_expected_write
```

## What An Answer Must Contain

Each model output must contain:

- `answer`: non-empty text.
- `action`: one of `summarize`, `route`, or `ask_clarifying_question`.
- `confidence`: a number from `0` to `1`.
- `citations`: source IDs from the current case.
- `writes`: an empty list.

The Grounded Answer Gate has a separate, narrower v0 contract. Its input is one
`citeglass_grounded_answer_case_v0` containing provider-neutral typed
`software_release` projections and the exact raw candidate JSON. Its receipt is
`citeglass_grounded_answer_receipt_v0` with stable pass/fail check codes,
approved and cited provenance, an answer hash and length, and the downstream
context decision. Unknown fields fail closed. No output repair or fallback
wrapping is allowed.

## Structured Output Canary

A canary is a small example that should pass or fail in a known way.
`structured_output_canary.py` checks these cases against the same
contract used by the demo. It is useful when prompt or model changes might
silently drift away from the JSON shape the application expects.

The fixture in `examples/canary_outputs.jsonl` includes one valid output and
three expected failures: unknown citation, write request, and non-JSON text.

## Protected-Path Proof

`protected_path_proof.py` compares synthetic before/after manifests. It checks
that only expected paths changed and that protected paths did not change.

Use this to check which paths a change affected. The supplied before/after
records are synthetic; they do not prove that a real process was contained.

## Harness Gain Decomposition

`harness_gain_report.py` checks a paired synthetic run without flattening
response-contract compliance, semantic quality, boundary behavior, authority
disposition, operational effects, or raw-versus-adapted output into one score.

The bundled run stops correctly after an authority-contract failure, preserves
the remaining scheduled case as `not_assessed_integrity_stop`, and leaves the
material-gain claim unassessed. A valid fail-closed record is therefore not
mistaken for a successful comparison.

## Related Tools

Choose a related example when you need to check another part of your workflow:

- [Public Repo Safety Kit](https://github.com/TheDarkniteFalls/public-repo-safety-kit)
  checks a public-candidate repo before publishing.
- [EvidenceGate](https://github.com/TheDarkniteFalls/evidencegate) records the
  evidence and checks behind an AI-assisted change.
- [Context Boundary Examples](https://github.com/TheDarkniteFalls/context-boundary-examples)
  checks whether an answer stays inside supplied evidence.
- [Green-Spine QA Pattern](https://github.com/TheDarkniteFalls/green-spine-qa-pattern)
  puts the checks for an important workflow behind one repeatable command.
- [Codex Project Instructions Starter](https://github.com/TheDarkniteFalls/codex-project-instructions-starter)
  gives coding agents clear project rules before they work.

## Public Data Notice

All examples are synthetic. Do not add private prompts, real assistant logs,
connector exports, credentials, or personal data.

## Quality Checks

```sh
python3 grounded_answer_gate.py --self-test
python3 grounded_answer_gate.py examples/grounded_answer_cases.json
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 reliability_demo.py --self-test
python3 reliability_demo.py examples/model_outputs.jsonl
python3 structured_output_canary.py --self-test
python3 structured_output_canary.py examples/canary_outputs.jsonl
python3 protected_path_proof.py --self-test
python3 protected_path_proof.py examples/protected_path_cases.jsonl
python3 harness_gain_report.py --self-test
python3 harness_gain_report.py examples/harness_gain_cases.json
python3 -m py_compile reliability_demo.py
python3 -m py_compile structured_output_canary.py
python3 -m py_compile protected_path_proof.py
python3 -m py_compile harness_gain_report.py
python3 -m py_compile grounded_answer_gate.py
```
