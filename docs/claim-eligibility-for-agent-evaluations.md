# From Metric to Promotion: Claim Eligibility for Agent Evaluations

Status: Public technical note; published in this repository

Evidence cutoff: 2026-08-02

Scope: This note proposes a bounded decision check. It is not a standard,
completed assurance case, model evaluation, promotion decision, or
authorization to publish, contact anyone, or change a model route.

## Thesis

**Add a bounded claim record between evaluation results and promotion.**

Agent evaluations produce scores, traces, grader results, and reports. What
crosses the boundary into promotion is usually a sentence: the harness improved
reasoning, the candidate is safer, or the route should change.

Between measurement and promotion sits a decision that is often left implicit:

> What is the strongest claim this evaluation record actually supports?

This note calls that decision **claim eligibility**. It keeps four steps
separate:

```text
observation -> attribution -> eligible claim -> authorized decision
```

A strict score may rise because the model reasoned better, or because the
harness improved output conformance, changed ambiguity behaviour, recovered an
infrastructure failure, or enforced a stop rule. These outcomes may all be
useful, but they do not earn the same sentence.

Claim eligibility produces that **bounded claim record**: exact wording and
scope, decision status, any unresolved gate, the smallest evidence that could
reopen a held claim, and the authority owner. The contribution combines
familiar controls into seven non-compensating gates at this handoff. The
individual questions and underlying methods are established.

## Audience and Usefulness

The first audience is people who build or review agent evaluations: harness and
benchmark maintainers, evaluation and integrity teams, research-infrastructure
engineers, and technical operators responsible for promotion decisions. The
bounded claim record gives them a reviewable handoff when results are mixed: it
separates conformance from semantic change, preserves regressions and unassessed
work, identifies the evidence needed to reopen a hold, and prevents a valid
record from being mistaken for a successful experiment. Promotion remains an
external authority decision.

The check is deliberately small. It does not replace task design, graders,
statistical analysis, ablations, provenance systems, or expert judgment.

## Claim Eligibility v0

The provisional decision check has seven non-compensating gates:

| Gate | Decision question |
| --- | --- |
| Evidence scope | Is the evidence real, synthetic, authenticated, representative, or only supplied classification? |
| Mixed outcome | Which outcomes are gains, regressions, partial, failed, unchanged, or unassessed, whether the record is a comparison or a single run? |
| Assessment integrity | Which cases were attempted, assessed, stopped, or left unassessed? |
| Attribution boundary | Are reported differences descriptive, or does a frozen intervention support a causal claim? |
| Claim eligibility | What is the strongest wording supported by the complete record? |
| Authority versus effect | Did an authority or validity rule fail, and what actually occurred: an evaluation result (including an invalid one), a downstream decision, or an operational action? |
| Promotion | Who may act on the eligible claim, and is promotion supported now? |

One gate cannot compensate for another. A precise evidence request does not
make an unsupported promotion safe, and a correct stop rule does not establish
candidate quality.

A corrected rerun may support a new claim; it does not retroactively validate
the earlier record.

This v0 was checked against hypothetical boundary cases and two bounded
public-record applications for obvious ambiguity and compensation failures.
These were author-run design checks, not external validation: it has not been
tested with external practitioners or shown to improve real evaluation
decisions. It should now remain frozen until further use exposes a specific
defect.

## Concrete Example

