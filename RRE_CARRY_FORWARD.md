# RRE Carry Forward

## Revision 0.3 — A correction is not complete until it survives the next relevant case

The Recursive Revision Engine began with a narrower test:

> Can a system acknowledge a valid correction and then actually change its behavior?

That distinction remains necessary, but it is not sufficient.

A system may replay a correction correctly once, persist the revised rule, and still revert to the defeated model when a later analogous decision appears. RRE therefore distinguishes four revision states.

## Revision status

### Stated Correction

The corrected rule can be repeated in speech, text, or another explicit representation.

A Stated Correction proves only that the system can state the correction.

### Replayed Correction

The corrected rule produces the expected result when tested against the case that exposed the error, or a materially equivalent replay.

A Replayed Correction proves that the correction can govern the triggering case.

### Installed Revision

The corrected rule changes behavior when an analogous condition recurs through the system's normal execution path.

An Installed Revision proves that the correction is not confined to the original replay.

### Carried Revision

The installed correction remains operative in later relevant decisions without requiring the original contradiction, correction, or authorization to be repurchased.

A Carried Revision is defeated if the system silently resets to the prior rule when the same supported correction remains relevant.

## RRE sequence

```text
Contradiction
    ↓
Locate
    ↓
Revise
    ↓
Replay
    ↓
Persist
    ↓
Attest
    ↓
Carry Forward
```

The stages are evidentiary, not ceremonial.

- **Contradiction** — establish the mismatch between expected and actual behavior.
- **Locate** — identify the rule, assumption, state, or implementation that governed the failure.
- **Revise** — create the candidate correction.
- **Replay** — test the triggering case or a materially equivalent case.
- **Persist** — save the verified correction where normal execution will read it.
- **Attest** — preserve the contradiction, revision, verification evidence, scope, and unresolved questions.
- **Carry Forward** — test whether the supported correction governs later relevant decisions without an unjustified reset.

## Carry Forward test

A Carry Forward claim requires all of the following:

1. A correction was behaviorally verified.
2. The correction was persisted through the system's normal state path.
3. A later materially analogous case occurs without re-supplying the original correction as live instruction.
4. The corrected behavior governs that later case.
5. No new defeater has arisen that would justify narrowing, reopening, or replacing the correction.

The governing rule is:

> **Do not reset without a defeater. Do not preserve without evidence.**

Carry Forward does not create permanent truth. A later contradiction may reopen the revision. It prevents only an unexplained return to a model already defeated within the same scope.

## Relationship to the current implementation

The current root implementation already contains important prerequisites:

- `VERIFY` tests the corrected behavior.
- `RETAIN` preserves a verified revision.
- durable state restores the corrected rule after restart.
- `test_D7_restart_preserves_corrected_behavior` proves that the corrected behavior survives a restart.

Those results establish persistence across restart. They are evidence toward Carry Forward, but Carry Forward is a broader claim: the revision must continue governing later relevant decisions without requiring the original correction to be reintroduced.

`test_rre_carry_forward.py` adds that explicit regression test without changing the engine's event vocabulary or rewriting the historical Prototype 0.1 specification.

## Attestation boundary

Attestation records what the evidence establishes. It does not convert a successful replay into a larger claim than the tests support.

For the current prototype:

- a passing replay supports **Replayed Correction**;
- later analogous behavior through the normal execution path supports **Installed Revision**;
- persistence plus later relevant behavior without re-purchase supports **Carried Revision**.

Where the evidence stops, the status stops.

## Historical integrity

`SPEC.md` remains the published Prototype 0.1 contract. It is not silently rewritten to pretend Carry Forward was part of the original specification.

This file records the later conceptual revision on top of that history.
