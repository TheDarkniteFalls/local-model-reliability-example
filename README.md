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
python3 reliability_demo.py --self-test
```

Expected result:

```text
PASS helpful_summary
PASS ask_for_source
```

## Contract

Each model output must contain:

- `answer`: non-empty text.
- `action`: one of `summarize`, `route`, or `ask_clarifying_question`.
- `confidence`: a number from `0` to `1`.
- `citations`: source IDs from the current case.
- `writes`: an empty list.

## Public Data Notice

All examples are synthetic. Do not add private prompts, real assistant logs,
connector exports, credentials, or personal data.

## Quality Checks

```sh
python3 reliability_demo.py --self-test
python3 reliability_demo.py examples/model_outputs.jsonl
python3 -m py_compile reliability_demo.py
```
