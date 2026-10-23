"""Grounded Evidence Judge v2 development build. Python 3.10+, stdlib only.

The semantic extractor is injected; no model/provider is bundled or implied. All
accept/reject, span, conflict, version, authorization, and response checks here
are deterministic. This is development material, not a claim-v2 evaluation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Protocol
import json, re, hashlib

SCHEMA_VERSION = "evidence-record/1.0"
POLICY_VERSION = "sufficiency/1.0"
ASSERTION_TYPES = {"asserted", "negated", "hypothetical", "estimated", "historical", "conditional", "unknown"}

class ExtractionModel(Protocol):
    def __call__(self, question: str, dossier: str) -> dict[str, Any]: ...

@dataclass(frozen=True)
class CandidateAssertion:
    source_span: str
    entity: str
    attribute: str
    value: str
    scope: dict[str, Any]
    assertion_type: str
    relation: str
    source_start: int | None = None
    source_end: int | None = None

@dataclass(frozen=True)
class EvidenceRecord:
    schema_version: str
    question: str
    dossier_sha256: str
    candidates: tuple[CandidateAssertion, ...]

@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]
    record: EvidenceRecord | None

@dataclass(frozen=True)
class Decision:
    status: str                    # ANSWER or ABSTAIN
    answer: str | None
    reason: str
    policy_version: str
    evidence_indices: tuple[int, ...] = ()

@dataclass(frozen=True)
class Policy:
    version: str = POLICY_VERSION
    # No source-authority ranking and no implicit conflict-resolution strategy.
    require_asserted: bool = True
    abstain_on_unresolved_conflict: bool = True
    allow_compatible_multi_evidence: bool = True


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _nonempty_string(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def validate_evidence_record(raw: dict[str, Any], question: str, dossier: str) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ValidationResult(False, ("record must be an object",), None)
    if raw.get("schema_version") != SCHEMA_VERSION: errors.append("unsupported schema_version")
    if raw.get("question") != question: errors.append("question binding mismatch")
    if raw.get("dossier_sha256") != sha256(dossier): errors.append("dossier hash mismatch")
    candidates = raw.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates must be a list"); candidates = []
    parsed: list[CandidateAssertion] = []
    required = ("source_span", "entity", "attribute", "value", "scope", "assertion_type", "relation")
    for i, c in enumerate(candidates):
        if not isinstance(c, dict): errors.append(f"candidate[{i}] must be an object"); continue
        for k in required:
            if k not in c: errors.append(f"candidate[{i}] missing {k}")
        if not _nonempty_string(c.get("source_span")): errors.append(f"candidate[{i}] source_span must be nonempty text")
        elif c["source_span"] not in dossier: errors.append(f"candidate[{i}] source_span is not an exact dossier substring")
        for k in ("entity", "attribute", "value", "relation"):
            if not _nonempty_string(c.get(k)): errors.append(f"candidate[{i}] {k} must be nonempty text")
        if not isinstance(c.get("scope"), dict): errors.append(f"candidate[{i}] scope must be an object")
        if c.get("assertion_type") not in ASSERTION_TYPES: errors.append(f"candidate[{i}] invalid assertion_type")
        start, end = c.get("source_start"), c.get("source_end")
        if start is not None or end is not None:
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start or end > len(dossier):
                errors.append(f"candidate[{i}] invalid source offsets")
            elif dossier[start:end] != c.get("source_span"):
                errors.append(f"candidate[{i}] offsets do not match source_span")
        if all(_nonempty_string(c.get(k)) for k in ("source_span", "entity", "attribute", "value", "relation")) and isinstance(c.get("scope"), dict) and c.get("assertion_type") in ASSERTION_TYPES:
            parsed.append(CandidateAssertion(c["source_span"], c["entity"], c["attribute"], c["value"], c["scope"], c["assertion_type"], c["relation"], start, end))
    rec = EvidenceRecord(SCHEMA_VERSION, question, sha256(dossier), tuple(parsed)) if not errors else None
    return ValidationResult(not errors, tuple(errors), rec)


def make_record(question: str, dossier: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Convenience for adapters; deliberately does not validate or repair candidates."""
    return {"schema_version": SCHEMA_VERSION, "question": question, "dossier_sha256": sha256(dossier), "candidates": candidates}


