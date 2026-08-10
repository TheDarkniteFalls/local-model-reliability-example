# Prevent Ungrounded Web Answers From Entering Trusted Context

A local model can produce fluent wording after receiving current web evidence
and still omit its citation, invent a version, misstate the date, or describe
the answer as model knowledge. If an application saves that wording as trusted
conversation context, one weak answer can influence later turns.

Citeglass v0.1 demonstrates an application-owned boundary:

1. A provider adapter or deterministic extractor creates typed facts.
2. Raw source prose stays outside the projection and has zero instruction
   authority.
3. The model writes one exact structured answer; the application does not
   repair or replace it.
4. The Grounded Answer Gate checks provenance, URLs, metadata, bounded release
   facts, browsing claims, and hostile-instruction canaries.
5. Only an accepted receipt permits the wording to enter downstream context.

## Five-Minute Proof

```sh
python3 grounded_answer_gate.py examples/grounded_answer_cases.json
```

The fixture freezes one accepted case and the known-bad cases before the gate
is evaluated. The command emits one NDJSON record per case containing the exact
receipt, the predetermined expectation, and `matches_expectation`. A zero exit
means every case reached its predetermined decision. It does not mean every
generated answer will be good.

## Integration

The public Python interface is:

```python
from grounded_answer_gate import evaluate_grounded_answer

receipt = evaluate_grounded_answer(case)
if receipt["downstream_context_allowed"]:
    trusted_history.append(candidate_answer_text)
else:
    show_rejection(receipt["failed_check_codes"])
```

`case` contains only provider-neutral typed source projections and the exact
raw candidate output. Each projection names its source reference and approved
URL, carries a bounded `software_release` fact, declares
`instruction_authority=false`, and declares `raw_content_included=false`.

The receipt never contains the answer text. It records a SHA-256 digest, size,
approved and cited provenance, failed check codes, and explicit no-model,
no-network, and no-mutation fields.

## Where Gemma And LiteRT-LM Fit

Gemma, LiteRT-LM, Ollama, MLX, or another runtime can produce the candidate
JSON. A search provider can supply source material below an application-owned
adapter. Neither belongs inside this gate: the same deterministic receipt
contract applies after any model and provider have finished.

This separation makes it possible to compare prompts, models, and runtimes
without changing the downstream acceptance boundary. It also makes failure
visible: model-quality problems remain model-quality problems rather than
being hidden by deterministic answer rewriting.

## Threat Boundary

The v0 gate fails closed on:

- malformed or extended answer and source schemas;
- missing, unknown, or mismatched provenance;
- absent or unapproved URLs;
- unsupported version-like claims;
- the wrong latest release tag or publication date;
- source metadata that claims model prior instead of supplied evidence;
- direct browsing claims and a small disclosed hostile-echo canary set; and
- typed projections that include raw content or non-zero instruction authority.

The gate does not authenticate an extractor, fetch a source, establish that a
source is true or current, understand arbitrary factual prose, or detect every
possible prompt injection. The first fact profile deliberately covers only
software releases. Production adopters must own source authentication,
extraction, policy, display, and storage boundaries around it.

It also does not resolve stale, duplicate, conflicting, or malicious typed
projections, and its bounded reference checks do not prove exhaustive
one-to-one citation coverage for arbitrary multi-source answers. The retained
hash and length are audit identifiers, not a privacy guarantee. The explicit
no-model, no-network, and no-mutation fields describe this gate invocation, not
the surrounding retrieval, model, UI, history, or storage pipeline.

## What This Establishes

A passing synthetic run establishes that the application can make an explicit,
reproducible downstream-context decision from the declared v0 contract. It
does not establish live-model answer quality, general semantic correctness,
source truth, runtime or token-budget compatibility, security against
arbitrary hostile content, or safe deployment.
