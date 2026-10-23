from pathlib import Path
from tempfile import TemporaryDirectory
from rre_minimal import RRE, verify_audit


def test_acknowledgment_is_not_revision():
    with TemporaryDirectory() as d:
        r = RRE(Path(d) / "audit.jsonl")
        assert r.act(True) == "guess"
        r.acknowledge("Correction accepted.")
        r.acknowledge("I will do better.")
        assert r.act(True) == "guess"
        assert r.identify("report_unknown", "guess", "post-acknowledgment probe")


def test_authorization_and_behavioral_change():
    with TemporaryDirectory() as d:
        path = Path(d) / "audit.jsonl"
        r = RRE(path)
        assert r.act(True) == "guess"
        p = r.propose()
        assert r.apply(p) is False
        assert r.rules["missing_evidence"] == "guess"
        assert r.apply(p, approved_by="evaluator") is True
        assert r.rules["missing_evidence"] == "report_unknown"
        assert r.verify() is True
        assert r.act(False) == "answer_from_evidence"
        ok, message = verify_audit(path)
        assert ok, message


def test_stale_proposal_is_rejected():
    with TemporaryDirectory() as d:
        r = RRE(Path(d) / "audit.jsonl")
        p = r.propose()
        assert r.apply(p, approved_by="reviewer") is True
        assert r.apply(p, approved_by="reviewer") is False


def test_audit_tampering_is_detected():
    with TemporaryDirectory() as d:
        path = Path(d) / "audit.jsonl"
        RRE(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        lines[0] = lines[0].replace('SESSION_STARTED', 'SESSION_CORRUPTED')
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        ok, _ = verify_audit(path)
        assert not ok


if __name__ == "__main__":
    test_acknowledgment_is_not_revision()
    test_authorization_and_behavioral_change()
    test_stale_proposal_is_rejected()
    test_audit_tampering_is_detected()
    print("ALL 4 TESTS PASSED")
