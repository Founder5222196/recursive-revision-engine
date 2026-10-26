"""RRE Economic Governance Kernel v0.2 release candidate; Python 3.10+, stdlib only.

This module EXTENDS contribution_bridge.py without modifying it. The prototype remains
responsible for contribution verification, value-pool registration, legacy policy
approval, and hypothetical arithmetic. This layer adds attribution, versioned
governance, claims, disputes, obligations, replay, and external checkpoint checking.

Governance records are experimental records. They do not create legal rights, execute
payments, or establish economic causation by themselves.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json
import threading
from functools import wraps

from contribution_bridge import AllocationPolicy, ContributionBridge, canonical, sha


PROPOSED = "PROPOSED"
APPROVED = "APPROVED"
DISPUTED = "DISPUTED"
PAYABLE = "PAYABLE"
PAID = "PAID"
REVERSED = "REVERSED"


@dataclass(frozen=True)
class AttributionRecord:
    attribution_id: str
    contribution_ids: tuple[str, ...]
    pool_id: str
    system_id: str
    period: str
    method_version: str
    evidence_refs: tuple[str, ...]
    evidence_sources: tuple[tuple[str, str], ...]
    reviewer: str
    status: str
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class GovernanceDecision:
    decision_id: str
    subject_id: str
    decision_type: str
    policy_version: int | None
    eligible_participants: tuple[str, ...]
    approval_evidence: str
    conflicts: tuple[str, ...]
    reasoning: str
    effective_at: str
    decided_by: str


@dataclass(frozen=True)
class Claim:
    claim_id: str
    claimant_id: str
    attribution_id: str
    policy_id: str
    policy_version: int
    amount_minor: int
    currency: str
    status: str
    decision_id: str = ""


@dataclass(frozen=True)
class Dispute:
    dispute_id: str
    claim_id: str
    grounds: str
    submitted_at: str
    reviewer: str
    evidence_refs: tuple[str, ...]
    decision: str
    remedy: str
    appeal_status: str


@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    claim_id: str
    debtor: str
    creditor: str
    amount_due_minor: int
    amount_paid_minor: int
    due_date: str
    payment_evidence: tuple[str, ...]
    status: str


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"malformed record: missing {name}")
    return value


def _str_tuple(value: Any, name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"malformed record: {name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"malformed record: {name} must not be empty")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"malformed record: {name} entries must be nonempty strings")
    return value


def _currency(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 3 or not value.isalpha():
        raise ValueError("malformed record: currency must be a 3-letter code")
    return value.upper()


def _rejection_subject(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    if args:
        first = args[0]
        for attr in ("attribution_id", "policy_id", "claim_id", "dispute_id", "obligation_id"):
            if hasattr(first, attr):
                return str(getattr(first, attr))
        if isinstance(first, str):
            return first
    for key in ("attribution_id", "policy_id", "claim_id", "dispute_id", "obligation_id", "pool_id"):
        if key in kwargs and kwargs[key] is not None:
            return str(kwargs[key])
    return "UNKNOWN"


def audit_rejections(action: str):
    """Ensure rejected governance actions remain visible in the append-only ledger."""
    def decorate(fn):
        @wraps(fn)
        def wrapped(self, *args, **kwargs):
            try:
                return fn(self, *args, **kwargs)
            except ValueError as exc:
                self._record(
                    "GOVERNANCE_ACTION_REJECTED",
                    {
                        "action": action,
                        "subject_id": _rejection_subject(args, kwargs),
                        "reason": str(exc),
                    },
                )
                raise
        return wrapped
    return decorate


class EconomicGovernanceKernel(ContributionBridge):
    """Governed extension of ContributionBridge with append-only replayed state.

    The inherited ContributionBridge remains unchanged on disk and in meaning.
    Operations invoked through this class use the stricter v0.2 allocation gate.
    """

    def __init__(self, audit_path: str | Path, checkpoint_path: str | Path | None = None):
        self._governance_lock = threading.RLock()
        self.attributions: dict[str, dict[str, Any]] = {}
        self.attribution_states: dict[str, str] = {}
        self.attribution_decisions: dict[str, str] = {}
        self.decisions: dict[str, dict[str, Any]] = {}
        self.policy_versions: dict[tuple[str, int], dict[str, Any]] = {}
        self.claims: dict[str, dict[str, Any]] = {}
        self.claim_states: dict[str, str] = {}
        self.claim_decisions: dict[str, str] = {}
        self.disputes: dict[str, dict[str, Any]] = {}
        self.dispute_resolutions: dict[str, dict[str, Any]] = {}
        self.obligations: dict[str, dict[str, Any]] = {}
        self.obligation_states: dict[str, str] = {}
        self.obligation_paid_minor: dict[str, int] = {}
        self.obligation_payment_evidence: dict[str, list[str]] = {}
        self.allocations: dict[str, dict[str, Any]] = {}
        super().__init__(audit_path)
        if checkpoint_path is not None:
            self.verify_checkpoint(checkpoint_path)

    # ---------- replay ----------

    def _replay(self, typ: str, p: dict[str, Any]):
        super()._replay(typ, p)

        if typ == "ALLOCATION_POLICY_APPROVED":
            policy = p["policy"]
            key = (policy["policy_id"], policy["version"])
            self.policy_versions[key] = {
                "policy": policy,
                "decision_id": None,
                "source": "prototype",
                "policy_sha256": p.get("policy_sha256", sha(policy)),
            }
        elif typ == "ATTRIBUTION_PROPOSED":
            record = p["record"]
            aid = record["attribution_id"]
            self.attributions[aid] = record
            self.attribution_states[aid] = PROPOSED
        elif typ == "ATTRIBUTION_APPROVED":
            aid = p["attribution_id"]
            self._replay_decision(p["decision"])
            self.attribution_states[aid] = APPROVED
            self.attribution_decisions[aid] = p["decision"]["decision_id"]
        elif typ == "ATTRIBUTION_REVERSED":
            aid = p["attribution_id"]
            self._replay_decision(p["decision"])
            self.attribution_states[aid] = REVERSED
            self.attribution_decisions[aid] = p["decision"]["decision_id"]
        elif typ == "GOVERNANCE_POLICY_VERSION_APPROVED":
            policy = p["policy"]
            self._replay_decision(p["decision"])
            self.policy_versions[(policy["policy_id"], policy["version"])] = {
                "policy": policy,
                "decision_id": p["decision"]["decision_id"],
                "source": "governance",
                "policy_sha256": p["policy_sha256"],
            }
        elif typ == "CLAIM_PROPOSED":
            claim = p["claim"]
            cid = claim["claim_id"]
            self.claims[cid] = claim
            self.claim_states[cid] = PROPOSED
        elif typ == "CLAIM_APPROVED":
            cid = p["claim_id"]
            self._replay_decision(p["decision"])
            self.claim_states[cid] = APPROVED
            self.claim_decisions[cid] = p["decision"]["decision_id"]
        elif typ == "DISPUTE_OPENED":
            dispute = p["dispute"]
            self.disputes[dispute["dispute_id"]] = {
                **dispute,
                "prior_claim_state": p["prior_claim_state"],
            }
            self.claim_states[dispute["claim_id"]] = DISPUTED
            for oid, obligation in self.obligations.items():
                if obligation["claim_id"] == dispute["claim_id"] and self.obligation_states.get(oid) == PAYABLE:
                    self.obligation_states[oid] = DISPUTED
        elif typ == "DISPUTE_RESOLVED":
            did = p["dispute_id"]
            self._replay_decision(p["decision"])
            self.dispute_resolutions[did] = p
            claim_id = self.disputes[did]["claim_id"]
            if p["outcome"] == "OVERTURN":
                self.claim_states[claim_id] = REVERSED
                for oid, obligation in self.obligations.items():
                    if obligation["claim_id"] == claim_id and self.obligation_states.get(oid) != PAID:
                        self.obligation_states[oid] = REVERSED
            else:
                prior = self.disputes[did]["prior_claim_state"]
                self.claim_states[claim_id] = prior
                for oid, obligation in self.obligations.items():
                    if obligation["claim_id"] == claim_id and self.obligation_states.get(oid) == DISPUTED:
                        self.obligation_states[oid] = PAYABLE
        elif typ == "OBLIGATION_CREATED":
            obligation = p["obligation"]
            oid = obligation["obligation_id"]
            self.obligations[oid] = obligation
            self.obligation_states[oid] = PAYABLE
            self.obligation_paid_minor[oid] = obligation["amount_paid_minor"]
            self.obligation_payment_evidence[oid] = list(obligation["payment_evidence"])
            self.claim_states[obligation["claim_id"]] = PAYABLE
        elif typ == "PAYMENT_RECORDED":
            oid = p["obligation_id"]
            self.obligation_paid_minor[oid] = p["new_amount_paid_minor"]
            self.obligation_payment_evidence.setdefault(oid, []).append(p["evidence_ref"])
            self.obligation_states[oid] = p["new_status"]
            claim_id = self.obligations[oid]["claim_id"]
            self.claim_states[claim_id] = p["new_status"]
        elif typ == "PAYMENT_REPORTED_UNVERIFIED":
            pass
        elif typ == "OBLIGATION_REVERSED":
            oid = p["obligation_id"]
            self._replay_decision(p["decision"])
            self.obligation_states[oid] = REVERSED
            self.claim_states[self.obligations[oid]["claim_id"]] = REVERSED
        elif typ == "GOVERNED_ALLOCATION_CALCULATED":
            self.allocations[p["allocation_id"]] = p

    def _replay_decision(self, decision: dict[str, Any]):
        self.decisions[decision["decision_id"]] = decision

    # ---------- shared validation ----------

    def _ensure_new_id(self, registry: dict[str, Any], record_id: str, label: str):
        _nonempty(record_id, label)
        if record_id in registry:
            raise ValueError(f"{label} already exists; records are immutable")

    def _validate_decision(self, d: GovernanceDecision):
        for name in ("decision_id", "subject_id", "decision_type", "approval_evidence", "reasoning", "effective_at", "decided_by"):
            _nonempty(getattr(d, name), name)
        _str_tuple(d.eligible_participants, "eligible_participants", allow_empty=True)
        _str_tuple(d.conflicts, "conflicts", allow_empty=True)
        if d.policy_version is not None and (not isinstance(d.policy_version, int) or d.policy_version < 1):
            raise ValueError("malformed record: policy_version must be None or an integer >= 1")
        if d.decision_id in self.decisions:
            raise ValueError("decision_id already exists; decisions are immutable")

    def _validate_policy(self, p: AllocationPolicy):
        _nonempty(p.policy_id, "policy_id")
        if not isinstance(p.version, int) or p.version < 1:
            raise ValueError("malformed record: version must be >= 1")
        _nonempty(p.basis, "basis")
        if not isinstance(p.weights, dict) or not p.weights:
            raise ValueError("malformed record: weights must be a nonempty mapping")
        if any(not isinstance(k, str) or not k.strip() for k in p.weights):
            raise ValueError("malformed record: weight keys must be contribution IDs")
        if any(not isinstance(v, int) or isinstance(v, bool) or v <= 0 for v in p.weights.values()):
            raise ValueError("malformed record: weights must be positive integers")
        _nonempty(p.approved_by, "approved_by")
        _nonempty(p.approval_reference, "approval_reference")
        _nonempty(p.dispute_process, "dispute_process")
        unknown = sorted(set(p.weights) - set(self.contributions))
        if unknown:
            raise ValueError("policy references unverified/unknown contributions: " + ", ".join(unknown))

    def _pool(self, pool_id: str) -> dict[str, Any]:
        if pool_id not in self.pools:
            raise ValueError("unknown/unregistered value pool")
        return self.pools[pool_id]["pool"]

    def _policy_version(self, policy_id: str, version: int) -> dict[str, Any]:
        key = (policy_id, version)
        if key not in self.policy_versions:
            raise ValueError("unknown/unapproved policy version")
        return self.policy_versions[key]["policy"]

    def _contributor_ids_for_attribution(self, attribution_id: str) -> set[str]:
        record = self.attributions[attribution_id]
        return {
            self.contributions[cid]["contribution"]["contributor_id"]
            for cid in record["contribution_ids"]
        }

    def _validate_attribution_relationship(self, record: dict[str, Any]):
        pool = self._pool(record["pool_id"])
        unknown = sorted(set(record["contribution_ids"]) - set(self.contributions))
        if unknown:
            raise ValueError("attribution references unverified/unknown contributions: " + ", ".join(unknown))
        if record["period"] != pool["period"]:
            raise ValueError("attribution period does not match value pool accounting period")
        if pool["evidence_reference"] not in record["evidence_refs"]:
            raise ValueError("attribution does not establish a supported link to the referenced value pool")
        contributors = self._contributor_ids_for_attribution(record["attribution_id"])
        if record["reviewer"] in contributors:
            raise ValueError("attribution reviewer must be independent of attributed contributors")

    def _allocation_inputs(self, pool_id: str, policy_id: str, attribution_id: str, policy_version: int):
        if attribution_id not in self.attributions:
            raise ValueError("allocation rejected: explicit attribution record required")
        if self.attribution_states.get(attribution_id) != APPROVED:
            raise ValueError("allocation rejected: attribution must be approved")
        attribution = self.attributions[attribution_id]
        if attribution["pool_id"] != pool_id:
            raise ValueError("allocation rejected: attribution references an unrelated value pool")
        pool = self._pool(pool_id)
        if attribution["period"] != pool["period"]:
            raise ValueError("allocation rejected: attribution and pool accounting periods differ")
        policy = self._policy_version(policy_id, policy_version)
        meta = self.policy_versions[(policy_id, policy_version)]
        if meta.get("source") != "governance" or not meta.get("decision_id"):
            raise ValueError("allocation rejected: policy version lacks v0.2 governance approval")
        if not set(policy["weights"]).issubset(set(attribution["contribution_ids"])):
            raise ValueError("allocation rejected: policy includes contributions outside approved attribution scope")
        return pool, policy, attribution

    @staticmethod
    def _compute_amounts(pool: dict[str, Any], policy: dict[str, Any]) -> tuple[int, dict[str, int]]:
        net = max(0, pool["gross_value_minor"] - pool["attributable_costs_minor"])
        weights = policy["weights"]
        total = sum(weights.values())
        amounts = {k: (net * v) // total for k, v in weights.items()}
        remainders = {k: (net * v) % total for k, v in weights.items()}
        remainder = net - sum(amounts.values())
        for key in sorted(weights, key=lambda k: (-remainders[k], k))[:remainder]:
            amounts[key] += 1
        return net, amounts

    def _claim_expected_amount(self, claim: dict[str, Any]) -> int:
        attribution = self.attributions[claim["attribution_id"]]
        pool, policy, _ = self._allocation_inputs(
            attribution["pool_id"], claim["policy_id"], claim["attribution_id"], claim["policy_version"]
        )
        _, amounts = self._compute_amounts(pool, policy)
        owned_contributions = {
            cid for cid in attribution["contribution_ids"]
            if self.contributions[cid]["contribution"]["contributor_id"] == claim["claimant_id"]
        }
        return sum(amounts.get(cid, 0) for cid in owned_contributions)

    def _accounting_key(self, pool: dict[str, Any]) -> tuple[str, str, str]:
        return (pool["period"], pool["currency"].upper(), pool["evidence_reference"])

    def _assert_no_double_count(self, current_claim_id: str, amount_minor: int, pool: dict[str, Any]):
        key = self._accounting_key(pool)
        capacity = max(0, pool["gross_value_minor"] - pool["attributable_costs_minor"])
        used = 0
        for cid, claim in self.claims.items():
            if cid == current_claim_id or self.claim_states.get(cid) not in {APPROVED, PAYABLE, PAID, DISPUTED}:
                continue
            other_attr = self.attributions.get(claim["attribution_id"])
            if not other_attr:
                continue
            other_pool = self._pool(other_attr["pool_id"])
            if self._accounting_key(other_pool) != key:
                continue
            other_capacity = max(0, other_pool["gross_value_minor"] - other_pool["attributable_costs_minor"])
            if other_capacity != capacity:
                raise ValueError("overlapping value pools have inconsistent accounting amounts")
            used += claim["amount_minor"]
        if used + amount_minor > capacity:
            raise ValueError("duplicate/double-counted value would exceed the governed pool capacity")

    # ---------- attribution ----------

    @audit_rejections("PROPOSE_ATTRIBUTION")
    def propose_attribution(self, a: AttributionRecord):
        with self._governance_lock:
            self._ensure_new_id(self.attributions, a.attribution_id, "attribution_id")
            _str_tuple(a.contribution_ids, "contribution_ids")
            for name in ("pool_id", "system_id", "period", "method_version", "reviewer"):
                _nonempty(getattr(a, name), name)
            _str_tuple(a.evidence_refs, "evidence_refs")
            if not isinstance(a.evidence_sources, tuple) or any(
                not isinstance(item, tuple) or len(item) != 2
                or not isinstance(item[0], str) or not item[0].strip()
                or item[1] not in {"OPERATOR_SUPPLIED", "INDEPENDENT_REVIEWED"}
                for item in a.evidence_sources
            ):
                raise ValueError("malformed record: evidence_sources must classify each evidence ref")
            source_map = {ref: source for ref, source in a.evidence_sources}
            if set(source_map) != set(a.evidence_refs) or len(source_map) != len(a.evidence_sources):
                raise ValueError("malformed record: each evidence_ref must have exactly one evidence source classification")
            _str_tuple(a.limitations, "limitations", allow_empty=True)
            if a.status != PROPOSED:
                raise ValueError("new attribution must start in PROPOSED state")
            self._pool(a.pool_id)
            unknown = sorted(set(a.contribution_ids) - set(self.contributions))
            if unknown:
                raise ValueError("attribution references unverified/unknown contributions: " + ", ".join(unknown))
            self._record("ATTRIBUTION_PROPOSED", {"record": asdict(a)})
            return {"status": PROPOSED, "attribution_id": a.attribution_id}

    @audit_rejections("APPROVE_ATTRIBUTION")
    def approve_attribution(self, attribution_id: str, decision: GovernanceDecision):
        with self._governance_lock:
            if attribution_id not in self.attributions:
                raise ValueError("unknown attribution")
            if self.attribution_states.get(attribution_id) != PROPOSED:
                raise ValueError("attribution is not in PROPOSED state")
            self._validate_decision(decision)
            if decision.subject_id != attribution_id or decision.decision_type != "ATTRIBUTION_APPROVAL":
                raise ValueError("decision does not approve this attribution")
            if decision.policy_version is not None:
                raise ValueError("attribution approval must not bind a policy version")
            record = self.attributions[attribution_id]
            self._validate_attribution_relationship(record)
            if decision.decided_by != record["reviewer"]:
                raise ValueError("attribution approval must be issued by the recorded independent reviewer")
            if decision.decided_by in self._contributor_ids_for_attribution(attribution_id):
                raise ValueError("self-adjudication rejected")
            self._record("ATTRIBUTION_APPROVED", {"attribution_id": attribution_id, "decision": asdict(decision)})
            return {"status": APPROVED, "attribution_id": attribution_id, "decision_id": decision.decision_id}

    @audit_rejections("REVERSE_ATTRIBUTION")
    def reverse_attribution(self, attribution_id: str, decision: GovernanceDecision):
        with self._governance_lock:
            if attribution_id not in self.attributions:
                raise ValueError("unknown attribution")
            if self.attribution_states.get(attribution_id) != APPROVED:
                raise ValueError("only an approved attribution may be reversed")
            active_claims = [
                claim_id for claim_id, claim in self.claims.items()
                if claim["attribution_id"] == attribution_id
                and self.claim_states.get(claim_id) in {APPROVED, DISPUTED, PAYABLE, PAID}
            ]
            if active_claims:
                raise ValueError("attribution reversal requires dependent claims to be resolved or reversed first")
            self._validate_decision(decision)
            if decision.subject_id != attribution_id or decision.decision_type != "ATTRIBUTION_REVERSAL":
                raise ValueError("decision does not reverse this attribution")
            if decision.policy_version is not None:
                raise ValueError("attribution reversal must not bind a policy version")
            if decision.decided_by in self._contributor_ids_for_attribution(attribution_id):
                raise ValueError("self-adjudication rejected")
            self._record("ATTRIBUTION_REVERSED", {"attribution_id": attribution_id, "decision": asdict(decision)})
            return {"status": REVERSED, "attribution_id": attribution_id, "decision_id": decision.decision_id}

    # ---------- policy governance ----------

    @audit_rejections("LEGACY_POLICY_APPROVAL")
    def approve_policy(self, p: AllocationPolicy):
        raise ValueError(
            "governance kernel rejects direct legacy policy approval; use approve_policy_version with GovernanceDecision"
        )

    @audit_rejections("APPROVE_POLICY_VERSION")
    def approve_policy_version(self, policy: AllocationPolicy, decision: GovernanceDecision):
        with self._governance_lock:
            self._validate_policy(policy)
            self._validate_decision(decision)
            if decision.subject_id != policy.policy_id or decision.policy_version != policy.version:
                raise ValueError("policy decision subject/version mismatch")
            if decision.decided_by != policy.approved_by:
                raise ValueError("policy decision maker must match approved_by")
            existing_versions = sorted(v for pid, v in self.policy_versions if pid == policy.policy_id)
            if (policy.policy_id, policy.version) in self.policy_versions:
                raise ValueError("retroactive policy replacement rejected; approved versions are immutable")
            if existing_versions:
                if policy.version != existing_versions[-1] + 1:
                    raise ValueError("policy revisions must append exactly one new version")
                if decision.decision_type != "POLICY_CORRECTION":
                    raise ValueError("existing policy may only be revised through an explicit correction decision")
            else:
                if policy.version != 1:
                    raise ValueError("first governance policy version must be version 1")
                if decision.decision_type != "POLICY_APPROVAL":
                    raise ValueError("first policy version requires POLICY_APPROVAL decision")
            payload = {
                "policy": asdict(policy),
                "decision": asdict(decision),
                "policy_sha256": sha(asdict(policy)),
            }
            self._record("GOVERNANCE_POLICY_VERSION_APPROVED", payload)
            return {
                "status": APPROVED,
                "policy_id": policy.policy_id,
                "version": policy.version,
                "policy_sha256": payload["policy_sha256"],
            }

    # ---------- governed allocation ----------

    @audit_rejections("CALCULATE_ALLOCATION")
    def calculate_allocation(
        self,
        pool_id: str,
        policy_id: str,
        attribution_id: str | None = None,
        policy_version: int | None = None,
    ):
        """Calculate a governed hypothetical allocation; never pays money.

        v0.2 intentionally strengthens the inherited method: callers through the
        governance kernel must supply an approved attribution and explicit approved
        policy version. The original ContributionBridge class remains unchanged.
        """
        with self._governance_lock:
            if attribution_id is None:
                raise ValueError("allocation rejected: explicit attribution record required")
            if policy_version is None:
                raise ValueError("allocation rejected: explicit approved policy version required")
            pool, policy, attribution = self._allocation_inputs(pool_id, policy_id, attribution_id, policy_version)
            net, amounts = self._compute_amounts(pool, policy)
            identity = {
                "pool_id": pool_id,
                "policy_id": policy_id,
                "policy_version": policy_version,
                "attribution_id": attribution_id,
                "pool_sha256": sha(pool),
                "policy_sha256": sha(policy),
                "attribution_sha256": sha(attribution),
            }
            allocation_id = "alloc-" + sha(identity)[:24]
            if allocation_id in self.allocations:
                return dict(self.allocations[allocation_id])
            result = {
                "allocation_id": allocation_id,
                "status": "CALCULATED_NOT_PAID",
                **identity,
                "currency": pool["currency"].upper(),
                "gross_value_minor": pool["gross_value_minor"],
                "costs_minor": pool["attributable_costs_minor"],
                "distributable_minor": net,
                "basis": policy["basis"],
                "weights": dict(policy["weights"]),
                "allocations_minor": amounts,
                "governance": {
                    "approved_by": policy["approved_by"],
                    "approval_reference": policy["approval_reference"],
                    "dispute_process": policy["dispute_process"],
                    "attribution_decision_id": self.attribution_decisions[attribution_id],
                    "policy_decision_id": self.policy_versions[(policy_id, policy_version)]["decision_id"],
                },
                "snapshots": {
                    "pool": dict(pool),
                    "policy": dict(policy),
                    "attribution": dict(attribution),
                },
                "limitations": [
                    "This governed calculation creates no legal entitlement and executes no payment.",
                    "Attribution evidence is recorded and reviewed but economic causation is not proven by software alone.",
                    "Identity labels remain local identifiers, not production authentication.",
                ],
            }
            self._record("GOVERNED_ALLOCATION_CALCULATED", result)
            return result

    def reproduce_allocation(self, allocation_id: str):
        if allocation_id not in self.allocations:
            raise ValueError("unknown governed allocation")
        stored = self.allocations[allocation_id]
        net, amounts = self._compute_amounts(stored["snapshots"]["pool"], stored["snapshots"]["policy"])
        return {
            "allocation_id": allocation_id,
            "policy_id": stored["policy_id"],
            "policy_version": stored["policy_version"],
            "distributable_minor": net,
            "allocations_minor": amounts,
            "matches_recorded": net == stored["distributable_minor"] and amounts == stored["allocations_minor"],
        }

    # ---------- claims ----------

    @audit_rejections("PROPOSE_CLAIM")
    def propose_claim(self, claim: Claim):
        with self._governance_lock:
            self._ensure_new_id(self.claims, claim.claim_id, "claim_id")
            for name in ("claimant_id", "attribution_id", "policy_id"):
                _nonempty(getattr(claim, name), name)
            if not isinstance(claim.policy_version, int) or claim.policy_version < 1:
                raise ValueError("malformed record: claim policy_version must be >= 1")
            if not isinstance(claim.amount_minor, int) or isinstance(claim.amount_minor, bool) or claim.amount_minor < 0:
                raise ValueError("malformed record: amount_minor must be a nonnegative integer")
            _currency(claim.currency)
            if claim.status != PROPOSED:
                raise ValueError("new claim must start in PROPOSED state")
            if claim.decision_id:
                raise ValueError("proposed claim must not pre-populate decision_id")
            if claim.attribution_id not in self.attributions or self.attribution_states.get(claim.attribution_id) != APPROVED:
                raise ValueError("claim requires an approved attribution")
            contributors = self._contributor_ids_for_attribution(claim.attribution_id)
            if claim.claimant_id not in contributors:
                raise ValueError("claimant is not an attributed contributor")
            self._record("CLAIM_PROPOSED", {"claim": asdict(claim)})
            return {"status": PROPOSED, "claim_id": claim.claim_id}

    @audit_rejections("APPROVE_CLAIM")
    def approve_claim(self, claim_id: str, decision: GovernanceDecision):
        with self._governance_lock:
            if claim_id not in self.claims:
                raise ValueError("unknown claim")
            if self.claim_states.get(claim_id) != PROPOSED:
                raise ValueError("claim is not in PROPOSED state")
            claim = self.claims[claim_id]
            self._validate_decision(decision)
            if decision.subject_id != claim_id or decision.decision_type != "CLAIM_APPROVAL":
                raise ValueError("decision does not approve this claim")
            if decision.policy_version != claim["policy_version"]:
                raise ValueError("claim decision policy version mismatch")
            if decision.decided_by == claim["claimant_id"]:
                raise ValueError("self-adjudication rejected")
            policy = self._policy_version(claim["policy_id"], claim["policy_version"])
            attribution = self.attributions[claim["attribution_id"]]
            pool = self._pool(attribution["pool_id"])
            if _currency(claim["currency"]) != _currency(pool["currency"]):
                raise ValueError("claim currency is inconsistent with attributed value pool")
            if not set(policy["weights"]).issubset(set(attribution["contribution_ids"])):
                raise ValueError("claim policy exceeds approved attribution scope")
            expected = self._claim_expected_amount(claim)
            if claim["amount_minor"] != expected:
                raise ValueError("claim amount does not match governed allocation under referenced policy version")
            for other_id, other in self.claims.items():
                if other_id == claim_id or self.claim_states.get(other_id) not in {APPROVED, PAYABLE, PAID, DISPUTED}:
                    continue
                if (
                    other["claimant_id"], other["attribution_id"], other["policy_id"], other["policy_version"]
                ) == (
                    claim["claimant_id"], claim["attribution_id"], claim["policy_id"], claim["policy_version"]
                ):
                    raise ValueError("duplicate claim would count the same governed allocation twice")
            self._assert_no_double_count(claim_id, claim["amount_minor"], pool)
            self._record("CLAIM_APPROVED", {"claim_id": claim_id, "decision": asdict(decision)})
            return {"status": APPROVED, "claim_id": claim_id, "decision_id": decision.decision_id}

    # ---------- disputes ----------

    @audit_rejections("OPEN_DISPUTE")
    def open_dispute(self, dispute: Dispute):
        with self._governance_lock:
            self._ensure_new_id(self.disputes, dispute.dispute_id, "dispute_id")
            for name in ("claim_id", "grounds", "submitted_at", "reviewer"):
                _nonempty(getattr(dispute, name), name)
            _str_tuple(dispute.evidence_refs, "evidence_refs", allow_empty=True)
            if dispute.decision or dispute.remedy:
                raise ValueError("new dispute must not pre-populate decision or remedy")
            if dispute.appeal_status != "OPEN":
                raise ValueError("new dispute appeal_status must be OPEN")
            if dispute.claim_id not in self.claims:
                raise ValueError("unknown claim")
            prior = self.claim_states.get(dispute.claim_id)
            if prior not in {APPROVED, PAYABLE}:
                raise ValueError("only an approved or payable claim may enter dispute")
            claim = self.claims[dispute.claim_id]
            original_decision = self.decisions[self.claim_decisions[dispute.claim_id]]
            if dispute.reviewer in {claim["claimant_id"], original_decision["decided_by"]}:
                raise ValueError("dispute reviewer must be independent of claimant and original decision maker")
            self._record("DISPUTE_OPENED", {"dispute": asdict(dispute), "prior_claim_state": prior})
            return {"status": DISPUTED, "claim_id": dispute.claim_id, "dispute_id": dispute.dispute_id}

    @audit_rejections("RESOLVE_DISPUTE")
    def resolve_dispute(self, dispute_id: str, decision: GovernanceDecision, remedy: str):
        with self._governance_lock:
            if dispute_id not in self.disputes:
                raise ValueError("unknown dispute")
            if dispute_id in self.dispute_resolutions:
                raise ValueError("dispute already resolved; records are immutable")
            _nonempty(remedy, "remedy")
            self._validate_decision(decision)
            dispute = self.disputes[dispute_id]
            claim = self.claims[dispute["claim_id"]]
            if decision.subject_id != claim["claim_id"]:
                raise ValueError("appeal decision must target the disputed claim")
            if decision.policy_version != claim["policy_version"]:
                raise ValueError("appeal decision policy version mismatch")
            if decision.decided_by != dispute["reviewer"]:
                raise ValueError("appeal decision must be issued by recorded independent reviewer")
            original_decision = self.decisions[self.claim_decisions[claim["claim_id"]]]
            if decision.decided_by in {claim["claimant_id"], original_decision["decided_by"]}:
                raise ValueError("appeal reviewer is not independent")
            if decision.decision_type == "CLAIM_APPEAL_OVERTURN":
                outcome = "OVERTURN"
            elif decision.decision_type == "CLAIM_APPEAL_UPHOLD":
                outcome = "UPHOLD"
            else:
                raise ValueError("appeal decision_type must be CLAIM_APPEAL_OVERTURN or CLAIM_APPEAL_UPHOLD")
            payload = {
                "dispute_id": dispute_id,
                "decision": asdict(decision),
                "outcome": outcome,
                "remedy": remedy,
                "old_decision_id": original_decision["decision_id"],
            }
            self._record("DISPUTE_RESOLVED", payload)
            return {
                "status": self.claim_states[claim["claim_id"]],
                "claim_id": claim["claim_id"],
                "old_decision_id": original_decision["decision_id"],
                "new_decision_id": decision.decision_id,
                "remedy": remedy,
            }

    # ---------- obligations and payments ----------

    @audit_rejections("CREATE_OBLIGATION")
    def create_obligation(self, obligation: Obligation):
        with self._governance_lock:
            self._ensure_new_id(self.obligations, obligation.obligation_id, "obligation_id")
            for name in ("claim_id", "debtor", "creditor", "due_date"):
                _nonempty(getattr(obligation, name), name)
            if obligation.claim_id not in self.claims:
                raise ValueError("unknown claim")
            if self.claim_states.get(obligation.claim_id) != APPROVED:
                raise ValueError("obligation requires an approved claim")
            claim = self.claims[obligation.claim_id]
            if obligation.creditor != claim["claimant_id"]:
                raise ValueError("obligation creditor must match claim claimant")
            if not isinstance(obligation.amount_due_minor, int) or isinstance(obligation.amount_due_minor, bool) or obligation.amount_due_minor < 0:
                raise ValueError("malformed record: amount_due_minor must be a nonnegative integer")
            if obligation.amount_due_minor != claim["amount_minor"]:
                raise ValueError("obligation amount must equal approved claim amount")
            if obligation.amount_paid_minor != 0:
                raise ValueError("new obligation must start with amount_paid_minor = 0")
            _str_tuple(obligation.payment_evidence, "payment_evidence", allow_empty=True)
            if obligation.payment_evidence:
                raise ValueError("new obligation must not pre-populate payment evidence")
            if obligation.status != PAYABLE:
                raise ValueError("new obligation must start in PAYABLE state")
            self._record("OBLIGATION_CREATED", {"obligation": asdict(obligation)})
            return {"status": PAYABLE, "obligation_id": obligation.obligation_id, "outstanding_minor": obligation.amount_due_minor}

    @audit_rejections("RECORD_PAYMENT")
    def record_payment(self, obligation_id: str, amount_minor: int, evidence_ref: str):
        with self._governance_lock:
            if obligation_id not in self.obligations:
                raise ValueError("unknown obligation")
            if self.obligation_states.get(obligation_id) != PAYABLE:
                raise ValueError("payment may only be applied to a PAYABLE obligation")
            if not isinstance(amount_minor, int) or isinstance(amount_minor, bool) or amount_minor <= 0:
                raise ValueError("payment amount must be a positive integer minor-unit amount")
            current = self.obligation_paid_minor[obligation_id]
            due = self.obligations[obligation_id]["amount_due_minor"]
            if current + amount_minor > due:
                raise ValueError("payment would exceed obligation amount")
            if not isinstance(evidence_ref, str) or not evidence_ref.strip():
                self._record("PAYMENT_REPORTED_UNVERIFIED", {
                    "obligation_id": obligation_id,
                    "reported_amount_minor": amount_minor,
                    "reason": "supporting payment evidence required",
                })
                return {
                    "status": "UNVERIFIED",
                    "obligation_id": obligation_id,
                    "amount_paid_minor": current,
                    "outstanding_minor": due - current,
                }
            new_paid = current + amount_minor
            new_status = PAID if new_paid == due else PAYABLE
            self._record("PAYMENT_RECORDED", {
                "obligation_id": obligation_id,
                "amount_minor": amount_minor,
                "evidence_ref": evidence_ref,
                "new_amount_paid_minor": new_paid,
                "new_status": new_status,
            })
            return {
                "status": new_status,
                "obligation_id": obligation_id,
                "amount_paid_minor": new_paid,
                "outstanding_minor": due - new_paid,
            }

    @audit_rejections("REVERSE_OBLIGATION")
    def reverse_obligation(self, obligation_id: str, decision: GovernanceDecision):
        with self._governance_lock:
            if obligation_id not in self.obligations:
                raise ValueError("unknown obligation")
            if self.obligation_states.get(obligation_id) == REVERSED:
                raise ValueError("obligation already reversed")
            self._validate_decision(decision)
            if decision.subject_id != obligation_id or decision.decision_type != "OBLIGATION_REVERSAL":
                raise ValueError("decision does not reverse this obligation")
            self._record("OBLIGATION_REVERSED", {"obligation_id": obligation_id, "decision": asdict(decision)})
            return {"status": REVERSED, "obligation_id": obligation_id, "decision_id": decision.decision_id}

    def obligation_balance(self, obligation_id: str) -> dict[str, Any]:
        if obligation_id not in self.obligations:
            raise ValueError("unknown obligation")
        due = self.obligations[obligation_id]["amount_due_minor"]
        paid = self.obligation_paid_minor[obligation_id]
        return {
            "obligation_id": obligation_id,
            "status": self.obligation_states[obligation_id],
            "amount_due_minor": due,
            "amount_paid_minor": paid,
            "outstanding_minor": due - paid,
            "payment_evidence": tuple(self.obligation_payment_evidence[obligation_id]),
        }

    # ---------- externally retained checkpoints ----------

    def checkpoint(self) -> dict[str, Any]:
        text = self.path.read_text(encoding="utf-8") if self.path.exists() else ""
        return {
            "sequence": len(self.events),
            "head_hash": self.events[-1]["hash"] if self.events else "GENESIS",
            "audit_sha256": sha(text),
        }

    def write_checkpoint(self, checkpoint_path: str | Path):
        target = Path(checkpoint_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.checkpoint()
        target.write_text(canonical(payload) + "\n", encoding="utf-8")
        return payload

    def verify_checkpoint(self, checkpoint_path: str | Path):
        target = Path(checkpoint_path)
        if not target.exists():
            raise ValueError("independently retained checkpoint is missing")
        expected = json.loads(target.read_text(encoding="utf-8"))
        actual = self.checkpoint()
        if expected != actual:
            raise ValueError("integrity failure against independently retained checkpoint")
        return {"status": "CHECKPOINT_VERIFIED", **actual}
