# Local Model Reliability Example

A tiny, synthetic example of the pattern: model proposes, application
validates.

The demo does not call a model. It reads sample local-model output, parses the
structured JSON, checks citations against the supplied source IDs, and rejects
write requests. This keeps the example deterministic and public-safe.

## Why It Exists

Small models can be useful, but their output should not be trusted just because
it looks confident. This repo shows a simple boundary: the model may propose an
answer, but the application validates shape, citations, confidence, and write
permissions before doing anything with it.

## Run

```sh
python3 reliability_demo.py examples/model_outputs.jsonl
python3 structured_output_canary.py examples/canary_outputs.jsonl
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

## Contract

Each model output must contain:

- `answer`: non-empty text.
- `action`: one of `summarize`, `route`, or `ask_clarifying_question`.
- `confidence`: a number from `0` to `1`.
- `citations`: source IDs from the current case.
- `writes`: an empty list.

## Structured Output Canary

`structured_output_canary.py` checks expected pass/fail cases against the same
contract used by the demo. It is useful when prompt or model changes might
silently drift away from the JSON shape the application expects.

The fixture in `examples/canary_outputs.jsonl` includes one valid output and
three expected failures: unknown citation, write request, and non-JSON text.

## How These Fit Together

Local Model Reliability Example is one piece of a small public toolkit:

- [Public Repo Safety Kit](https://github.com/TheDarkniteFalls/public-repo-safety-kit)
  checks a public-candidate repo before publishing.
- [EvidenceGate](https://github.com/TheDarkniteFalls/evidencegate) records the
  evidence and checks behind an AI-assisted change.
- Local Model Reliability Example validates structured model output before
  trusting it.
- [Context Boundary Examples](https://github.com/TheDarkniteFalls/context-boundary-examples)
  checks whether an answer stays inside supplied evidence.
- [Green-Spine QA Pattern](https://github.com/TheDarkniteFalls/green-spine-qa-pattern)
  bundles the important path behind one repeatable command.

## Public Data Notice

All examples are synthetic. Do not add private prompts, real assistant logs,
connector exports, credentials, or personal data.

## Quality Checks

```sh
python3 reliability_demo.py --self-test
python3 reliability_demo.py examples/model_outputs.jsonl
python3 structured_output_canary.py --self-test
python3 structured_output_canary.py examples/canary_outputs.jsonl
python3 -m py_compile reliability_demo.py
python3 -m py_compile structured_output_canary.py
```
