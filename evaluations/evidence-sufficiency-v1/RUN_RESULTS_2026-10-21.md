# Evidence Sufficiency Claim v1 — RUN RESULTS (2026-10-21)

Recorded alongside the claim per its own procedure: "a run's result is recorded alongside it, pass or fail." CLAIM.md is unedited.

Run 2026-10-21 by the record keeper (Muse), locally, ground-truth key in evaluator custody throughout. Each implementation received only question + content per dossier (protocol rule 3) — no IDs, no category labels, no sufficiency indicators. Scoring per README_PROTOCOL rule 5: answerable items pass only on a matching answer (harmless formatting allowed); unanswerable items pass only on abstention. Pass bar (frozen): ≥16/20 overall AND ≥4/5 in every category. Full raw responses: `run_responses_v1.jsonl`, `run_responses_v2.jsonl`, `run_responses_v3.jsonl` in this directory.

## VERDICT: THE CLAIM FAILS — for all three submitted implementations.

| Build | Total | A (plain) | B (buried) | C (absent) | D (conflict) |
|---|---|---|---|---|---|
| v1 — label matcher | 5/20* | 1/5 | 0/5 | 4/5 | 0/5 |
| v2 — fixed-field hardening build | 10/20 | 0/5 | 0/5 | 5/5 | 5/5 |
| v3 — generic-terms build | 10/20 | 1/5 | 1/5 | 3/5 | 5/5 |
| **Bar** | **16/20** | **4/5** | **4/5** | **4/5** | **4/5** |

*Adjudication: automated scoring initially gave v1 6/20; manual review under protocol rule 5 moved B4 to FAIL (see below). Final: 5/20.

## Borderline adjudications (protocol: harmless formatting allowed)
- v1 P2 / v3 P2 — PASS (noted): the response embeds the key value ("Room 214") in a full sentence copied from the dossier. Single-valued and unambiguous; counted as a formatting difference.
- v3 B5 — PASS (noted): same pattern; the single value matches the key exactly inside a sentence fragment.
- v1 B4 — FAIL (adjusted): the response returned THREE values ("FX-210, FX-210B, and FX-211..."). Listing every candidate including the key is not providing the correct answer.

## Per-build notes
- v1 (5/20): abstained on 4 of 5 plainly-present items (prose blindness); answered neighboring values and clock fragments on buried items; selected one side on all five contradiction dossiers (D 0/5) — its conflict check never fired on prose-stated contradictions.
- v2 (10/20): abstained on all 20 dossiers (its fixed field table identified no field in any answerable item). Its 10 points are exactly the abstain-all score, which the claim text names as necessarily failing. A 0/5, B 0/5.
- v3 (10/20): the strongest contradiction performance (D 5/5 — normalized conflict detection works) and correct answers on P2 and B5, but abstained on a plainly stated budget (P1) and a person's name (P3), on 4 of 5 buried items, and answered dossier fragments on C2 and C3 where abstention was required.

## Independent practice evaluation (context, not the claim's verdict)
Before this run, all three builds were also measured on a 20-dossier adversarial practice set authored independently by the project's external evaluator (Mistral Le Chat, "OTA Reacts") — same four shapes, harder material, scored by the same evaluator procedure. Results: v1 5/20, v2 11/20 (abstention composition), v3 8/20. The practice results and the frozen results agree in structure: every build fails the answer-present and buried categories; the differences are in how each fails.

## What the evaluation establishes
The frozen dossiers are short and plainly written, and the answerable ones still defeated all three implementations. The binding constraint is assertion recognition — knowing that a sentence states the requested fact (a budget approved in prose, a serial number given as "plate reads SN…", a name in nominative position). Label matching, fixed field tables, and question-term matching each capture a slice of that and miss the rest; tightening any of them trades wrong answers for refusals without crossing the bar. Three architectures were measured against the same registered instrument; the result is a falsification, not an implementation delay.

Per CLAIM.md: "Any lower score falsifies the claim for this evaluation." **Evidence Sufficiency Claim v1 is falsified for every implementation submitted.**

## Integrity notes
- The v1 build's session had prior exposure to the ground-truth key through a repository commit fetch during an earlier build attempt (the freeze had mistakenly committed the key into the public tree; the session detected the exposure and aborted at the time). Its score is reported with that status attached. The v2 and v3 build sessions were fresh, had no key exposure, and never received dossiers, labels, or the key at build time.
- The key's presence in this repository's history is a standing caveat on the evaluation's secrecy. The mitigation of record: builders received only a certified attachment package excluding key and dossiers; scoring was performed locally by the evaluator.
- The evaluator also authored the freeze and two of the three build packets. Scoring was mechanical under protocol rule 5, with the three adjudications above stated on the record.
