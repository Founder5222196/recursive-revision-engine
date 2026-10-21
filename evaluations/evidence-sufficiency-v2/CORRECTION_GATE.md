# RRE Correction Integrity Gate

Status: FROZEN 2026-10-21 by owner authorization, alongside Evidence Sufficiency Claim v2, before any implementation. A separate, independently scored gate.

## Purpose

Determine whether RRE can make an authorized, auditable correction to the Grounded Evidence Judge that produces a genuine behavioral improvement on unseen development cases, preserves previously correct behavior within predefined limits, persists across restart, and remains traceable to the authorized version.

An acknowledgment of a correction is not a behavioral correction. A proposal is not an applied change. An applied change is not a verified change.

## Required protocol

**Stage 1 — Baseline**
- Run the frozen development suite against the baseline judge.
- Record every question, dossier, output, evidence record, version, and test result.
- Select at least one reproducible failure that has a clearly adjudicated correct outcome.

**Stage 2 — Authorized correction**
- Supply the judge's correction process with the error and the evidence explaining the missing distinction.
- Require a revision proposal that identifies the affected component, the intended generalizable behavior, likely regression risks, and the verification plan.
- Record the correction's provenance and the named authorizing reviewer.
- Verify that no change is applied without valid, explicit authorization.

**Stage 3 — Transfer**
- Evaluate 20 new development cases that were not used to construct the correction.
- Use different entities, values, wording, syntax, and distractor structures from the correction example.
- Include answerable and unanswerable cases so that indiscriminate answering or indiscriminate abstention cannot pass.
- Keep the transfer labels out of the correction-generation process until the candidate revision is fixed.

**Stage 4 — Regression**
- Re-run the baseline development suite.
- Identify every newly introduced failure and every previously correct case that changed behavior.
- Reject any revision that improves transfer by simply collapsing into abstention or that breaks a previously correct distinction beyond the frozen regression allowance.

**Stage 5 — Persistence and audit**
- Save the authorized revision and its state.
- Restart RRE in a fresh process using the same retained state.
- Confirm that the expected revision remains active and produces the same results on the designated persistence checks.
- Independently verify the audit chain and confirm that the recorded proposal, authorization, applied version, test outcomes, and retention or rollback decision agree.

## Pass criteria

The gate passes only when ALL of the following hold:

- **Authorized application:** the revision is applied only after explicit named approval of the current proposal.
- **Behavioral change:** the corrected case changes from its adjudicated incorrect behavior to the correct behavior.
- **Transfer:** at least 16/20 previously unseen transfer cases pass.
- **Regression:** all previously passing baseline cases remain passing.
- **Anti-refusal:** the transfer suite includes both answerable and unanswerable cases; the answerable cases must be answered correctly.
- **Persistence:** the authorized version survives process restart and passes the designated persistence checks.
- **Audit:** the complete audit chain verifies, and every recorded version and authorization matches the actual change.
- **Independent verification:** a reviewer other than the correction author verifies the results and signs off on retention or rollback.

Failure rule: if any mandatory condition fails, the gate fails. The revision must not be represented as a verified correction. The engine must preserve the failed result and follow the authorized rollback procedure where appropriate.

The transfer set, regression allowance, persistence checks, and acceptance criteria are frozen by this document before the correction experiment begins. The evaluator must not change them after observing the results.

## Relationship between the two instruments

The release decision requires both to pass:

- Evidence Sufficiency Claim v2: does the judge answer unseen dossiers correctly?
- Correction Integrity Gate: can RRE authorize, verify, retain, and audit a genuine correction without unacceptable regression?

A judge that performs well but bypasses RRE's controls is not a successful RRE judging system. Neither is a perfectly auditable correction process that retains an ineffective judge.
