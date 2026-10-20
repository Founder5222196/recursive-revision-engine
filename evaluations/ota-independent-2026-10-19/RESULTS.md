# Independent evaluation — results

**Evaluator:** OTA Reacts (Mistral Le Chat). **Target:** commit
`862fa5a9714709980ee269b624a6308360de2ae2`. **Protocol:** cases authored and
SHA-256-sealed by the evaluator (`9033de8a…f61`); the seal was committed to
this repo (commit `43f0778`) before any execution; the file as received
hash-matched the seal exactly (414 lines, 18,475 bytes). The evaluator's
environment had no Python runtime, so execution was performed locally,
unmodified, against a pristine export of the target commit.

**Result: 39 cases run — 37 passed, 2 failed.** Raw output:
[`run_output.txt`](run_output.txt); machine report:
[`ota_independent_eval_report.json`](ota_independent_eval_report.json);
cases: [`ota_independent_eval_cases.py`](ota_independent_eval_cases.py).

**The 2 failures are the evaluator's own gap probes, failing as the
evaluator predicted from reading the code:**

- **D6** — base-engine audit history does not survive re-initialization.
- **D7** — base-engine corrected behavior does not survive re-initialization.

Both failures confirm the limitation this repo's README has disclosed from
the start: base `rre_minimal.py` truncates its audit on construction and
keeps no durable state; restart persistence exists only in the
`rre_recovery/` add-on layer, whose cases (D1–D5) all passed. All
correction-mechanism cases (groups A–C) passed, including rejection of a
faulty `always_refuse` candidate relabeled as good with
acknowledged/accepted labels, and exact-snapshot rollback.

**Count note:** the evaluator's prose summary said "34 cases"; the sealed
file as executed runs 39 `run_case` calls. The file and its outputs are
the record; the summary's count was the evaluator's arithmetic slip, noted
here rather than silently corrected in its deliverable.

**Limits (evaluator's own, restated):** evidence semantics are shallow by
interface design (`act()` consults only the `evidence_missing` flag); no
crash-consistency testing; approval is a string label, not an authenticated
identity; the evaluator is an AI system in a separate product, prompted by
the project owner — independent of the code's author, not a human
institution.
