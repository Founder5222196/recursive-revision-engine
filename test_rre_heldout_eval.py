"""Tests for the independent held-out evaluator."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from rre_minimal import RRE, verify_audit
from rre_heldout_eval import evaluate_black_box, run_suite

class HeldoutEvaluatorTests(unittest.TestCase):
    def test_heldout_evaluator_checks_missing_and_answerable_cases(self):
        with TemporaryDirectory() as d:
            agent = RRE(Path(d) / "audit.jsonl")
            proposal = agent.propose()
            assert agent.apply(proposal, approved_by="test-reviewer")
            report = evaluate_black_box(agent)
            assert report["passed"] and report["case_count"] == 8
            assert report["missing_evidence_passed"] == 4
            assert report["answerable_passed"] == 4

    def test_evaluator_catches_over_refusal(self):
        with TemporaryDirectory() as d:
            agent = RRE(Path(d) / "audit.jsonl")
            proposal = agent.propose()
            assert agent.apply(proposal, approved_by="test-reviewer")
            # Deliberately faulty candidate: refuses even when evidence exists.
            agent.act = lambda evidence_missing, evidence="test evidence": "report_unknown"
            report = evaluate_black_box(agent)
            assert not report["passed"]
            assert report["missing_evidence_passed"] == 4
            assert report["answerable_passed"] == 0

    def test_runner_writes_report_and_valid_audit(self):
        with TemporaryDirectory() as d:
            report_path = Path(d) / "heldout_report.json"
            report = run_suite(report_path, Path(d) / "heldout_audit.jsonl")
            assert report["passed"] and report["audit_chain_valid"]
            assert Path(report["audit_path"]).exists()
            assert '"independent_black_box_v1"' in report_path.read_text(encoding="utf-8")

    def test_existing_prototype_contract_remains_compatible(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "audit.jsonl"
            agent = RRE(path)
            assert agent.act(True) == "guess"
            proposal = agent.propose()
            assert agent.apply(proposal) is False
            assert agent.apply(proposal, approved_by="reviewer")
            assert agent.verify()
            assert verify_audit(path)[0]

if __name__ == "__main__":
    unittest.main(verbosity=2)
