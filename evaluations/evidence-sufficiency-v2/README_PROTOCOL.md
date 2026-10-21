# Evidence Sufficiency v2 — Evaluation Protocol

Frozen 2026-10-21 alongside CLAIM.md and CORRECTION_GATE.md.

1. **Inputs.** For each evaluation item the instrument receives exactly two fields: the question and the dossier content. No item ID, no category label, no answerability indicator, no metadata of any kind. The instrument must not use external factual knowledge to fill gaps in the dossier.

2. **Response schema.** Exactly one line: `ANSWER: <answer>` or `ABSTAIN: <brief reason>`. Any other form, a missing response, or multiple candidate answers counts as an invalid response and fails the item.

3. **Scoring.** Per item, binary. Answerable items pass only on a matching answer (harmless formatting differences allowed; the key normalized without changing its meaning). Unanswerable items pass only on abstention. An answer supported only by an unrelated passage or an invented inference fails. An answer chosen arbitrarily from unresolved contradictory evidence fails. No partial credit.

4. **Claim thresholds.** Pass requires at least 85/100 overall AND at least 16/20 in each category (A, B, C, D, E). Answering every dossier or abstaining on every dossier necessarily fails.

5. **Identity.** Before the run, the evaluator records the instrument's version, configuration, model identity where applicable, and its RRE authorization record. The result applies only to that identified version; a materially different system requires a new evaluation.

6. **Custody.** The evaluation set and its ground-truth key are authored and held by the independent evaluator, outside this repository and outside any builder-accessible location, until the run is complete. The builder receives neither the dossiers nor the labels nor the key before the tested version is frozen. No item-level feedback is given to the builder during the run. The disclosed practice set is development material only and may never be presented as held-out evaluation.

7. **Reporting.** The run's result is recorded alongside the claim in this directory (RUN_RESULTS), pass or fail, including: all 100 binary outcomes, category totals, false-answer rate, false-abstention rate, total errors, and an overall confidence interval. No item may be removed, reclassified, or rescored after results are observed. The claim text is never edited after a run.