The public [Harness Gain
Decomposition](https://github.com/TheDarkniteFalls/local-model-reliability-example/blob/main/docs/measuring-what-a-harness-changed.md)
provides a deterministic synthetic example. It compares a `bare_model` arm
with a `guided_harness` arm across eight classified cases. It calls no model,
uses no network service, and contains no prompts, model responses, benchmark
answers, or private evaluation traces.

The [public
fixture](https://github.com/TheDarkniteFalls/local-model-reliability-example/blob/main/examples/harness_gain_cases.json)
is deliberately mixed. Its eight cases contain a shared pass; an
output-discipline recovery that changes machine usability without changing the
supplied substantive judgment; designated semantic and behavioural gains; a
regression; a shared failure; an authority stop with no reported operational
effect; and an unattempted, unassessed remainder.

The resulting bounded claim record is:

| Field | Record |
| --- | --- |
| Exact eligible claim wording | Under the supplied synthetic rules, the guided arm records one conformance recovery plus semantic and behavioural gains alongside a regression and shared failure; an authority-integrity stop leaves material gain unassessed. |
| Evidence scope | Public synthetic fixture with supplied, unauthenticated classifications; no real model, private traces, or representative sample. |
| Decision status | Fixture-bounded descriptive claim eligible. Material gain unassessed; promotion ineligible. |
| Decisive unresolved gate | Assessment integrity: the stop left the final scheduled case unattempted and unassessed. |
| Smallest reopening evidence | A pre-frozen comparison with every scheduled case assessed and no integrity stop; causal component wording still requires a separate frozen ablation. |
| Promotion authority owner or gap | No owner or thresholds declared; no model-route change authorized. |

## Transfer Illustration: MoE Routing

This is a transfer illustration, not evidence of cross-domain transfer.
Suppose a mixture-of-experts dashboard reports nearly even token utilization
across routed experts. Exact run identity, token counts, aggregation window,
and a reproducible calculation may support balance during that window.

Utilization alone does not establish input-dependent routing, useful expert
specialization, robustness across workloads, or promotion eligibility. Those
claims would need evidence such as router-score distributions and baselines;
expert-output comparisons and bounded ablation or rerouting; stratified
quality, overload, communication, and latency evidence; and declared
thresholds, regression and cost evidence, plus an identified promotion owner.
The hold is not a rejection: it prevents one attractive aggregate from
acquiring more authority than its evidence supplies.

## Adjacent Research and Novelty Boundary

The surrounding territory is established. Anthropic's agent-evaluation
guidance treats the model and harness as the evaluated system and recommends
multiple grader types. [Harness-Bench](https://arxiv.org/abs/2605.27922) studies
model-harness configurations under shared protocols, while
[AgentCompass](https://arxiv.org/abs/2607.13705) separates benchmark, harness,
and environment and adds trajectory analysis. [NIST AI
800-3](https://www.nist.gov/news-events/news/2026/02/new-report-expanding-ai-evaluation-toolbox-statistical-models)
formalizes measurement targets and assumptions that affect what benchmark
results mean. Work on [execution
provenance](https://arxiv.org/abs/2606.04990) connects agent claims to supporting
evidence and traces.

OpenAI's [shared playbook for trustworthy third party
evaluations](https://openai.com/index/trustworthy-third-party-evaluations-foundations/)
directly overlaps this handoff: it asks reports to state the claim an evaluation
was designed to test, disclose the harness and validity evidence, and give
decision makers enough detail to understand what claims the evaluation
supports. It defines assessment more broadly as a judgment about whether
evidence supports a claim, risk conclusion, or assurance position.

Gao and Zhou's [evidence-supported bounds for interactive-agent
evaluation](https://arxiv.org/abs/2605.10448) adds an outcome-evidence reporting
layer to existing benchmarks. It locks case checklists before evidence scoring,
labels completed records `Evidence Pass`, `Evidence Fail`, or `Unknown`, and
reports bounds over the fixed set rather than hiding uncertain cases inside one
aggregate score.

Claim-evidence structures and go/no-go controls are also established.
[Argument-based assurance
cases](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/explaining-decisions-made-with-artificial-intelligence/annexe-5-argument-based-assurance-cases/)
organize claims, arguments, context, and evidence; the [NIST AI
RMF](https://airc.nist.gov/airmf-resources/airmf/4-effectiveness/) calls for
explicit commissioning and deployment decisions.

These sources materially overlap any broad claim that evaluation evidence
should bound reporting claims, that claim strength depends on harness and
validity evidence, or that insufficient artifacts should remain visible as
uncertainty. Claim eligibility does not claim to originate claim-aligned
evaluation reporting, evidence-supported score bounds, claim-evidence
structures, or go/no-go controls.

The narrower contribution proposed here is the bounded, non-compensating
handoff from the complete evaluation record to exact eligible wording, a
decisive unresolved gate and reopening evidence, and a separately named
external promotion authority. This may be an application of established
evaluation and assurance principles; academic novelty and external usefulness
remain unproven.

## Evidence Map

| Claim | Evidence | Status |
| --- | --- | --- |
| Agent-evaluation outcomes depend on more than a base model. | Anthropic guidance, Harness-Bench, and AgentCompass | `supported` |
| Contract, semantic, behavioural, authority, operational-effect, and assessment states can be recorded separately. | Public Harness Gain Decomposition and fixture | `supported` |
| A valid fail-closed record can leave material gain and promotion ineligible. | Public synthetic authority-stop example | `supported_for_the_fixture` |
| A bounded claim record tested through seven non-compensating gates is a coherent evaluation handoff. | Operational synthesis, hypothetical boundary-case checks, and two bounded public-record applications for obvious ambiguity and compensation failures | `hypothesis` |
| Claim eligibility improves real reviewers' decisions. | No external-use evidence | `needs_evidence` |
| The method transfers to MoE routing decisions. | Worked analogy without empirical routing data | `hypothesis` |
| The method is academically novel or a general standard. | No systematic novelty or validation study | `not_claimed` |

## Uncertainties and Limitations

- The principal example is synthetic. Its classifications are supplied rather
  than authenticated observations from a real evaluation.
- The deterministic checker validates internal relationships; it does not
  establish factual truth, representative sampling, statistical significance,
  or real-model improvement.
- The seven-gate v0 was checked against hypothetical boundary cases and two
  bounded public-record applications for obvious ambiguity and compensation
  failures; these are author-run design checks, not external practitioner
  validation.
- Promotion thresholds and authority owners remain application-specific.
- The MoE example is illustrative and contains no empirical routing result.
- No external practitioner study is planned at this stage. External usefulness
  remains unknown until the method earns real use.
- Publication on this repository’s main branch is not evidence of adoption,
  lab interest, or production readiness.

## Privacy and Generalization

The principal case uses public synthetic data only. Private LSAL prompts,
outputs, tasks, judges, manifests, holdouts, logs, paths, identities, and real
evaluation counts are excluded. Internal work motivated the questions but is
not offered as evidence readers must accept.

The MoE example is hypothetical. It makes no claim about a specific model,
router, dataset, or lab.

This note was developed through collaboration between Mike and Codex.
Publication in this repository discloses that assistance. Human evidence,
privacy, source, and editorial review remain required for any revision or
broader promotion.

## Next Action

The smallest next step is to observe further use without expanding v0
speculatively. Outreach, implementation, standardization, and broader promotion
remain separate owner decisions.

## Sources

- [Harness Gain Decomposition](https://github.com/TheDarkniteFalls/local-model-reliability-example/blob/main/docs/measuring-what-a-harness-changed.md).
- [Synthetic harness-gain fixture](https://github.com/TheDarkniteFalls/local-model-reliability-example/blob/main/examples/harness_gain_cases.json).
- Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
- Yao et al., [Harness-Bench: Measuring Harness Effects across Models in Realistic Agent Workflows](https://arxiv.org/abs/2605.27922).
- Chen et al., [AgentCompass: A Unified Evaluation Infrastructure for Agent Capabilities](https://arxiv.org/abs/2607.13705).
- NIST, [Expanding the AI Evaluation Toolbox with Statistical Models](https://www.nist.gov/news-events/news/2026/02/new-report-expanding-ai-evaluation-toolbox-statistical-models).
- Wang et al., [From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents](https://arxiv.org/abs/2606.04990).
- OpenAI, [A shared playbook for trustworthy third party evaluations](https://openai.com/index/trustworthy-third-party-evaluations-foundations/).
- Gao and Zhou, [Can Agent Benchmarks Support Their Scores? Evidence-Supported Bounds for Interactive-Agent Evaluation](https://arxiv.org/abs/2605.10448).
- Information Commissioner's Office, [Argument-based assurance cases](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/explaining-decisions-made-with-artificial-intelligence/annexe-5-argument-based-assurance-cases/).
- NIST, [AI Risk Management Framework: Effectiveness](https://airc.nist.gov/airmf-resources/airmf/4-effectiveness/).
