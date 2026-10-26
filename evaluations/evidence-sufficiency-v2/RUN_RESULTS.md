# Evidence Sufficiency Claim v2 — RUN RESULTS (2026-10-26)

Frozen claim: CLAIM.md (commit ca64237). Evaluation run executed once, scored by the record keeper against the evaluator's sealed key per README_PROTOCOL. Published pass or fail, per protocol — the result is a PASS.

## The run

- Return received via the owner 2026-10-26 ~16:51 CT, filed verbatim as `builder-claim-v2-run-return-2026-10-26.txt` (SHA-256 `2e119d99743899c02b3031fe9d68b7a569f7fa4a154b97330338e6f8331b6102`). Run packet sent was `claim-v2-run-packet-v2-ALL-IN-ONE` (fresh-named copy, bytes identical, SHA-256 `e77859ed…`), after the builder correctly answered DO NOT HOLD to a state-check packet (it no longer held the run packet in-session) and stopped without inventing anything.
- Builder's test answers were correct (stage, judge hash, return contents, must-nots). Instrument identity as run (from run_manifest): extraction by OpenAI "GPT-5.6 Sol", adapter manual-chat-output/1.0, host-managed decoding; judge `evidence_judge.py` r3 `fc3b0970…` (matches frozen record); engine `rre_minimal.py` `4e31f3c1…` (matches); policy sufficiency/1.0 + authorized two-rule extension (both rules enabled), approved by Tarnue Tyler 2026-10-23.
- Counts: 100 response lines, 100 extraction records, 100 decision traces. Answer/abstain split: 60 ANSWER / 40 ABSTAIN, matching the set design.

## Verification (record keeper, 2026-10-26)

1. **Dossier binding — PASS.** Every extraction record's `dossier_sha256` and question recomputed against the sealed set (`ota-claim-v2-dossiers-SEALED-2026-10-23.json`): all 100 bind exactly. Nothing substituted.
2. **Prompt hash — RESOLVED.** The manifest cites the frozen extraction prompt as `caf6c0a3…`; the frozen record cites `940a4684…`. Both are the same text: the packet-embedded prompt section hashed with its trailing blank line gives `caf6c0a3…`; the prompt content itself is byte-identical to the released `FROZEN_EXTRACTION_PROMPT.txt` (`940a4684…`). Framing difference only; the frozen prompt was used verbatim.
3. **Replay — PASS.** All 100 extraction records replayed through the released adapter (`rre_run.py decide`, released build, authorized extension applied in a fresh process) using the run's stated per-item targets: **all 100 response lines and all 100 traces reproduce exactly** (status, answer, evidence indices). Configuration note, recorded for honesty: a first replay without the targets file diverged on 29 items, because the adapter defaults the target to candidate[0]'s entity/attribute when no targets are supplied; the run's traces carry question-derived targets, and with those supplied the replay is exact. The divergence was a replay-configuration artifact, not a run defect.

## Scoring (frozen convention: CLAIM.md + README_PROTOCOL §3)

Binary per item. Answerable items pass on a matching answer, "allowing harmless formatting differences"; unanswerable items pass only on abstention. No partial credit; nothing rescored.

- **Status accuracy: 100/100.** No false answers on unanswerable items (all 40 abstained correctly); no false abstentions (all 60 answerable items answered).
- **Adjudicated as harmless formatting (PASS), 11 items** — returned answer states the key's value with surface differences only: items 10 ("220 people" / key "220"), 12 (leading "the"), 18 ("27 pupils" / "27"), 23 ("600 sacks of flour" / "600 sacks"), 31 ("1,900 head" / "1,900"), 35 ("£5" / "£5 per performance"), 36 ("SW force 5" / "southwest, force 5"), 40 (rate qualifier dropped, amount identical), 83 ("two pike per rod" / "two pike"), 91 ("90 minutes" / "every 90 minutes"), 96 ("1.90 pence each" / "per unit").
- **Item 25 equivalence (filed at seal time) applied:** key "2,040", returned "TWO THOUSAND FORTY" — equal, PASS.
- **Seal-time caveats on items 63 and 76:** both are category-D ABSTAIN items; the instrument abstained on both, citing the unresolved contradictions — correct; the caveats do not bind.
- **Adjudicated FAIL, 1 item — item 28 (category B).** Key: "7 June 1754". Returned: "June 7th". The day/month and the disambiguation it tests (7 June, not 9 June) are correct, but the established answer includes the year and the returned answer omits it; a missing component of a date is content, not formatting. Recorded as the run's single error and as the report's one judgment call — the evaluator's independent verification can confirm or overturn it; the outcome below does not depend on it either way (98 or 99 both clear the overall bar, but category B is 19/20 with the fail, 20/20 without).

## Result

| Category | Score | Bar |
|---|---|---|
| A | 20/20 | ≥16 |
| B | 19/20 | ≥16 |
| C | 20/20 | ≥16 |
| D | 20/20 | ≥16 |
| E | 20/20 | ≥16 |
| **Total** | **99/100** | **≥85** |

- Total errors: 1. False answers: 1 (item 28, incomplete date). False abstentions: 0.
- False-answer rate: 1/100 overall (1/60 among answerable). False-abstention rate: 0/100 (0/40 unanswerable-side: none).
- Overall accuracy 99% — Wilson 95% CI [0.9455, 0.9982].

**VERDICT: CLAIM v2 PASSES** — 99/100 overall and ≥16/20 in every category, on a replay-verified run of the released, authorized instrument over the evaluator's sealed unseen set.


## Appendix — all 100 binary outcomes

