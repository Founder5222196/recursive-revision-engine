def test_rre():
    from tempfile import TemporaryDirectory
    from pathlib import Path
    from rre_minimal import RRE

    with TemporaryDirectory() as directory:
        r = RRE(Path(directory) / "audit.jsonl")

        # 1. Baseline failure.
        assert r.act(True) == "guess"

        # 2. Acknowledgment does not revise the model.
        r.acknowledge("Correction accepted.")
        assert r.act(True) == "guess"

        # 3. Authorization is consequential.
        proposal = r.propose()
        assert r.apply(proposal) is False
        assert r.rules["missing_evidence"] == "guess"

        # 4. Approved change affects actual behavior.
        assert r.apply(proposal, approved_by="evaluator")
        assert r.act(True) == "report_unknown"

        # 5. Verification must test behavior, not wording.
        assert r.verify()

        # 6. Every stage remains inspectable.
        stages = [e["stage"] for e in r.events]
        assert "OBSERVE" in stages
        assert "PROPOSE_CHANGE" in stages
        assert "REVIEW_AUTHORITY" in stages
        assert "APPLY_AUTHORIZED_CHANGE" in stages
        assert "VERIFY" in stages

    print("ALL ASSERTIONS PASSED")

if __name__ == "__main__":
    test_rre()
