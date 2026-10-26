# Recursive Revision Engine (RRE)

**Status: early prototype. Unverified.**

**Status update, 2026-10-26:** the Evidence Sufficiency v2 instrument in this repository has since been evaluated on a sealed, independently authored 100-dossier set and **passed (99/100)** — see [`evaluations/evidence-sufficiency-v2/RUN_RESULTS.md`](evaluations/evidence-sufficiency-v2/RUN_RESULTS.md). The line above describes the prototype as originally published; the record below it is the current one.

This repository publishes the Recursive Revision Engine as it actually exists today: a real, working starting point, published to establish a public record of the work and its development — not as a finished or verified system.

Publishing this prototype does **not** establish that the system works as intended. Testing will establish that, and this repository will not claim verification that has not been performed.

## What this is

RRE is an engine for recursive revision: work is revised in rounds, each revision recorded, so the progression from the first draft of an idea to its tested form stays visible and auditable.

## What is implemented

- [`SPEC.md`](SPEC.md) — the Prototype 0.1 specification and implementation contract, as delivered.
- [`rre_minimal.py`](rre_minimal.py) — the reference implementation: a versioned working model, a revision loop (observe → propose → authority review → apply → verify), per-version rule snapshots, and a hash-chained JSONL audit log with a standalone chain verifier. Python 3.10+, standard library only.
- [`test_rre_minimal.py`](test_rre_minimal.py) — four named tests: acknowledgment-is-not-revision, authority enforcement, stale proposals, and audit-chain tampering.
- [`test_rre_restart.py`](test_rre_restart.py) — the D6/D7 regression tests from the independent evaluation: restart preserves audit history; restart preserves corrected behavior.
- [`demo_audit.jsonl`](demo_audit.jsonl) — the author's shipped demonstration audit (18 hash-chained events).
- [`audit.jsonl`](audit.jsonl) — the audit artifact produced by the local execution recorded below. It is byte-identical to `demo_audit.jsonl`: the demonstration is deterministic, and running the code reproduces the author's recorded chain exactly.
- [`rre_heldout_eval.py`](rre_heldout_eval.py) — the v0.2 held-out evaluator add-on: a separate black-box evaluator that tests the agent through its public `act()` interface on held-out cases — missing-evidence cases (must report uncertainty) and answerable cases (must still answer) — and rejects a deliberately faulty always-refuse candidate. See [`README_RRE_0.2_eval.md`](README_RRE_0.2_eval.md).
- [`test_rre_heldout_eval.py`](test_rre_heldout_eval.py) — the evaluator's own test suite (4 tests). [`heldout_report.json`](heldout_report.json) and [`heldout_audit.jsonl`](heldout_audit.jsonl) are its generated report and 13-event audit chain; [`execution_results.json`](execution_results.json) is the author's recorded execution results.
- [`rre_recovery/`](rre_recovery/) — the persistence, adversarial-revision, and rollback milestone, filed as delivered: `rre_persistent.py` (durable versioned state, append-only audit, candidate verification, rollback), `test_rre_persistent.py` (7 named tests), `run_milestone.py`, and generated artifacts under `rre_recovery/artifacts/`. Note: the evaluator inside this package is a reconstruction of the v0.2 eight-case protocol — the builder documented that the original evaluator source was not recoverable on its side. The canonical v0.2 evaluator remains the root `rre_heldout_eval.py`, unchanged.
- [`evaluations/ota-independent-2026-10-19/`](evaluations/ota-independent-2026-10-19/) — the first independent evaluation: 39 sealed black-box cases authored by OTA Reacts (Mistral Le Chat), an evaluator that authored none of this code, hash-sealed and committed before execution. **37 passed, 2 failed** — the failures are the evaluator's gap probes confirming the disclosed base-engine restart limitation below. Full record in that directory.
- [`evaluations/ota-reevaluation-2026-10-19/`](evaluations/ota-reevaluation-2026-10-19/) — the round-two re-evaluation of the D6/D7 fix under a fresh seal: 45 cases, **44 passed, 1 failed**. The deciders D6/D7 (and new probes D10/D11) pass; the one failure, D1, exposed a new in-memory defect in the persistent layer (see that directory's RESULTS.md).
- [`evaluations/ota-round3-2026-10-19/`](evaluations/ota-round3-2026-10-19/) — the round-three re-evaluation of the candidate-isolation patch under a fresh seal: 47 cases, **47 passed, 0 failed**, D1 closed in its round-two formulation and the defect probed directly (C8/C9).
- [`evaluations/evidence-sufficiency-v1/`](evaluations/evidence-sufficiency-v1/) — the pre-registered judgment evaluation: a tightened, falsifiable claim (authored by Sol) and a frozen 20-dossier set with ground truth (A plainly present / B buried / C absent / D conflicting, 5 each), hash-sealed (`f4a1e052…47e9`, verified by independent reconstruction before commit). Pass requires ≥16/20 overall **and** ≥4/5 per category. No judging implementation exists yet; the claim stands in the record ahead of any build.
- **Candidate-isolation patch (2026-10-19, after round two):** `rre_recovery/rre_persistent.py` no longer installs candidate rules live during verification — candidates are verified in isolation, so a rejected candidate (including a malformed empty one, whose KeyError previously stranded the live rules as `{}`) cannot mutate live rules, version, or identity; `snapshot()` deep-copies. The persistent suite is now 11 tests, including four named isolation tests. The milestone audit trail is correspondingly shorter (22 events: verification probes are no longer written as live observations). Details in [`rre_recovery/README_PATCH.md`](rre_recovery/README_PATCH.md). The round-three fresh-seal re-evaluation has since confirmed the fix: **47/47** (see [`evaluations/ota-round3-2026-10-19/`](evaluations/ota-round3-2026-10-19/)), with D1 passing in its round-two formulation and the defect probed directly (C8/C9).

## Execution record

The specification was delivered unexecuted — its author stated plainly that the files had not been created or tested on their side. On publication, the files were saved exactly as delivered and run here:

- 2026-10-18, Python 3.12.3: `python3 rre_minimal.py` → all three PASS lines, exit 0.
- 2026-10-18, Python 3.12.3: `python3 test_rre_minimal.py` → `ALL ASSERTIONS PASSED`, exit 0.
- 2026-10-19, Python 3.12.3: a revised Prototype 0.1 build (expanded implementation, four named tests, 18-event demonstration audit) was delivered and run here: demo exit 0 with all PASS lines; `python3 test_rre_minimal.py` → `ALL 4 TESTS PASSED`, exit 0. The audit produced by this run is byte-identical to the author's shipped `demo_audit.jsonl`.
- 2026-10-19, Python 3.12.3: the v0.2 held-out evaluator add-on was delivered and run here: original tests still `ALL 4 TESTS PASSED`; `python3 -m unittest test_rre_heldout_eval.py` → 4 tests OK; the evaluator run scored 8/8 held-out cases (4/4 missing-evidence, 4/4 answerable) with its audit chain verified at 13 events. The locally generated report and audit are byte-identical to the author's shipped artifacts.
- 2026-10-19, Python 3.12.3: the persistence / adversarial-revision / rollback milestone (`rre_recovery/`) was delivered and run here: original tests still `ALL 4 TESTS PASSED` (both original files byte-identical to the versions in this repo); `test_rre_persistent.py` → 7 tests OK; the milestone runner exited 0 with its audit chain verified at 38 events and the post-rollback evaluator score preserved at 8/8. The locally regenerated milestone report and audit are byte-identical to the shipped artifacts.
- 2026-10-19, Python 3.12.3: the D6/D7 restart-persistence fix to `rre_minimal.py` was delivered and run here: original tests `ALL 4 TESTS PASSED`; `test_rre_restart.py` → PASS D6, PASS D7; the demo on a fresh path reproduces `demo_audit.jsonl` byte-identically (18 events) and now also writes an `audit.jsonl.state.json` sidecar; the v0.2 held-out evaluator on fresh paths still scores 8/8 with a 13-event chain. Two record notes: (1) re-running the v0.2 evaluator in place now *appends* to its existing audit file (resume semantics) instead of regenerating it, so its shipped artifacts are left as originally generated; (2) the sealed OTA harness resolves `rre_minimal` to the copy bundled in `rre_recovery/` (its `sys.path` order), so a valid re-evaluation must pin the root module — locally, with the root engine bound, the sealed cases pass 39/39; the formal fresh-seal re-evaluation followed: 45 cases, 44 passed — D6/D7 and the new D10/D11 probes pass; the single failure (D1) traced to a rejected empty candidate emptying the persistent layer's *in-memory* rules during case C6 while durable state stayed correct (the post-restart snapshot matched the durable snapshot exactly). That defect has since been fixed by the candidate-isolation patch recorded above and confirmed by the round-three evaluation (47/47 under a fresh seal, D1 and the direct defect probes C8/C9 passing).

That verifies the delivered code runs, passes its own tests, and reproduces its recorded demonstration exactly. At delivery it was **not** an independent evaluation: the tests were the implementation's own. An authorship-independent evaluation has since been run — see the `evaluations/` record below and the execution record.

## Verify it yourself

The two 2026-10-26 results recorded in this repository can be re-checked from a fresh clone:

- **Evidence Sufficiency Claim v2 — PASS, 99/100** ([`evaluations/evidence-sufficiency-v2/RUN_RESULTS.md`](evaluations/evidence-sufficiency-v2/RUN_RESULTS.md)). The released instrument's own suites: `cd builds/evidence-sufficiency-v2 && python3 -m unittest test_evidence_judge.py test_rre_minimal.py test_correction_integrity.py` → 13 tests, OK. The run was replay-verified by the record keeper before scoring: every extraction record binds by SHA-256 to the evaluator's sealed dossiers, and replaying the records through the released adapter reproduces all 100 verdicts exactly. The evaluation set and its key were never committed here (evaluator custody, per the v2 freeze design); RUN_RESULTS carries every item's binary outcome and the scoring adjudications.
- **Economic Governance Kernel v0.2** ([`builds/economic-governance-v0.2/`](builds/economic-governance-v0.2/)): `python3 -m unittest test_contribution_bridge.py test_economic_governance.py` in that directory → 31 tests, OK (21 governance + 10 prototype regression). Per-file SHA-256 values are in its `BUILD_MANIFEST.md`; the record keeper's execution is recorded in its `VERIFICATION.md`.

## What is missing or unverified

Named plainly, so nobody has to guess:

- **Audit-history reset** — not implemented.
- **Real rollback** — per-version rule snapshots exist in the implementation; a tested rollback path is not implemented.
- **Authenticated authorization** — not implemented; `approved_by` is a named label, not an authenticated identity.
- **Independent evaluation** — first performed 2026-10-19 by OTA Reacts (Mistral Le Chat), an AI system in a separate product that authored none of this code: 39 sealed cases, hash committed before execution, 37 passed / 2 failed (the failures confirm the base-engine restart gap). Still not performed: evaluation by a human or institution outside the owner's operation entirely.
- **Persistent state across restarts** — addressed in the `rre_recovery/` add-on layer, and since 2026-10-19 in the base engine itself: `rre_minimal.py` no longer truncates on initialization — it validates and continues the existing chain, and restores rules/version from an atomic-write `.state.json` sidecar (reconstructing from the audit history if the sidecar is missing). Fresh-path behavior is unchanged: the demo on a new path still reproduces `demo_audit.jsonl` byte-identically. This fix answers the independent evaluation's D6/D7 failures, and the fresh-seal re-evaluation has since confirmed it (round two, below): D6 and D7 pass, along with the evaluator's new D10/D11 probes of the fix itself.
- **Crash-consistency** — not performed. The milestone's own stated remaining step: termination injected at each commit boundary, proving recovery lands on a fully committed version, never a partially written state.

## Development

This repository will be updated as RRE develops, preserving the progression from the initial prototype to the tested implementation. Commits land on top of the existing history; the early prototype is never silently replaced.

## License

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (`CC BY-NC-SA 4.0`). See [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md).