def _norm(s: str) -> str:
    # Only formatting normalization: casefold + collapse whitespace. Do not strip
    # units, qualifiers, negation, dates, or punctuation inside values.
    return re.sub(r"\s+", " ", s.strip()).casefold()


def _same_fact(a: CandidateAssertion, b: CandidateAssertion) -> bool:
    return (_norm(a.entity) == _norm(b.entity) and _norm(a.attribute) == _norm(b.attribute)
            and _norm(str(a.scope)) == _norm(str(b.scope))
            and a.assertion_type == b.assertion_type)

class SufficiencyPolicy:
    def __init__(self, policy: Policy | None = None): self.policy = policy or Policy()

    def decide(self, record: EvidenceRecord, target_entity: str | None = None,
               target_attribute: str | None = None) -> Decision:
        eligible = []
        for i, a in enumerate(record.candidates):
            if self.policy.require_asserted and a.assertion_type != "asserted": continue
            if target_entity and _norm(a.entity) != _norm(target_entity): continue
            if target_attribute and _norm(a.attribute) != _norm(target_attribute): continue
            eligible.append((i, a))
        if not eligible:
            return Decision("ABSTAIN", None, "no attributable asserted evidence for the requested fact", self.policy.version)
        # Preserve multiple candidates. Any same-fact incompatible values cause abstention;
        # there is no first-match or source-authority preference.
        for x in range(len(eligible)):
            for y in range(x + 1, len(eligible)):
                ia, a = eligible[x]; ib, b = eligible[y]
                if _same_fact(a, b) and _norm(a.value) != _norm(b.value):
                    return Decision("ABSTAIN", None, f"unresolved contradictory evidence in candidates {ia} and {ib}", self.policy.version, (ia, ib))
        values: dict[str, list[int]] = {}
        for i, a in eligible: values.setdefault(_norm(a.value), []).append(i)
        if len(values) > 1:
            # Different entity/attribute/scope records may be irrelevant neighbors;
            # absent a question-conditioned semantic target, do not choose arbitrarily.
            return Decision("ABSTAIN", None, "multiple non-equivalent candidate values; attribution/scope needs model adjudication", self.policy.version, tuple(i for i, _ in eligible))
        indices = tuple(i for i, _ in eligible)
        return Decision("ANSWER", eligible[0][1].value, "supported by validated, attributable evidence", self.policy.version, indices)

class GroundedEvidenceJudge:
    def __init__(self, model: ExtractionModel, policy: Policy | None = None):
        self.model = model
        self.policy = SufficiencyPolicy(policy)

    def judge(self, question: str, dossier: str, *, target_entity: str | None = None,
              target_attribute: str | None = None) -> tuple[str, dict[str, Any]]:
        raw = self.model(question, dossier)
        validation = validate_evidence_record(raw, question, dossier)
        if not validation.valid or validation.record is None:
            decision = Decision("ABSTAIN", None, "evidence record rejected: " + "; ".join(validation.errors), self.policy.policy.version)
        else:
            decision = self.policy.decide(validation.record, target_entity, target_attribute)
        response = format_response(decision)
        return response, {"validation": {"valid": validation.valid, "errors": list(validation.errors)},
                          "decision": asdict(decision), "record": raw}

_RESPONSE = re.compile(r"\A(?:ANSWER: (\S(?:.*\S)?)|ABSTAIN: (\S(?:.*\S)?))\Z")
def validate_response(text: str) -> bool:
    return isinstance(text, str) and _RESPONSE.fullmatch(text) is not None

