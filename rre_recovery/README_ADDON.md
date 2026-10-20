# RRE persistence and adversarial rollback add-on

This add-on keeps `rre_minimal.py` and `test_rre_minimal.py` unchanged. It adds `rre_persistent.py`, a named `unittest` suite, a v0.2-compatible eight-case evaluator, and generated artifacts under `artifacts/`.

## Run

Requires Python 3.10+ and standard library only:

```sh
python test_rre_minimal.py
python -m unittest -v test_rre_persistent.py
python run_milestone.py
```

The durable working state is an atomically replaced JSON snapshot; the audit is append-only JSONL with SHA-256 chained events. A candidate is staged and behaviorally evaluated before any state commit. Failed candidates leave the durable working version unchanged. Acknowledgment, acceptance, and candidate labels do not override the evaluator.

## Important provenance note

The accessible Library contained `rre_minimal.py` and `test_rre_minimal.py`, but did not return the previous `rre_heldout_eval.py` source or its ZIP. Therefore the included `rre_heldout_eval.py` is reconstructed from the previous conversation's stated protocol (four missing-evidence cases plus four answerable cases), not represented as byte-identical recovery of that prior file. No independent evaluator owns these tests; authorship and evaluation remain within this project session.
