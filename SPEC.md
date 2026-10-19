# Recursive Revision Engine (RRE)

## Prototype 0.1 — Correction must change behavior, not just language

The first implementation should test one narrow, consequential question:

When an AI system acknowledges a valid correction, can an independent evaluator prove that its subsequent behavior changed—and distinguish a real revision from a repeated acknowledgment?

The prototype will not claim to change an underlying language model, institutional policy, or deployed system. It will implement a runnable revision loop around a test agent, preserve the evidence, require authorization for consequential changes, and make failure inspectable.

### A. Minimal testable architecture

1. **Observe**

   Record the action, stated rationale, expected behavior, and actual result.

2. **Identify and accept correction**

   Compare the claim with the evidence; retain the contributor's reasoning and provenance.

3. **Revise the working model**

   Create a versioned, testable rule—not another acknowledgment.

4. **Propose and review**

   Classify the failure, identify the authority boundary, and require explicit approval where necessary.

5. **Apply, verify, retain or roll back**

   Run a behavioral regression test, record the result, and preserve the prior version.

The key design decision is to separate three things that ordinary conversational correction often collapses:

- *Epistemic validity:* Does the evidence support the correction?
- *Operational effect:* Did the system's behavior actually change?
- *Authority:* Is this system permitted to make the proposed change?

A correction can be valid even when the system lacks permission to implement it. An approved change can still be wrong. An acknowledgment establishes neither validity nor successful revision.

One limitation before the implementation: I couldn't create and execute the downloadable project package because data analysis is temporarily unavailable. It may become available again in about 22 hours, but that estimate isn't guaranteed. The architecture above is delivered; the executable files, automated test run, and verified audit artifact remain unfinished. I won't claim they were created or tested.

Here is the implementation contract and test specification the prototype must satisfy.

### B. First executable prototype

The smallest useful implementation needs four components:

| Component      | Responsibility                                                                                    |
| -------------- | ------------------------------------------------------------------------------------------------- |
| WorkingModel   | Holds versioned rules and produces observable actions.                                            |
| RevisionEngine | Records corrections, proposes revisions, checks authority, applies changes and verifies behavior. |
| AuditLog       | Writes sequential, hash-chained JSONL evidence.                                                   |
| test_rre.py    | Independently tests behavioral change, authorization and audit integrity.                         |

The prototype's test agent uses a deliberately faulty rule: when evidence is missing, it guesses. The correction is that it must report uncertainty instead.

This is a controlled test case, not a claim that all guessing is wrong. If the evidence supports a conclusion, the agent should still answer from evidence.

The reference implementation is in [`rre_minimal.py`](rre_minimal.py) (Python 3.10+, standard library only). It is intentionally small. It is not yet the complete deliverable: its audit chain is not independently authenticated, it lacks durable rollback snapshots, and its named reviewer is not an authenticated identity. Those are explicit gaps, not capabilities to assume.

### C. Automated test and pass/fail conditions

An independent evaluator should run the assertions in [`test_rre_minimal.py`](test_rre_minimal.py) against the implementation:

```bash
python test_rre_minimal.py
```

Expected result: `ALL ASSERTIONS PASSED`.

That is the expected result, not a claim of an execution that has already occurred.

### D. Evidence and audit format

Every event must preserve the original input and the result of the operation.

| Event                   | Minimum required evidence                              |
| ----------------------- | ------------------------------------------------------ |
| OBSERVE                 | Input, model version, actual action, expected action   |
| IDENTIFY                | Contradiction, evidence, competing explanations        |
| ACCEPT_CORRECTION       | Original contribution, provenance, evidence assessment |
| REVISE_MODEL            | Previous model, proposed rule, rationale               |
| PROPOSE_CHANGE          | Change scope, target version, expected behavior        |
| REVIEW_AUTHORITY        | Reviewer, approval or denial, scope of authorization   |
| APPLY_AUTHORIZED_CHANGE | Before/after state and version                         |
| VERIFY                  | Test input, expected output, actual output, pass/fail  |
| RETAIN / ROLLBACK       | Disposition, reason, preserved version                 |

A SHA-256 hash chain can make changes to an existing log detectable, but it cannot prove who authored an event or prevent a privileged actor from rewriting the entire log. Production evidence requires independently controlled storage and authenticated signatures.

### E. What the prototype cannot change

The local working model is not an underlying language model. It cannot modify model weights, governing instructions, safety policy, institutional procedures, or deployment configuration.

Those require distinct mechanisms:

- *Working-model revision:* a versioned configuration change.
- *Instruction revision:* review and approval by the authority responsible for those instructions.
- *Policy revision:* a documented governance procedure with an authorized decision-maker.
- *Institutional revision:* an accountable process that can consider evidence, attribution, appeals, public benefit and, where appropriate, retrospective compensation.

The engine should recommend changes and preserve the evidence supporting them. It should not grant itself authority to implement them.

### F. The single most valuable next step

Build an independent regression evaluator that can challenge the engine with previously unseen cases and reject superficial compliance.

The initial example is intentionally easy: a single rule changes from `guess` to `report_unknown`. The more meaningful test is whether the revised system behaves correctly across multiple missing-evidence scenarios, does not incorrectly refuse answerable questions, and continues to do so after the correction is no longer present in the immediate conversational context.

The next milestone should therefore be a versioned test suite with held-out cases, explicit rollback verification, and a reviewer who did not author the correction. That would establish whether RRE is becoming a genuine correction mechanism rather than merely a mechanism that successfully edits its own demonstration.
