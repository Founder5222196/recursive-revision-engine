# Evidence Sufficiency v2 build — RELEASE RECORD (2026-10-23)

**Released version:** `stage2-ext-2026-10-23-r3-rule-a-b`
- `evidence_judge.py` — SHA-256 `fc3b0970e11014935605be972a6c4feb393d6111a05ddb6aa77a3b340fc767b9`
- `rre_minimal.py` — SHA-256 `4e31f3c1e34175fc55570494c53ec2d321a5b708bd8a3100187aede950ccd9a4` (canonical, unchanged)
- Frozen extraction prompt (`FROZEN_EXTRACTION_PROMPT.txt`) — SHA-256 `940a468410478d59f03c583457c219d849c967294c9c3c69823c4a69a94328c1`
- `evidence_judge_original.py` is the frozen pre-correction base (`07865f78…`), retained for rollback comparison.

**Basis.** This build is the fixed candidate of the Correction Integrity Gate, which PASSED on 2026-10-23 (see `evaluations/evidence-sufficiency-v2/GATE_COMPLETION_RECORD.md`): baseline 18/20 with two adjudicated failures; the authorized two-rule correction (`GENERAL_RULE_WITH_SCOPED_EXCEPTION`, `ASSERTED_FACT_IN_HISTORICAL_SOURCE`) corrects both with zero regressions; transfer on 20 sealed unseen dossiers scored 18/20 against a ≥16/20 bar with zero false answers; persistence across restart and rollback verified. A post-Gate stress-test episode (an unauthorized variant, measured and rejected) is recorded in `evaluations/evidence-sufficiency-v2/STRESS_TEST_EPISODE_2026-10-23.md`; the candidate of record was never displaced.

**Authorization.** Release authorized by the owner, Tarnue Kamara Tyler, 2026-10-23 ("let's finish — all of it"), following the Gate sign-off recorded the same day.

**Boundary.** This release makes the Gate-validated build the standing version of record. **Evidence Sufficiency Claim v2 has NOT been evaluated**: its frozen bar (≥85/100 overall and ≥16/20 in each of five categories on 100 independently authored unseen dossiers) has never been run, and no such set exists yet. This release asserts the Gate result only — it does not assert the claim.
