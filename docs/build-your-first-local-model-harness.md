# Build Your First Local Model Harness: From API Call to Evidence

This is a 20-to-30-minute guide for builders who can already get text back
from a local-model endpoint and want to make that response dependable. If you
do not have a running model yet, you can still complete every checkpoint with
the synthetic responses in this repository.

The guide does not install or call a model. It does not depend on a particular
server, provider, model family, or piece of hardware. Every local checkpoint
uses Python's standard library, makes no network request, and leaves tracked
repository files unchanged.

## The Core Idea

A response is not evidence that the whole system worked.

Treat model output as an untrusted proposal. Let the surrounding harness own
the context, validation, state boundary, evidence record, and any decision to
use a model for this kind of work again.

Use four separate evidence levels:

| Evidence level | Question | What a pass establishes | What it does not establish |
| --- | --- | --- | --- |
| Transport | Did the endpoint return a response? | The request reached a runtime and produced bytes or text. | The response is valid, grounded, useful, or safe. |
| Contract | Did the response satisfy the declared rules? | The supplied output passed shape, source, action, and state-boundary checks. | The answer is factually correct or helpful. |
| Utility | Did the answer solve the task well enough? | A task-specific evaluation or reviewer found the result useful. | Another model would not do better, or this route should become the default. |
| Promotion | Has this route earned continued use? | Repeated, matched evidence supports a reviewed routing decision. | Universal model superiority or safety outside the tested workload. |

Do not collapse these levels into one `success` flag. A server returning a
confident paragraph is transport evidence. It becomes contract evidence only
after validation, and it becomes utility evidence only after task-specific
evaluation.

## Get The Example

Clone the repository, then enter its root folder:

```sh
git clone https://github.com/TheDarkniteFalls/local-model-reliability-example.git
cd local-model-reliability-example
```

If you do not use Git, select **Code → Download ZIP** on the repository page,
extract it, and open a terminal in the extracted folder. Run every command
below from this repository root.

## Checkpoint Map

| Checkpoint | Command | Model called | Network used | Tracked files changed |
| --- | --- | --- | --- | --- |
| Validator self-test | `python3 -B reliability_demo.py --self-test` | No | No | No |
| Synthetic output validation | `python3 -B reliability_demo.py examples/model_outputs.jsonl` | No | No | No |
| Positive and negative canaries | `python3 -B structured_output_canary.py examples/canary_outputs.jsonl` | No | No | No |
| Expected-write proof | `python3 -B protected_path_proof.py examples/protected_path_cases.jsonl` | No | No | No |

The `-B` flag prevents Python from creating bytecode cache files. These checks
exercise the harness rules, not a live model.

## 1. Start At The API Boundary

Your first local-model call may prove several useful things:

- the server process is reachable;
- the request format is accepted;
- the chosen model can produce a response; and
- the runtime can finish one request under the current conditions.

That is transport evidence. Keep it, but label it honestly.

It does not yet tell you whether the response:

- follows the shape your application needs;
- cites only sources that were supplied;
- refuses when evidence is missing;
- tries to claim or request a write;
- answers the right question; or
- is good enough to justify this model's time and resource cost.

Before adding a chat interface or an agent loop, establish a deterministic
place to test those claims:

```sh
python3 -B reliability_demo.py --self-test
```

Expected output:

```text
self-test passed
```

This proves the validator accepts a known-good object and rejects at least one
known-bad object. It does not test a model endpoint.

## 2. Put The Harness In Charge

Keep the first architecture deliberately uneven: the model proposes; the
harness and operator decide.

| Part | Owns |
| --- | --- |
| Model | Generated wording or a structured proposal. |
| Harness | Approved context, requested output shape, validation, allowed actions, expected writes, protected paths, and evidence records. |
| Human or calling application | Task acceptance, consequential actions, and changes to default model routes. |

Keep the provider adapter (the small piece of code that talks to the
endpoint) thin. Its job is to send an approved request and return the raw
response with transport diagnostics such as status, latency, and errors. Do
not let it silently repair output, choose new sources, write application state,
or promote a model route.

Before calling a model, make the request previewable. A useful preview names:

- the task;
- the allowed source IDs;
- the output contract;
- the selected model profile (a named bundle of endpoint, model, and request
  settings);
- whether a model will be called;
- whether state may change; and
- the expected and protected paths.

The fixtures in `examples/model_outputs.jsonl` stand in for captured raw model
responses so that the contract can be tested without a live endpoint:

```sh
python3 -B reliability_demo.py examples/model_outputs.jsonl
```

Expected output:

```text
PASS helpful_summary
PASS ask_for_source
```

The second case matters as much as the first. A useful harness must preserve
"I need more evidence" as a valid outcome instead of pressuring the model to
guess.

## 3. Validate More Than JSON

Parsing JSON is only the first contract check. This example also requires:

- a non-empty `answer`;
- an allowed `action`;
- a `confidence` value from `0` to `1`;
- `citations` drawn from the source IDs supplied for this case; and
- an empty `writes` list.

The canary file includes a valid response and three expected failures:

```sh
python3 -B structured_output_canary.py examples/canary_outputs.jsonl
```

Expected output:

```text
PASS valid_summary_with_citation
PASS invalid_unknown_citation
PASS invalid_write_request
PASS invalid_non_json
```

