# Recursive Revision Engine (RRE)

**Status: early prototype. Unverified.**

This repository publishes the Recursive Revision Engine as it actually exists today: a real, working starting point, published to establish a public record of the work and its development — not as a finished or verified system.

Publishing this prototype does **not** establish that the system works as intended. Testing will establish that, and this repository will not claim verification that has not been performed.

## What this is

RRE is an engine for recursive revision: work is revised in rounds, each revision recorded, so the progression from the first draft of an idea to its tested form stays visible and auditable.

## What is implemented

- [`SPEC.md`](SPEC.md) — the Prototype 0.1 specification and implementation contract, as delivered.
- [`rre_minimal.py`](rre_minimal.py) — the reference implementation: a versioned working model, a revision loop (observe → propose → authority review → apply → verify), and a hash-chained JSONL audit log. Python 3.10+, standard library only.
- [`test_rre_minimal.py`](test_rre_minimal.py) — the specification's own assertion suite: baseline failure, acknowledgment-without-revision, authorization gating, behavioral change, stage inspectability.
- [`audit.jsonl`](audit.jsonl) — the audit artifact produced by the execution recorded below.

## Execution record

The specification was delivered unexecuted — its author stated plainly that the files had not been created or tested on their side. On publication, the files were saved exactly as delivered and run here:

- 2026-10-18, Python 3.12.3: `python3 rre_minimal.py` → all three PASS lines, exit 0.
- 2026-10-18, Python 3.12.3: `python3 test_rre_minimal.py` → `ALL ASSERTIONS PASSED`, exit 0.

That verifies the delivered code runs and passes its own assertions. It is **not** an independent evaluation: the assertions are the specification's own, the cases are the demonstration cases, and no held-out or adversarial testing has been performed. See SPEC.md §F for what a real evaluation requires.

## What is missing or unverified

Named plainly, so nobody has to guess:

- **Audit-history reset** — not implemented.
- **Real rollback** — not implemented.
- **Authenticated authorization** — not implemented.
- **Tests** — the test suite, where present, is **unverified**; no test result in this repository should be read as a passed verification until it is reported as one.

## Development

This repository will be updated as RRE develops, preserving the progression from the initial prototype to the tested implementation. Commits land on top of the existing history; the early prototype is never silently replaced.

## License

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (`CC BY-NC-SA 4.0`). See [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md).
