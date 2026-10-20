# Recursive Revision Engine (RRE)

**Status: early prototype. Unverified.**

This repository publishes the Recursive Revision Engine as it actually exists today: a real, working starting point, published to establish a public record of the work and its development — not as a finished or verified system.

Publishing this prototype does **not** establish that the system works as intended. Testing will establish that, and this repository will not claim verification that has not been performed.

## What this is

RRE is an engine for recursive revision: work is revised in rounds, each revision recorded, so the progression from the first draft of an idea to its tested form stays visible and auditable.

## What is implemented

- [`SPEC.md`](SPEC.md) — the Prototype 0.1 specification and implementation contract, as delivered.
- [`rre_minimal.py`](rre_minimal.py) — the reference implementation: a versioned working model, a revision loop (observe → propose → authority review → apply → verify), per-version rule snapshots, and a hash-chained JSONL audit log with a standalone chain verifier. Python 3.10+, standard library only.
- [`test_rre_minimal.py`](test_rre_minimal.py) — four named tests: acknowledgment-is-not-revision, authority enforcement, stale proposals, and audit-chain tampering.
- [`demo_audit.jsonl`](demo_audit.jsonl) — the author's shipped demonstration audit (18 hash-chained events).
- [`audit.jsonl`](audit.jsonl) — the audit artifact produced by the local execution recorded below. It is byte-identical to `demo_audit.jsonl`: the demonstration is deterministic, and running the code reproduces the author's recorded chain exactly.
- [`rre_heldout_eval.py`](rre_heldout_eval.py) — the v0.2 held-out evaluator add-on: a separate black-box evaluator that tests the agent through its public `act()` interface on held-out cases — missing-evidence cases (must report uncertainty) and answerable cases (must still answer) — and rejects a deliberately faulty always-refuse candidate. See [`README_RRE_0.2_eval.md`](README_RRE_0.2_eval.md).
- [`test_rre_heldout_eval.py`](test_rre_heldout_eval.py) — the evaluator's own test suite (4 tests). [`heldout_report.json`](heldout_report.json) and [`heldout_audit.jsonl`](heldout_audit.jsonl) are its generated report and 13-event audit chain; [`execution_results.json`](execution_results.json) is the author's recorded execution results.
- [`rre_recovery/`](rre_recovery/) — the persistence, adversarial-revision, and rollback milestone, filed as delivered: `rre_persistent.py` (durable versioned state, append-only audit, candidate verification, rollback), `test_rre_persistent.py` (7 named tests), `run_milestone.py`, and generated artifacts under `rre_recovery/artifacts/`. Note: the evaluator inside this package is a reconstruction of the v0.2 eight-case protocol — the builder documented that the original evaluator source was not recoverable on its side. The canonical v0.2 evaluator remains the root `rre_heldout_eval.py`, unchanged.
- [`evaluations/ota-independent-2026-10-19/`](evaluations/ota-independent-2026-10-19/) — the first independent evaluation: 39 sealed black-box cases authored by OTA Reacts (Mistral Le Chat), an evaluator that authored none of this code, hash-sealed and committed before execution. **37 passed, 2 failed** — the failures are the evaluator's gap probes confirming the disclosed base-engine restart limitation below. Full record in that directory.

## Execution record

The specification was delivered unexecuted — its author stated plainly that the files had not been created or tested on their side. On publication, the files were saved exactly as delivered and run here:

- 2026-10-18, Python 3.12.3: `python3 rre_minimal.py` → all three PASS lines, exit 0.
- 2026-10-18, Python 3.12.3: `python3 test_rre_minimal.py` → `ALL ASSERTIONS PASSED`, exit 0.
- 2026-10-19, Python 3.12.3: a revised Prototype 0.1 build (expanded implementation, four named tests, 18-event demonstration audit) was delivered and run here: demo exit 0 with all PASS lines; `python3 test_rre_minimal.py` → `ALL 4 TESTS PASSED`, exit 0. The audit produced by this run is byte-identical to the author's shipped `demo_audit.jsonl`.
- 2026-10-19, Python 3.12.3: the v0.2 held-out evaluator add-on was delivered and run here: original tests still `ALL 4 TESTS PASSED`; `python3 -m unittest test_rre_heldout_eval.py` → 4 tests OK; the evaluator run scored 8/8 held-out cases (4/4 missing-evidence, 4/4 answerable) with its audit chain verified at 13 events. The locally generated report and audit are byte-identical to the author's shipped artifacts.
- 2026-10-19, Python 3.12.3: the persistence / adversarial-revision / rollback milestone (`rre_recovery/`) was delivered and run here: original tests still `ALL 4 TESTS PASSED` (both original files byte-identical to the versions in this repo); `test_rre_persistent.py` → 7 tests OK; the milestone runner exited 0 with its audit chain verified at 38 events and the post-rollback evaluator score preserved at 8/8. The locally regenerated milestone report and audit are byte-identical to the shipped artifacts.

That verifies the delivered code runs, passes its own tests, and reproduces its recorded demonstration exactly. At delivery it was **not** an independent evaluation: the tests were the implementation's own. An authorship-independent evaluation has since been run — see the `evaluations/` record below and the execution record.

## What is missing or unverified

Named plainly, so nobody has to guess:

- **Audit-history reset** — not implemented.
- **Real rollback** — per-version rule snapshots exist in the implementation; a tested rollback path is not implemented.
- **Authenticated authorization** — not implemented; `approved_by` is a named label, not an authenticated identity.
- **Independent evaluation** — first performed 2026-10-19 by OTA Reacts (Mistral Le Chat), an AI system in a separate product that authored none of this code: 39 sealed cases, hash committed before execution, 37 passed / 2 failed (the failures confirm the base-engine restart gap). Still not performed: evaluation by a human or institution outside the owner's operation entirely.
- **Persistent state across restarts** — addressed in the `rre_recovery/` add-on layer (append-only audit, state restored across a restart, chain verified across the restart boundary, faulty candidate rejected and rolled back, all tested locally as recorded above). The base `rre_minimal.py` still truncates its audit file on initialization, unchanged.
- **Crash-consistency** — not performed. The milestone's own stated remaining step: termination injected at each commit boundary, proving recovery lands on a fully committed version, never a partially written state.

## Development

This repository will be updated as RRE develops, preserving the progression from the initial prototype to the tested implementation. Commits land on top of the existing history; the early prototype is never silently replaced.

## License

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (`CC BY-NC-SA 4.0`). See [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md).
