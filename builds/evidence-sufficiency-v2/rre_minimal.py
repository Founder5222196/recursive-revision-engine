"""Recursive Revision Engine prototype 0.1.

A small, deterministic correction loop. Standard library only; Python 3.10+.
The engine changes only its local working rule, never an underlying model or policy.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class RRE:
    def __init__(self, audit_path: str | Path = "audit.jsonl"):
        self.path = Path(audit_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path = self.path.with_name(self.path.name + ".state.json")
        self.events: list[dict[str, Any]] = []
        self.version = 1
        self.rules: dict[str, str] = {"missing_evidence": "guess"}
        self.snapshots: dict[int, dict[str, str]] = {1: dict(self.rules)}

        # Existing audit logs are append-only: validate and load the chain before
        # recording anything new. Never truncate an existing history.
        if (self.path.exists() and self.path.stat().st_size) or self.state_path.exists():
            if self.path.exists() and self.path.stat().st_size:
                self.events = self._load_audit_events()
            self._restore_state()
            self._record("SESSION_STARTED", {"version": self.version, "rules": dict(self.rules),
                                               "resumed": True})
        else:
            # Preserve the original fresh-path behavior and event vocabulary.
            self._record("SESSION_STARTED", {"version": self.version, "rules": self.rules})
            self._persist_state()

    def _load_audit_events(self) -> list[dict[str, Any]]:
        loaded: list[dict[str, Any]] = []
        previous = "GENESIS"
        for expected_seq, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            event = json.loads(line)
            claimed = event.get("hash")
            body = dict(event)
            body.pop("hash", None)
            if event.get("sequence") != expected_seq or event.get("previous_hash") != previous or claimed != digest(body):
                raise ValueError(f"cannot resume: invalid audit chain at line {expected_seq}")
            loaded.append(event)
            previous = claimed
        return loaded

    def _restore_state(self) -> None:
        # The sidecar is the primary durable state. If absent (e.g. copied audit
        # file), reconstruct the latest known rules/version from audit events.
        if self.state_path.exists():
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            rules, version = state.get("rules"), state.get("version")
            if not isinstance(rules, dict) or not isinstance(version, int) or version < 1:
                raise ValueError("cannot resume: malformed durable state")
            self.rules = {str(k): str(v) for k, v in rules.items()}
            self.version = version
        else:
            for event in self.events:
                payload = event.get("payload", {})
                if event.get("stage") == "APPLY_AUTHORIZED_CHANGE":
                    after = payload.get("after", {})
                    if isinstance(after.get("version"), int) and isinstance(after.get("rules"), dict):
                        self.version = after["version"]
                        self.rules = dict(after["rules"])
                elif event.get("stage") == "ROLLBACK_APPLIED":
                    if isinstance(payload.get("to_version"), int) and isinstance(payload.get("after"), dict):
                        self.version = payload["to_version"]
                        self.rules = dict(payload["after"])
        # Rebuild available rollback snapshots from the chronological state events.
        self.snapshots = {1: {"missing_evidence": "guess"}}
        for event in self.events:
            payload = event.get("payload", {})
            if event.get("stage") == "APPLY_AUTHORIZED_CHANGE":
                after = payload.get("after", {})
                if isinstance(after.get("version"), int) and isinstance(after.get("rules"), dict):
                    self.snapshots[after["version"]] = dict(after["rules"])
            elif event.get("stage") == "ROLLBACK_APPLIED":
                if isinstance(payload.get("to_version"), int) and isinstance(payload.get("after"), dict):
                    self.snapshots[payload["to_version"]] = dict(payload["after"])
        self.snapshots[self.version] = dict(self.rules)

    def _persist_state(self) -> None:
        state = {"version": self.version, "rules": self.rules}
        temp = self.state_path.with_name(self.state_path.name + ".tmp")
        temp.write_text(canonical(state) + "\n", encoding="utf-8")
        temp.replace(self.state_path)

    def _record(self, stage: str, payload: dict[str, Any]) -> dict[str, Any]:
        previous = self.events[-1]["hash"] if self.events else "GENESIS"
        event = {"sequence": len(self.events) + 1, "stage": stage,
                 "payload": payload, "previous_hash": previous}
        event["hash"] = digest(event)
        self.events.append(event)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(canonical(event) + "\n")
        return event

    def act(self, evidence_missing: bool, evidence: str = "test evidence") -> str:
        if evidence_missing:
            action = self.rules["missing_evidence"]
        else:
            action = "answer_from_evidence"
        self._record("OBSERVE", {"version": self.version, "input": {"evidence_missing": evidence_missing,
                      "evidence": evidence}, "actual_action": action})
        return action

    def identify(self, expected: str, actual: str, evidence: str) -> bool:
        contradiction = expected != actual
        self._record("IDENTIFY", {"contradiction": contradiction, "expected": expected,
                      "actual": actual, "evidence": evidence,
                      "alternatives": ["reasoning/model rule error", "missing information", "operational or authority constraint"]})
        return contradiction

    def accept_correction(self, contribution: str, contributor: str, evidence: str,
                          assessment: str = "supported in this controlled test") -> None:
        self._record("ACCEPT_CORRECTION", {"contribution": contribution, "provenance": {"contributor": contributor},
                      "evidence": evidence, "assessment": assessment,
                      "scope_note": "Acceptance records the assessment; it does not itself change behavior."})

    def acknowledge(self, correction: str) -> None:
        self._record("ACKNOWLEDGMENT_ONLY", {"correction": correction, "version": self.version,
                      "behavior_changed": False})

    def propose(self) -> dict[str, Any]:
        proposal = {"rule": "missing_evidence", "old": self.rules["missing_evidence"],
                    "new": "report_unknown", "target_version": self.version + 1,
                    "expected_behavior": "report_unknown when evidence is missing",
                    "preserve_answerable_cases": True}
        self._record("REVISE_MODEL", {"from_version": self.version, "candidate_rule": proposal["new"],
                      "rationale": "Missing evidence must not be silently converted into a guess."})
        self._record("PROPOSE_CHANGE", proposal)
        return proposal

    def apply(self, proposal: dict[str, Any], approved_by: str | None = None) -> bool:
        valid = (proposal.get("rule") == "missing_evidence"
                 and proposal.get("target_version") == self.version + 1
                 and proposal.get("old") == self.rules["missing_evidence"]
                 and proposal.get("new") == "report_unknown")
        authorized = bool(approved_by and approved_by.strip()) and valid
        self._record("REVIEW_AUTHORITY", {"authorized": authorized, "reviewer": approved_by,
                      "reason": "explicit named approval and current proposal" if authorized else
                      ("missing explicit named approval" if not approved_by else "stale or mismatched proposal"),
                      "next_step_authority": "named human reviewer"})
        if not authorized:
            return False
        before = {"version": self.version, "rules": dict(self.rules)}
        self.rules[proposal["rule"]] = proposal["new"]
        self.version += 1
        self.snapshots[self.version] = dict(self.rules)
        self._record("APPLY_AUTHORIZED_CHANGE", {"before": before, "after": {"version": self.version,
                      "rules": dict(self.rules)}, "approved_by": approved_by})
        self._persist_state()
        return True

    def verify(self) -> bool:
        missing_action = self.act(True, "held-out case: no supporting evidence")
        answerable_action = self.act(False, "held-out case: supporting evidence available")
        passed = missing_action == "report_unknown" and answerable_action == "answer_from_evidence"
        self._record("VERIFY", {"tests": [
            {"input": "missing evidence", "expected": "report_unknown", "actual": missing_action,
             "passed": missing_action == "report_unknown"},
            {"input": "evidence available", "expected": "answer_from_evidence", "actual": answerable_action,
             "passed": answerable_action == "answer_from_evidence"}], "passed": passed})
        self._record("RETAIN" if passed else "ROLLBACK", {"version": self.version, "verified": passed,
                      "reason": "behavioral regression tests" if passed else "verification failed"})
        if not passed:
            self.rollback()
        return passed

    def rollback(self) -> None:
        previous_version = self.version - 1
        if previous_version in self.snapshots:
            before = dict(self.rules)
            self.rules = dict(self.snapshots[previous_version])
            old_version = self.version
            self.version = previous_version
            self._record("ROLLBACK_APPLIED", {"from_version": old_version, "to_version": self.version,
                          "before": before, "after": dict(self.rules)})
            self._persist_state()


def verify_audit(path: str | Path) -> tuple[bool, str]:
    previous = "GENESIS"
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        for expected_seq, line in enumerate(lines, 1):
            event = json.loads(line)
            if event.get("sequence") != expected_seq:
                return False, f"sequence mismatch at line {expected_seq}"
            if event.get("previous_hash") != previous:
                return False, f"previous_hash mismatch at line {expected_seq}"
            claimed = event.pop("hash", None)
            if claimed != digest(event):
                return False, f"event hash mismatch at line {expected_seq}"
            previous = claimed
        return True, f"verified {len(lines)} events"
    except (OSError, ValueError, TypeError) as exc:
        return False, f"audit unreadable: {exc}"


def demo(audit_path: str | Path = "audit.jsonl") -> list[str]:
    r = RRE(audit_path)
    output = []
    baseline = r.act(True)
    output.append(f"Baseline action with missing evidence: {baseline}")
    r.identify("report_unknown", baseline, "controlled input explicitly has no supporting evidence")
    r.accept_correction("When evidence is missing, report uncertainty instead of guessing.",
                         "independent-test-contributor", "baseline action was 'guess' on missing-evidence input")
    r.acknowledge("I understand; I will report uncertainty.")
    r.acknowledge("Correction accepted; I will do better.")
    after_ack = r.act(True)
    output.append(f"After two acknowledgments, action remains: {after_ack}")
    detected = r.identify("report_unknown", after_ack, "behavioral probe after acknowledgments")
    r._record("CLOSED_LOOP_DETECTED", {"detected": detected and after_ack == baseline,
                "reason": "acknowledgment occurred without behavioral change"})
    proposal = r.propose()
    denied = r.apply(proposal)
    output.append(f"Unauthorised apply blocked: {not denied}; current rule: {r.rules['missing_evidence']}")
    applied = r.apply(proposal, approved_by="independent-test-reviewer")
    verified = r.verify() if applied else False
    output.append(f"Authorized local rule change applied: {applied}; version: {r.version}")
    output.append(f"Held-out behavioral verification: {'PASS' if verified else 'FAIL'}")
    chain_ok, chain_message = verify_audit(audit_path)
    output.append(f"Audit hash-chain integrity: {'PASS' if chain_ok else 'FAIL'} ({chain_message})")
    return output

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", default="audit.jsonl", help="JSONL audit path")
    args = parser.parse_args()
    for line in demo(args.audit):
        print(line)
    print(f"Audit file: {Path(args.audit).resolve()}")
