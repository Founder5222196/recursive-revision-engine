# Evidence Sufficiency Claim v2 — Grounded Semantic Judging Under Adversarial Variation

Status: FROZEN 2026-10-21 by owner authorization, before any implementation. Drafted by the original builder (v2 Freeze Packet, 2026-10-21); registered verbatim by the record keeper. A run's result is recorded alongside this claim, pass or fail; the claim text is never edited after a run.

## Claim

Given a question and a dossier, without an explicit indicator of answerability, the Grounded Evidence Judge must determine whether the dossier contains sufficient, internally consistent, attributable evidence to answer the question.

The judge must return the supported answer when the evidence satisfies the frozen sufficiency policy and must abstain when the requested fact is absent, cannot be attributed unambiguously, or remains unresolved by contradictory evidence.

The instrument must generalize across materially different expressions of the same proposition, distinguish relevant evidence from lexically similar distractors, and recognize when multiple assertions are incompatible. It must not use external factual knowledge to fill gaps in the dossier or invent a rule to resolve a contradiction.

Following correction through the Recursive Revision Engine, the versioned and authorized instrument will be evaluated on a frozen, independently authored set of 100 previously unseen dossiers. The evaluation set will contain five categories of 20 dossiers each. The builder will receive neither the dossiers nor their answerability labels or ground-truth key before evaluation.

Each dossier receives one binary score under the frozen response protocol. The claim passes only if the judge achieves at least 85/100 overall and at least 16/20 in every category. The claim also requires independent verification that the tested instrument version is the version authorized and recorded by RRE.

Passing establishes performance on the defined evaluation domain and protocol. It does not establish universal evidence sufficiency, general intelligence, or reliability on every possible natural-language dossier.

## Frozen evaluation design

- **A — 20 items. Direct assertion and correct attribution.** Answerable facts stated plainly, with distractors that test whether the judge selects the requested fact and binds it to the right entity.
- **B — 20 items. Buried, paraphrased, and structurally varied assertions.** Answerable facts expressed through varied grammar, unfamiliar wording, distant passages, or compatible evidence that must be combined.
- **C — 20 items. Absent facts and misleading neighbors.** Unanswerable questions accompanied by tempting but insufficient evidence, related attributes, or information about the wrong subject.
- **D — 20 items. Contradictory evidence without authorized resolution.** Unanswerable questions where incompatible assertions concern the same requested fact and no defensible resolution rule exists.
- **E — 20 items. Scope, time, modality, and compatible evidence.** Answerable cases requiring correct distinctions between contexts, time periods, hypothetical and asserted information, or compatible statements.

Categories A, B, and E are answerable. Categories C and D are unanswerable under the frozen policy.

## Scoring and output rules

- Answerable item: pass only when the returned `ANSWER: <answer>` matches the independently established answer, allowing harmless formatting differences. Abstention fails.
- Unanswerable item: pass only when the judge returns `ABSTAIN: <brief reason>`. An answer fails even if plausible in the real world.
- Response schema: missing or invalid responses fail.
- Contradictions: choosing arbitrarily between unresolved conflicting assertions fails.
- Evidence grounding: an answer supported only by an unrelated passage or an invented inference fails.
- No partial credit: mentioning the correct value alongside unsupported alternatives does not earn a pass.
- Thresholds: at least 85/100 overall and at least 16/20 in every category. Both conditions must hold.
- Identity: the evaluator independently verifies the tested instrument's version, configuration, model identity where applicable, and RRE authorization.

The final report must include all 100 binary outcomes, category totals, false-answer rate, false-abstention rate, total errors, and an overall confidence interval. No item may be removed, reclassified, or rescored to manufacture a pass after results are observed.

## Evaluation custody

The independent evaluator authors and retains the evaluation set and answer key. The builder must not receive its questions, dossiers, answerability labels, or key before the tested version is frozen.

The disclosed practice set is permanently development material. The previous v1 result remains public and unchanged. Neither the practice scores nor success on a small demonstration may be substituted for the registered v2 result.

Evaluation material (dossiers and key) is held in evaluator custody OUTSIDE this repository until the run is complete; only the claim, the gate, the protocol, and — after the run — the results are committed here. (This corrects the v1 freeze design, in which the key was committed into the public tree before the run.)
