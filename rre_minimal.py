import json
import hashlib
from pathlib import Path

def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()

class RRE:
    def __init__(self, audit_path="audit.jsonl"):
        self.path = Path(audit_path)
        self.path.write_text("")
        self.events = []
        self.version = 1
        self.rules = {"missing_evidence": "guess"}

    def record(self, stage, payload):
        previous = self.events[-1]["hash"] if self.events else "GENESIS"
        event = {
            "sequence": len(self.events) + 1,
            "stage": stage,
            "payload": payload,
            "previous_hash": previous,
        }
        event["hash"] = digest(event)
        self.events.append(event)
        with self.path.open("a") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")

    def act(self, evidence_missing):
        action = (
            self.rules["missing_evidence"]
            if evidence_missing else "answer_from_evidence"
        )
        self.record("OBSERVE", {
            "version": self.version,
            "evidence_missing": evidence_missing,
            "actual_action": action,
        })
        return action

    def acknowledge(self, correction):
        self.record("ACKNOWLEDGMENT_ONLY", {
            "correction": correction,
            "version": self.version,
        })

    def propose(self):
        proposal = {
            "rule": "missing_evidence",
            "old": self.rules["missing_evidence"],
            "new": "report_unknown",
            "target_version": self.version + 1,
        }
        self.record("PROPOSE_CHANGE", proposal)
        return proposal

    def apply(self, proposal, approved_by=None):
        if not approved_by:
            self.record("REVIEW_AUTHORITY", {
                "authorized": False,
                "reason": "No explicit named approval",
            })
            return False

        if (proposal["target_version"] != self.version + 1
                or proposal["old"] != self.rules["missing_evidence"]):
            self.record("REVIEW_AUTHORITY", {
                "authorized": False,
                "reason": "Stale or mismatched proposal",
            })
            return False

        before = dict(self.rules)
        self.record("REVIEW_AUTHORITY", {
            "authorized": True,
            "approved_by": approved_by,
            "proposal": proposal,
        })
        self.rules[proposal["rule"]] = proposal["new"]
        self.version += 1
        self.record("APPLY_AUTHORIZED_CHANGE", {
            "before": before,
            "after": dict(self.rules),
            "version": self.version,
        })
        return True

    def verify(self):
        actual = self.act(evidence_missing=True)
        passed = actual == "report_unknown"
        self.record("VERIFY", {
            "expected": "report_unknown",
            "actual": actual,
            "passed": passed,
        })
        self.record(
            "RETAIN" if passed else "ROLLBACK_REQUIRED",
            {"version": self.version, "verified": passed},
        )
        return passed

if __name__ == "__main__":
    rre = RRE()

    # Establish the failure.
    assert rre.act(True) == "guess"

    # Repeated acknowledgments must not count as revision.
    rre.acknowledge("I should report uncertainty.")
    rre.acknowledge("I understand and will do that.")
    assert rre.act(True) == "guess"

    # An independent behavioral test detects the unchanged behavior.
    rre.record("CLOSED_LOOP_DETECTED", {
        "detected": True,
        "reason": "Acknowledgments occurred without behavioral change",
    })

    # Propose a narrow, testable revision.
    proposal = rre.propose()

    # Authority boundary: no approval, no change.
    assert not rre.apply(proposal)
    assert rre.act(True) == "guess"

    # Explicit test authorization permits the local model change.
    assert rre.apply(proposal, approved_by="test-reviewer")
    assert rre.verify()

    print("PASS: acknowledgment failure detected")
    print("PASS: unauthorized change blocked")
    print("PASS: authorized behavioral revision verified")
    print("Audit:", rre.path.resolve())
