"""Named regression tests for independent evaluation failures D6 and D7."""
from pathlib import Path
from tempfile import TemporaryDirectory
from rre_minimal import RRE, verify_audit


def test_D6_restart_preserves_audit_history():
    with TemporaryDirectory() as d:
        path = Path(d) / "audit.jsonl"
        first = RRE(path)
        first.act(True)
        original = path.read_text(encoding="utf-8")
        original_count = len(first.events)
        second = RRE(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[:original_count] == original.splitlines(), "existing audit bytes/lines were changed"
        assert len(lines) == original_count + 1, "resume must append, not replace, session event"
        ok, message = verify_audit(path)
        assert ok, message
        assert second.events[-1]["sequence"] == original_count + 1


def test_D7_restart_preserves_corrected_behavior():
    with TemporaryDirectory() as d:
        path = Path(d) / "audit.jsonl"
        first = RRE(path)
        proposal = first.propose()
        assert first.apply(proposal, approved_by="regression-reviewer")
        assert first.version == 2
        assert first.act(True) == "report_unknown"
        second = RRE(path)
        assert second.version == 2
        assert second.rules["missing_evidence"] == "report_unknown"
        assert second.act(True) == "report_unknown"
        assert second.act(False) == "answer_from_evidence"
        ok, message = verify_audit(path)
        assert ok, message


if __name__ == "__main__":
    test_D6_restart_preserves_audit_history()
    print("PASS D6: restart preserves audit history")
    test_D7_restart_preserves_corrected_behavior()
    print("PASS D7: restart preserves corrected behavior")
