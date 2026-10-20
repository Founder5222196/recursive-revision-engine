# Independent re-evaluation (round two) — results

**Evaluator:** OTA Reacts (Mistral Le Chat). **Target:** commit
`c218b5ff4fb5e4e72262f04aff012db9e32ffc95`. **Protocol:** fresh seal
(`09bc12a2…f190`, committed as `dea7d37` before execution); the file as
received hash-matched the seal exactly (25,946 bytes); executed unmodified
against a pristine export of the target commit. Raw output:
[`run_output_r2.txt`](run_output_r2.txt); machine report:
[`ota_independent_eval_report_r2.json`](ota_independent_eval_report_r2.json);
cases: [`ota_independent_eval_cases_r2.py`](ota_independent_eval_cases_r2.py).

**Result: 45 cases run — 44 passed, 1 failed.**

**The deciding cases all passed.** D6 (base-engine audit history survives
re-initialization, byte-prefix preserved, chain valid) and D7 (corrected
behavior survives re-initialization) — the two round-one failures this
build existed to answer — now **PASS** under the fresh seal, as do D8, D9,
and the evaluator's two new probes of the fix: D10 (state rebuilt from the
audit alone when the sidecar is deleted) and D11 (constructor refuses a
corrupted audit and leaves it byte-identical). Import binding R1/R2
passed: the base engine tested was the repository-root `rre_minimal.py`.

**The one failure — D1 — is a new, real finding, and it is not a restart
failure.** D1 requires the post-restart snapshot to equal both the
pre-Group-C durable snapshot and the live pre-restart object's snapshot.
Forensics (an instrumented *copy* of the harness was used for diagnosis;
the sealed file was never modified): the post-restart snapshot **equals
the durable pre-Group-C snapshot exactly** — restart restore is correct.
The mismatch is the live object: during case C6 (the malformed empty
candidate `commit_candidate({})`), the live `PersistentRRE` instance's
in-memory rules were emptied to `{}` even though the candidate was
rejected and the durable state file was never touched (C6's own checks
passed, including its snapshot-equality sub-check, which did not detect
the mutation). A restart heals the divergence; a live object that kept
serving after an empty candidate would be running on emptied rules.
Round one's D1 formulation did not compare against the live post-Group-C
object, so this defect was invisible until the stricter round-two case
caught it. Pinpointing the exact internal mechanism is the builder's
work; the behavioral fact above is established by the sealed run plus the
diagnostic trace.

**Standing after round two:** the base engine's restart gap (round one
D6/D7) is closed and independently confirmed. One new defect is on the
record: rejected empty candidates corrupt the persistent layer's
in-memory rules while durable state stays correct. Crash-consistency and
human/institutional evaluation remain unperformed, as stated in the main
README.