Here, `PASS invalid_unknown_citation` means the harness correctly rejected the
invalid case. A negative example that fails to fail is a broken guardrail.

When you add your own task, begin with a small set of cases:

1. one ordinary valid response;
2. one response with an unknown source;
3. one response that should admit missing evidence;
4. one malformed response;
5. one forbidden action or write request; and
6. one plausible-looking answer that is wrong for the task.

The first five primarily test the contract. The sixth begins to test utility.
Keep those results separate.

## 4. Prove The State Boundary

"Read-only" should be a checked claim, not an intention.

The protected-path example compares synthetic before and after manifests. It
checks that:

- every changed path was declared in `expected_writes`;
- every expected write actually happened; and
- no changed path falls under a protected prefix.

Run:

```sh
python3 -B protected_path_proof.py examples/protected_path_cases.jsonl
```

Expected output:

```text
PASS valid_expected_write_only
PASS invalid_unexpected_write
PASS invalid_protected_path_change
PASS invalid_missing_expected_write
```

This is a small, deterministic pattern. It is not an operating-system sandbox,
and synthetic hashes do not prove that a real process was contained. In a live
workflow, create the manifests independently of the model call and retain the
evidence needed to reproduce the comparison.

## 5. Turn A Result Into Evidence

Record the evidence levels separately for every meaningful run. The following
is an illustrative worksheet, not a schema enforced by this repository:

```json
{
  "run_id": "synthetic-run-001",
  "task_id": "source-bound-summary",
  "model_profile": "local-model-a",
  "model_called": false,
  "state_mutating": false,
  "transport_status": "not_measured",
  "contract_status": "pass",
  "utility_status": "not_measured",
  "promotion_status": "not_evaluated",
  "failure_class": "none",
  "latency_ms": 0,
  "reviewer_outcome": "not_reviewed"
}
```

`not_measured` is not a pass. Preserve it so a downstream report cannot turn
missing evidence into assurance.

Use failure classes that point to the next investigation:

| Failure class | Example | Do next |
| --- | --- | --- |
| `infrastructure` | Timeout, server error, or runtime crash. | Repair or retest the runtime before judging answer quality. |
| `schema` | Non-JSON output or missing required fields. | Inspect the contract, prompt, adapter, and model behavior. |
| `source_boundary` | Unknown citation or unsupported claim. | Inspect context selection and grounding behavior. |
| `answer_quality` | Valid structure but incorrect, incomplete, or unhelpful content. | Review the task, context, prompt, and model fit. |
| `human_revision` | The answer required substantial correction before use. | Record the revision burden as part of utility. |

This separation prevents two common mistakes: calling a runtime failure a bad
answer, and calling a schema-valid response a useful answer.

## 6. Compare Models Without Inventing A Winner

Only compare models on task instances they all attempted. Compare within a
named workload class, not across a pile of unrelated work.

Useful measures include:

- completion status;
- contract failures by class;
- task-specific human score;
- revision rounds;
- wall time; and
- pass-quality latency: time to a response that cleared the required gates.

Raw speed is weak evidence. A fast response that fails the source boundary may
cost more reviewer time than a slower response that passes.

The separate
[Model Workload Telemetry](https://github.com/TheDarkniteFalls/model-workload-telemetry)
project owns the runnable paired-comparison pattern. From a checkout of that
repository, its no-model self-test is:

```sh
python3 -B model_workload_telemetry.py --self-test
```

A comparison report may recommend a route, but begin in report-only mode. Keep
the actual default unchanged until repeated matched cases pass, failures are
understood, and a human reviews the promotion decision.

One strong run is a reason to test again, not a reason to change the default.

## 7. Know What To Postpone

Do not open every capability because one contract check passed. Keep these
separate and closed until the simpler path is dependable:

- direct filesystem or shell access for the model;
- browser or connector access;
- automatic durable memory;
- broad web search or arbitrary URL fetching;
- model-controlled tools;
- external actions;
- automatic route promotion; and
- autonomous agent loops.

The first useful milestone is smaller:

> One task can be previewed, run through a declared contract, checked for
> unexpected writes, evaluated honestly, and recorded without hiding missing
> evidence.

Build the user interface after that path is boring enough to trust.

## Run The Complete Local Check

These are the repository's deterministic checks:

```sh
python3 -B reliability_demo.py --self-test
python3 -B reliability_demo.py examples/model_outputs.jsonl
python3 -B structured_output_canary.py --self-test
python3 -B structured_output_canary.py examples/canary_outputs.jsonl
python3 -B protected_path_proof.py --self-test
python3 -B protected_path_proof.py examples/protected_path_cases.jsonl
```

Together they establish that the supplied synthetic cases preserve the
declared output, citation, confidence, and no-write rules. They still do not
call a model, verify semantic truth, measure live-model quality, or prove that
any route deserves promotion.

## Where To Go Next

- Use this repository to keep the first contract small and inspectable.
- Use
  [Local Assistant Reliability Lab](https://github.com/TheDarkniteFalls/local-assistant-reliability-lab)
  to find adjacent patterns for context, authority, receipts, and repeatable
  quality checks.
- Use
  [Model Workload Telemetry](https://github.com/TheDarkniteFalls/model-workload-telemetry)
  when you have repeated runs on matched tasks and are ready to compare model
  routes without declaring a universal winner.

The goal is not to accumulate the most machinery. It is to know exactly what
each layer proves before trusting the next one.