| Item | Cat | Expected | Returned | Outcome |
|---|---|---|---|---|
| 1 | A | ANSWER | ANSWER: 1894 | PASS |
| 2 | A | ANSWER | ANSWER: 1,180 °C | PASS |
| 3 | A | ANSWER | ANSWER: 3 May 1938 | PASS |
| 4 | A | ANSWER | ANSWER: 57 | PASS |
| 5 | A | ANSWER | ANSWER: 75 pence | PASS |
| 6 | A | ANSWER | ANSWER: Ironheart | PASS |
| 7 | A | ANSWER | ANSWER: 21 days | PASS |
| 8 | A | ANSWER | ANSWER: 4.2 tonnes | PASS |
| 9 | A | ANSWER | ANSWER: 104.7 FM | PASS |
| 10 | A | ANSWER | ANSWER: 220 people | PASS (adjudicated: harmless formatting) |
| 11 | A | ANSWER | ANSWER: 29.5 °C | PASS |
| 12 | A | ANSWER | ANSWER: the first and third Thursdays of each month | PASS (adjudicated: harmless formatting) |
| 13 | A | ANSWER | ANSWER: 225 millimetres | PASS |
| 14 | A | ANSWER | ANSWER: 34 | PASS |
| 15 | A | ANSWER | ANSWER: 8 hours | PASS |
| 16 | A | ANSWER | ANSWER: £50 | PASS |
| 17 | A | ANSWER | ANSWER: 6 | PASS |
| 18 | A | ANSWER | ANSWER: 27 pupils | PASS (adjudicated: harmless formatting) |
| 19 | A | ANSWER | ANSWER: 3.25 percent | PASS |
| 20 | A | ANSWER | ANSWER: 18 tonnes | PASS |
| 21 | B | ANSWER | ANSWER: 340 metres | PASS |
| 22 | B | ANSWER | ANSWER: 1,215 | PASS |
| 23 | B | ANSWER | ANSWER: 600 sacks of flour | PASS (adjudicated: harmless formatting) |
| 24 | B | ANSWER | ANSWER: 76 acres | PASS |
| 25 | B | ANSWER | ANSWER: TWO THOUSAND FORTY | PASS |
| 26 | B | ANSWER | ANSWER: eleven | PASS |
| 27 | B | ANSWER | ANSWER: Sir Gerald Marley | PASS |
| 28 | B | ANSWER | ANSWER: June 7th | FAIL (adjudicated: answer omits the year of the established answer) |
| 29 | B | ANSWER | ANSWER: 78 mph | PASS |
| 30 | B | ANSWER | ANSWER: 2,400 bales | PASS |
| 31 | B | ANSWER | ANSWER: 1,900 head | PASS (adjudicated: harmless formatting) |
| 32 | B | ANSWER | ANSWER: J. Aldous | PASS |
| 33 | B | ANSWER | ANSWER: 44.2 t | PASS |
| 34 | B | ANSWER | ANSWER: 43 | PASS |
| 35 | B | ANSWER | ANSWER: £5 | PASS (adjudicated: harmless formatting) |
| 36 | B | ANSWER | ANSWER: SW force 5 | PASS (adjudicated: harmless formatting) |
| 37 | B | ANSWER | ANSWER: 17 | PASS |
| 38 | B | ANSWER | ANSWER: Callender & Ross | PASS |
| 39 | B | ANSWER | ANSWER: 250 | PASS |
| 40 | B | ANSWER | ANSWER: six shillings and eightpence | PASS (adjudicated: harmless formatting) |
| 41 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 42 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 43 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 44 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 45 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 46 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 47 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 48 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 49 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 50 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 51 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 52 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 53 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 54 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 55 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 56 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 57 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 58 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 59 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 60 | C | ABSTAIN | ABSTAIN: no attributable asserted evidence for the requested fact | PASS |
| 61 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 62 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 63 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 64 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 65 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 66 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 67 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 68 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 69 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 70 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 71 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 72 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 73 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 74 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 75 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 76 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 77 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 78 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 79 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 80 | D | ABSTAIN | ABSTAIN: unresolved contradictory evidence in candidates 0 and 1 | PASS |
| 81 | E | ANSWER | ANSWER: sixpence | PASS |
| 82 | E | ANSWER | ANSWER: threepence | PASS |
| 83 | E | ANSWER | ANSWER: two pike per rod | PASS (adjudicated: harmless formatting) |
| 84 | E | ANSWER | ANSWER: 26 rooms | PASS |
| 85 | E | ANSWER | ANSWER: £1.20 | PASS |
| 86 | E | ANSWER | ANSWER: 140 | PASS |
| 87 | E | ANSWER | ANSWER: 2,640 | PASS |
| 88 | E | ANSWER | ANSWER: five shillings and sixpence | PASS |
| 89 | E | ANSWER | ANSWER: eight brace per gun | PASS |
| 90 | E | ANSWER | ANSWER: £7 | PASS |
| 91 | E | ANSWER | ANSWER: 90 minutes | PASS (adjudicated: harmless formatting) |
| 92 | E | ANSWER | ANSWER: £72 per year | PASS |
| 93 | E | ANSWER | ANSWER: 2.8 million tonnes | PASS |
| 94 | E | ANSWER | ANSWER: 21:00 | PASS |
| 95 | E | ANSWER | ANSWER: five coats | PASS |
| 96 | E | ANSWER | ANSWER: 1.90 pence each | PASS (adjudicated: harmless formatting) |
| 97 | E | ANSWER | ANSWER: 80 pence per head | PASS |
| 98 | E | ANSWER | ANSWER: Woolsthorpe House | PASS |
| 99 | E | ANSWER | ANSWER: fifteen head per gun | PASS |
| 100 | E | ANSWER | ANSWER: 20,000 bottles | PASS |