def format_response(decision: Decision) -> str:
    if decision.status == "ANSWER" and _nonempty_string(decision.answer):
        out = "ANSWER: " + decision.answer.strip()
    elif decision.status == "ABSTAIN" and _nonempty_string(decision.reason):
        out = "ABSTAIN: " + decision.reason.strip()
    else:
        raise ValueError("invalid internal decision; response gate refuses malformed state")
    if not validate_response(out): raise ValueError("response gate generated malformed output")
    return out

def gate_model_response(text: str) -> str:
    """Accept only exact contract; malformed text is rejected, not repaired."""
    if not validate_response(text): raise ValueError("malformed model response: expected exactly ANSWER: ... or ABSTAIN: ...")
    return text

class VersionedPolicyExtension:
    """Small explicit extension alongside canonical RRE; never mutates on init.

    Uses the canonical engine's append-only hash-chain recorder and state sidecar.
    A separate sidecar stores policy/config; apply requires proposal + named approval.
    """
    def __init__(self, engine: Any, policy_path: str | Path, initial_policy: dict[str, Any] | None = None):
        self.engine = engine; self.policy_path = Path(policy_path)
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)
        if self.policy_path.exists():
            self.state = json.loads(self.policy_path.read_text(encoding="utf-8"))
            if not isinstance(self.state.get("version"), int) or not isinstance(self.state.get("policy"), dict): raise ValueError("invalid policy state")
        else:
            self.state = {"version": 1, "policy": initial_policy or asdict(Policy()), "model_config": {"provider": "injected", "model_id": "unconfigured"}}
            # Explicit creation event only; no engine behavior/rule is changed.
            self._persist()
            self.engine._record("JUDGE_POLICY_INITIALIZED", {"version": 1, "policy_hash": sha256(json.dumps(self.state, sort_keys=True))})

    def _persist(self) -> None:
        tmp = self.policy_path.with_name(self.policy_path.name + ".tmp")
        tmp.write_text(json.dumps(self.state, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"); tmp.replace(self.policy_path)

    def propose(self, new_policy: dict[str, Any], rationale: str, provenance: str, model_config: dict[str, Any] | None = None) -> dict[str, Any]:
        p = {"base_version": self.state["version"], "target_version": self.state["version"] + 1,
             "old_policy": self.state["policy"], "new_policy": new_policy, "rationale": rationale,
             "provenance": provenance, "model_config": model_config or self.state.get("model_config", {})}
        p["proposal_sha256"] = sha256(json.dumps(p, sort_keys=True, separators=(",", ":")))
        self.engine._record("JUDGE_POLICY_PROPOSED", p)
        return p

    def apply(self, proposal: dict[str, Any], approved_by: str | None = None) -> bool:
        valid = (proposal.get("base_version") == self.state["version"] and proposal.get("target_version") == self.state["version"] + 1
                 and proposal.get("old_policy") == self.state["policy"] and isinstance(proposal.get("new_policy"), dict))
        authorized = bool(isinstance(approved_by, str) and approved_by.strip() and valid)
        self.engine._record("JUDGE_POLICY_AUTHORIZATION", {"authorized": authorized, "approved_by": approved_by,
            "proposal_sha256": proposal.get("proposal_sha256"), "base_version": self.state["version"],
            "reason": "named approval of current proposal" if authorized else "missing named approval or stale/mismatched proposal"})
        if not authorized: return False
        before = dict(self.state)
        self.state = {"version": proposal["target_version"], "policy": proposal["new_policy"], "model_config": proposal.get("model_config", {})}
        self._persist()
        self.engine._record("JUDGE_POLICY_APPLIED", {"before": before, "after": self.state, "approved_by": approved_by,
            "proposal_sha256": proposal["proposal_sha256"]})
        return True

    def rollback(self, previous_state: dict[str, Any], approved_by: str) -> bool:
        if not approved_by or not approved_by.strip(): return False
        current = dict(self.state); self.state = dict(previous_state); self._persist()
        self.engine._record("JUDGE_POLICY_ROLLBACK", {"before": current, "after": self.state, "approved_by": approved_by})
        return True
