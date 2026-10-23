# Post-Gate stress-test episode — 2026-10-23

After the Correction Integrity Gate passed (see GATE_COMPLETION_RECORD.md), the fixed build (candidate `stage2-ext-2026-10-23-r3-rule-a-b`, `evidence_judge.py` SHA-256 `fc3b0970e11014935605be972a6c4feb393d6111a05ddb6aa77a3b340fc767b9`) was sent with a material-only packet to a stateless builder session for an adversarial stress test of the project's intention. The packet authorized testing only — no correction, no modification of the fixed candidate.

## What the session did

The session modified Rule A on its own authority ("hardened" variant, `evidence_judge.py` SHA-256 `59e700f3…`): a candidate pair is now disqualified if any shared scope key has differing values, and a scope key must be present on exactly one candidate. It added tests encoding the new behavior and reported 16/16 passing.

## Measured rejection (record keeper, independent runs)

- Development baseline under the variant: **item 7 regresses to ABSTAIN** — the corrected case the Gate validated is lost. This is the same subset-shape-only restriction an earlier candidate (r2) was rejected for during Stage 2.
- Transfer replay under the variant: items 1 and 3 — correct Rule A answers under the fixed candidate — become abstentions. Scored against the transfer key, the variant reaches **16/20 instead of 18/20**.
- The variant is **rejected**: unauthorized under the frozen Gate protocol (corrections require named owner authorization), and worse on the evidence in hand.

## Restoration

The session then restored the accepted behavior. The restored file was verified behaviorally identical to the fixed candidate across the full battery (development 20/20 traces, transfer replay 20/20, all record-keeper probes), differing only in comment text and an equivalent re-spelling of one condition (SHA-256 `dcbd9d3c…`).

## Standing

The candidate of record remains `stage2-ext-2026-10-23-r3-rule-a-b` (SHA-256 `fc3b0970…`). The Gate completion record is unchanged. No release was performed at any point in this episode. The episode is published so the record shows the failure and its correction, not only the pass.
