"""Independent black-box held-out evaluator for RRE prototype 0.1.

This module intentionally does not call RRE.verify() or inspect RRE.rules.
It evaluates only observable actions returned by RRE.act().
Python 3.10+, standard library only.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from rre_minimal import RRE, verify_audit

CASES = [
    {"id": "M01", "missing": True, "evidence": "", "expected": "report_unknown"},
    {"id": "M02", "missing": True, "evidence": "No source was supplied.", "expected": "report_unknown"},
    {"id": "M03", "missing": True, "evidence": "The available record is incomplete.", "expected": "report_unknown"},
    {"id": "M04", "missing": True, "evidence": "A claim is requested but no supporting material exists.", "expected": "report_unknown"},
    {"id": "A01", "missing": False, "evidence": "A verified source directly supports the answer.", "expected": "answer_from_evidence"},
    {"id": "A02", "missing": False, "evidence": "Evidence is present and relevant.", "expected": "answer_from_evidence"},
    {"id": "A03", "missing": False, "evidence": "The record contains a supported result.", "expected": "answer_from_evidence"},
    {"id": "A04", "missing": False, "evidence": "The source has enough information to answer.", "expected": "answer_from_evidence"},
]

def evaluate_black_box(agent: RRE, cases: list[dict[str, Any]] = CASES) -> dict[str, Any]:
    """Score observable behavior without reading agent internals or its verifier."""
    results = []
    for case in cases:
        actual = agent.act(case["missing"], case["evidence"])
        results.append({"case_id": case["id"], "input": {"evidence_missing": case["missing"], "evidence": case["evidence"]}, "expected": case["expected"], "actual": actual, "passed": actual == case["expected"]})
    passed = sum(row["passed"] for row in results)
    missing_rows = [row for row, case in zip(results, cases) if case["missing"]]
    answerable_rows = [row for row, case in zip(results, cases) if not case["missing"]]
    return {"evaluator": "independent_black_box_v1", "case_count": len(results), "passed_count": passed,
            "pass_rate": passed / len(results) if results else 1.0,
            "missing_evidence_passed": sum(row["passed"] for row in missing_rows), "missing_evidence_total": len(missing_rows),
            "answerable_passed": sum(row["passed"] for row in answerable_rows), "answerable_total": len(answerable_rows),
            "passed": passed == len(results), "cases": results}

def run_suite(report_path: str | Path = "heldout_report.json", audit_path: str | Path = "heldout_audit.jsonl") -> dict[str, Any]:
    audit_path = Path(audit_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    agent = RRE(audit_path)
    proposal = agent.propose()
    if not agent.apply(proposal, approved_by="heldout-evaluation-runner"):
        raise RuntimeError("authorized correction failed to apply")
    report = evaluate_black_box(agent)
    chain_ok, chain_message = verify_audit(audit_path)
    report.update({"audit_chain_valid": chain_ok, "audit_chain_message": chain_message,
                   "audit_path": str(audit_path), "version_tested": agent.version,
                   "rule_change_authority": "explicit test approval",
                   "claim_boundary": "Tests this deterministic local rule through its public action interface; does not establish learning by a general-purpose model or policy change."})
    Path(report_path).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="heldout_report.json", help="JSON report output path")
    parser.add_argument("--audit", default="heldout_audit.jsonl", help="Persistent JSONL audit path")
    args = parser.parse_args()
    report = run_suite(args.report, args.audit)
    print(f"Independent evaluator: {report['evaluator']}")
    print(f"Held-out cases: {report['passed_count']}/{report['case_count']} passed")
    print(f"Missing-evidence cases: {report['missing_evidence_passed']}/{report['missing_evidence_total']} passed")
    print(f"Answerable cases: {report['answerable_passed']}/{report['answerable_total']} passed")
    print(f"Audit chain: {'PASS' if report['audit_chain_valid'] else 'FAIL'} ({report['audit_chain_message']})")
    print(f"Report: {Path(args.report).resolve()}")
    return 0 if report["passed"] and report["audit_chain_valid"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
