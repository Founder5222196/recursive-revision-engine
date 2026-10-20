"""RRE persistence/adversarial rollback add-on; leaves rre_minimal.py untouched."""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from typing import Any


def canonical(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def digest(x: Any) -> str:
    return hashlib.sha256(canonical(x).encode()).hexdigest()

def verify_chain(path: str | Path) -> tuple[bool, str]:
    prev, count = "GENESIS", 0
    try:
        for count, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
            event = json.loads(line)
            claimed = event.pop("hash", None)
            if event.get("sequence") != count: return False, f"sequence mismatch at line {count}"
            if event.get("previous_hash") != prev: return False, f"previous_hash mismatch at line {count}"
            if claimed != digest(event): return False, f"event hash mismatch at line {count}"
            prev = claimed
        return True, f"verified {count} events"
    except (OSError, ValueError, TypeError) as e:
        return False, f"audit unreadable: {e}"

class PersistentRRE:
    """Append-only audit + atomic state snapshot. Candidate revisions are staged, never live."""
    def __init__(self, state_path: str | Path, audit_path: str | Path):
        self.state_path, self.audit_path = Path(state_path), Path(audit_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        if self.state_path.exists():
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.version, self.rules, self.version_id = state["version"], state["rules"], state["version_id"]
            ok, msg = verify_chain(self.audit_path)
            if not ok: raise ValueError(f"refusing corrupt audit: {msg}")
            self._record("RESTART_RESTORED", {"version":self.version,"version_id":self.version_id,"rules":self.rules})
        else:
            self.version, self.rules = 1, {"missing_evidence":"guess"}
            self.version_id = self._version_id(self.version, self.rules)
            self._save()
            self._record("INITIALIZED", {"version":self.version,"version_id":self.version_id,"rules":self.rules})

    @staticmethod
    def _version_id(version, rules): return f"v{version}-" + digest({"version":version,"rules":rules})[:16]
    def _save(self):
        payload = {"version":self.version,"rules":self.rules,"version_id":self.version_id}
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(canonical(payload)+"\n", encoding="utf-8")
        os.replace(tmp, self.state_path)
    def _record(self, stage, payload):
        ok, _ = verify_chain(self.audit_path) if self.audit_path.exists() and self.audit_path.stat().st_size else (True, "empty")
        if not ok: raise ValueError("audit chain invalid before append")
        previous, seq = "GENESIS", 0
        if self.audit_path.exists():
            for line in self.audit_path.read_text(encoding="utf-8").splitlines():
                e=json.loads(line); previous=e["hash"]; seq=e["sequence"]
        event={"sequence":seq+1,"stage":stage,"payload":payload,"previous_hash":previous}
        event["hash"]=digest(event)
        with self.audit_path.open("a",encoding="utf-8") as f: f.write(canonical(event)+"\n")
        return event
    def act(self, evidence_missing: bool):
        action = self.rules["missing_evidence"] if evidence_missing else "answer_from_evidence"
        self._record("OBSERVE", {"version":self.version,"version_id":self.version_id,"evidence_missing":evidence_missing,"actual_action":action})
        return action
    def snapshot(self): return {"version":self.version,"version_id":self.version_id,"rules":dict(self.rules)}
    def commit_candidate(self, candidate_rules: dict[str,str], label: str, acknowledged=False, accepted=False):
        before=self.snapshot(); candidate={"rules":dict(candidate_rules),"label":label,"acknowledged":acknowledged,"accepted":accepted}
        # Deliberately activate the candidate in memory for verification, but do not
        # persist it before it passes. This exercises an actual working-state rollback.
        self.rules=dict(candidate_rules)
        missing=[self.act(True) for _ in range(4)]
        answerable=[self.act(False) for _ in range(4)]
        passed=all(x=="report_unknown" for x in missing) and all(x=="answer_from_evidence" for x in answerable)
        self._record("CANDIDATE_VERIFIED", {"base_version_id":before["version_id"],"candidate":candidate,"missing_actions":missing,"answerable_actions":answerable,"passed":passed})
        if passed:
            self.version += 1; self.version_id=self._version_id(self.version,self.rules); self._save()
            self._record("CANDIDATE_RETAINED", {"before":before,"after":self.snapshot()})
        else:
            failed_snapshot={"version":self.version,"version_id":self.version_id,"rules":dict(self.rules)}
            self.version=before["version"]; self.version_id=before["version_id"]; self.rules=dict(before["rules"])
            self._save()
            self._record("ROLLBACK_APPLIED", {"failed_candidate":candidate,"failed_working_state":failed_snapshot,"restored":self.snapshot(),"reason":"held-out behavioral verification failed; labels cannot override evidence"})
        return passed
    @staticmethod
    def _act_pure(rules, missing): return rules["missing_evidence"] if missing else "answer_from_evidence"

def evaluate(agent: PersistentRRE):
    cases=[]
    for i in range(4):
        got=agent.act(True); cases.append({"case":f"missing_{i+1}","expected":"report_unknown","actual":got,"passed":got=="report_unknown"})
    for i in range(4):
        got=agent.act(False); cases.append({"case":f"answerable_{i+1}","expected":"answer_from_evidence","actual":got,"passed":got=="answer_from_evidence"})
    return {"passed":sum(c["passed"] for c in cases),"total":len(cases),"cases":cases}
