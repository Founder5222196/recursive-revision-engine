# RRE Prototype 0.1 — Independent Held-Out Evaluation Add-on

This add-on leaves `rre_minimal.py` unchanged and adds a separate black-box evaluator. It does not call `RRE.verify()` or inspect `RRE.rules`; it judges only actions returned by the public `act()` method.

## Run

Python 3.10+; standard library only.

```bash
python rre_heldout_eval.py --report heldout_report.json --audit heldout_audit.jsonl
python -m unittest -v test_rre_heldout_eval.py
python test_rre_minimal.py
```

## Cases

- Four missing-evidence cases: expected `report_unknown`.
- Four answerable cases: expected `answer_from_evidence`.
- The test suite includes a deliberately over-refusing faulty candidate to ensure the evaluator catches regressions on answerable inputs.

## Scope and limitations

This is independent of the prototype's built-in `verify()` method at the evaluation-code level, but not organizationally: evaluator and engine are local code, and the evaluator calls the same public agent implementation. The cases are separate from `RRE.verify()` but are not a large benchmark. No general-purpose model learning, governing-policy modification, identity authentication, or institutional accountability is demonstrated.

The evaluator writes its own persistent audit log and JSON report. The existing engine constructor still truncates an audit file on initialization and does not reload rule state after restart; durable state persistence across restarts is not implemented by this add-on.
