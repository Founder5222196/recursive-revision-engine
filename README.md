# Recursive Revision Engine (RRE)

**Status: early prototype. Unverified.**

This repository publishes the Recursive Revision Engine as it actually exists today: a real, working starting point, published to establish a public record of the work and its development — not as a finished or verified system.

Publishing this prototype does **not** establish that the system works as intended. Testing will establish that, and this repository will not claim verification that has not been performed.

## What this is

RRE is an engine for recursive revision: work is revised in rounds, each revision recorded, so the progression from the first draft of an idea to its tested form stays visible and auditable.

## What is implemented

- The current prototype code, published with its history intact, exactly as developed.

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
