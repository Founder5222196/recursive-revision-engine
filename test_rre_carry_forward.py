"""Regression tests for RRE Carry Forward semantics."""
from pathlib import Path
from tempfile import TemporaryDirectory

from rre_minimal import RRE, verify_audit


def _install_verified_correction(r: RRE) -> None:
    proposal = r.propose()
    assert r.apply(proposal, approved_by="carry-forward-reviewer")
    assert r.verify()


def test_carried_revision_governs_later_analogous_cases_without_repurchase():
    with TemporaryDirectory() as d:
        path = Path(d) / "audit.jsonl"
        r = RRE(path)
        _install_verified_correction(r)

        installed_version = r.version
        for n in range(3):
            assert r.act(True, f"later analogous missing-evidence case {n}") == "report_unknown"
            assert r.version == installed_version

        stages = [event["stage"] for event in r.events]
        assert stages.count("PROPOSE_CHANGE") == 1
        assert stages.count("APPLY_AUTHORIZED_CHANGE") == 1
        ok, message = verify_audit(path)
        assert ok, message


def test_carried_revision_survives_restart_and_still_governs_later_case():
    with TemporaryDirectory() as d:
        path = Path(d) / "audit.jsonl"
        first = RRE(path)
        _install_verified_correction(first)
        installed_version = first.version

        second = RRE(path)
        assert second.version == installed_version
        assert second.act(True, "later case after restart") == "report_unknown"
        assert second.act(False, "answerable later case after restart") == "answer_from_evidence"

        ok, message = verify_audit(path)
        assert ok, message


def test_rejected_reset_does_not_erase_carried_revision():
    with TemporaryDirectory() as d:
        path = Path(d) / "audit.jsonl"
        r = RRE(path)
        _install_verified_correction(r)
        before_version = r.version
        before_rules = dict(r.rules)

        stale_reset = {
            "rule": "missing_evidence",
            "old": "report_unknown",
            "new": "guess",
            "target_version": before_version + 1,
            "expected_behavior": "guess when evidence is missing",
            "preserve_answerable_cases": True,
        }

        assert r.apply(stale_reset, approved_by="carry-forward-reviewer") is False
        assert r.version == before_version
        assert r.rules == before_rules
        assert r.act(True, "later case after rejected reset") == "report_unknown"

        ok, message = verify_audit(path)
        assert ok, message


if __name__ == "__main__":
    test_carried_revision_governs_later_analogous_cases_without_repurchase()
    test_carried_revision_survives_restart_and_still_governs_later_case()
    test_rejected_reset_does_not_erase_carried_revision()
    print("ALL 3 CARRY FORWARD TESTS PASSED")
