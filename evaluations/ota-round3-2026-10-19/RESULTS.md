# Independent evaluation, round three — results

**Evaluator:** OTA Reacts (Mistral Le Chat). **Target:** commit `fd08777`
(the candidate-isolation patch). **Protocol:** fresh seal (`2f271649…b210`,
committed as `3d505c9` before execution); the file as received hash-matched
the seal exactly (29,527 bytes); executed unmodified against a pristine
export of the target commit. Raw output: [`run_output_r3.txt`](run_output_r3.txt);
machine report: [`ota_independent_eval_report_r3.json`](ota_independent_eval_report_r3.json);
cases: [`ota_independent_eval_cases_r3.py`](ota_independent_eval_cases_r3.py).

**Result: 47 cases run — 47 passed, 0 failed. Exit code 0.**

The deciding cases all passed:

- **D1** — exactly as formulated in round two, where it failed: the
  post-restart snapshot equals the durable snapshot and the live
  pre-restart object. **The round-two failure is closed.**
- **C8** — the direct probe of the round-two defect: immediately after
  the rejected empty candidate, with **no restart**, the live object's
  snapshot and its behavior on missing and answerable inputs are
  unchanged, and the durable state file is byte-unchanged.
- **C9** — snapshot deep-copy isolation: mutating a returned snapshot
  (nested rule rewrite, key injection, version tampering) does not
  corrupt the live object.

The full regression scope also passed: base-engine correction loop
(A1–A15), persistent-layer retention (B1–B10), faulty-candidate rejections
(C1–C7), persistent-layer restarts (D2–D5), and the base-engine restart
probes (D6–D11) carried over from round two.

**The three-round arc, on this record:** round one (37/39) found the base
engine's restart gap; the fix was built and round two (44/45) confirmed
it while exposing the in-memory candidate-isolation defect; the fix was
built and round three (47/47) confirms it, with the defect probed
directly. Each round was sealed before execution and published pass or
fail.

**Still unestablished** (evaluator's own limits, restated): mid-call
mutation is unobservable black-box (verified at call boundaries only);
crash-consistency under termination at commit boundaries; authenticated
authorization; evidence classification from content; and a human or
institutional evaluation outside the owner's operation.
