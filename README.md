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

## Execution record

The specification was delivered unexecuted — its author stated plainly that the files had not been created or tested on their side. On publication, the files were saved exactly as delivered and run here:

- 2026-10-18, Python 3.12.3: `python3 rre_minimal.py` → all three PASS lines, exit 0.
- 2026-10-18, Python 3.12.3: `python3 test_rre_minimal.py` → `ALL ASSERTIONS PASSED`, exit 0.
- 2026-10-19, Python 3.12.3: a revised Prototype 0.1 build (expanded implementation, four named tests, 18-event demonstration audit) was delivered and run here: demo exit 0 with all PASS lines; `python3 test_rre_minimal.py` → `ALL 4 TESTS PASSED`, exit 0. The audit produced by this run is byte-identical to the author's shipped `demo_audit.jsonl`.

That verifies the delivered code runs, passes its own tests, and reproduces its recorded demonstration exactly. It is **not** an independent evaluation: the tests are the implementation's own, the cases are the demonstration cases and the implementation's internal held-out probes, and no evaluator independent of the author has designed or run additional cases. See SPEC.md §F for what a real evaluation requires.

## What is missing or unverified

Named plainly, so nobody has to guess:

- **Audit-history reset** — not implemented.
- **Real rollback** — per-version rule snapshots exist in the implementation; a tested rollback path is not implemented.
- **Authenticated authorization** — not implemented; `approved_by` is a named label, not an authenticated identity.
- **Independent evaluation** — not performed. The test suite passes locally (see the execution record), but its cases are the implementation's own; the passing result is a reproduction, not an independent evaluation.

## Development

This repository will be updated as RRE develops, preserving the progression from the initial prototype to the tested implementation. Commits land on top of the existing history; the early prototype is never silently replaced.

## License

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (`CC BY-NC-SA 4.0`). See [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md).
