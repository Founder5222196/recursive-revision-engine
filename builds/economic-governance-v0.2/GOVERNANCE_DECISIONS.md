# RRE Economic Governance Kernel v0.2 — Governance Design Decisions

This file records implementation decisions that go beyond, or resolve ambiguities in, the Milestone 2 proposal. They are **builder decisions**, not claims that the proposal itself required the exact implementation choice.

## D-001 — Extend by subclassing; do not modify the prototype

**Decision:** `EconomicGovernanceKernel` subclasses `ContributionBridge`. `contribution_bridge.py` and `test_contribution_bridge.py` are not changed.

**Rationale:** The order requires extension without rewriting prototype history. Subclassing keeps the prototype executable and testable in its original form while allowing v0.2 to enforce stricter gates for governed allocations.

## D-002 — Direct legacy policy approval is blocked through v0.2

**Decision:** Calls to `approve_policy(...)` through `EconomicGovernanceKernel` are rejected. v0.2 callers must use `approve_policy_version(...)` with a `GovernanceDecision`.

**Rationale:** If the governance kernel inherited direct prototype policy approval unchanged, an operator could bypass the new authority and version-decision record while still using the governed allocation API.

**Compatibility:** The original `ContributionBridge.approve_policy(...)` remains untouched and available on the prototype class.

## D-003 — Historical prototype policies are preserved but are not sufficient for a new v0.2 governed allocation

**Decision:** Replay recognizes prototype `ALLOCATION_POLICY_APPROVED` records and stores their versions as historical policy evidence with source `prototype`. A new v0.2 governed allocation requires a policy version whose source is `governance` and that has a v0.2 decision ID.

**Rationale:** Silently upgrading an old approval record into a new governance decision would rewrite the historical meaning of the prototype.

## D-004 — Add `decided_by` to GovernanceDecision

**Decision:** `GovernanceDecision` adds `decided_by`.

**Ambiguity resolved:** The proposal requires self-adjudication to be rejected in code, but its listed `GovernanceDecision` fields do not identify who actually made the decision.

**Rationale:** A concrete actor identifier is necessary to compare the adjudicator with a claimant, contributor, or original reviewer.

**Limitation:** Local identifiers are not authenticated identities.

## D-005 — Make GovernanceDecision.policy_version optional for non-policy decisions

**Decision:** `policy_version` may be `None` for attribution approval/reversal and obligation reversal. Claim and policy decisions require a concrete positive version.

**Rationale:** The proposal places `policy_version` on every governance decision, but attribution occurs before policy selection and should not be falsely bound to an unrelated version.

## D-006 — Add `policy_version` to Claim

**Decision:** `Claim` adds an explicit `policy_version` field.

**Ambiguity resolved:** The proposal says a claim under an unapproved policy version cannot be approved, but its listed `Claim` fields identify only `policy_id`.

**Rationale:** Historical reproducibility and retroactivity protection require the exact version to be part of the asserted claim.

## D-007 — Add explicit evidence-source classification to AttributionRecord

**Decision:** `AttributionRecord` adds `evidence_sources`, mapping every `evidence_ref` to either `OPERATOR_SUPPLIED` or `INDEPENDENT_REVIEWED`.

**Ambiguity resolved:** Economic Rule 8 requires operator-supplied evidence to be distinguishable from independently reviewed evidence, but the listed record fields contain only untyped `evidence_refs`.

**Rationale:** The distinction should be machine-visible instead of inferred from prose.

**Limitation:** `INDEPENDENT_REVIEWED` is a recorded classification, not cryptographic or institutional proof that independence is genuine.

## D-008 — Define the minimum machine-checkable contribution-to-pool link

**Decision:** An attribution can be approved only when:

1. `AttributionRecord.pool_id` exists;
2. attribution period equals the value-pool period; and
3. the value pool's `evidence_reference` appears in the attribution's `evidence_refs`.

**Ambiguity resolved:** The prototype has no system ID on `ValuePool` and no pre-existing graph that can independently determine causal relevance.

**Rationale:** v0.2 needs a deterministic way to reject an unsupported or unrelated pool without pretending to solve causal attribution scientifically.

**Limitation:** This proves an explicit evidence linkage in the governance record, not real-world economic causation.

## D-009 — Attribution approval must be issued by the record's independent reviewer

**Decision:** `ATTRIBUTION_APPROVAL.decided_by` must equal `AttributionRecord.reviewer`, and that reviewer must differ from every attributed contributor ID owner.

**Rationale:** Merely naming a reviewer on the attribution without binding approval authority to that identity would leave the independence rule unenforced.

## D-010 — Policy versions append exactly one version at a time

**Decision:** A first governance policy is version 1 with `POLICY_APPROVAL`. Later versions must be exactly `max_version + 1` and use `POLICY_CORRECTION`. Existing versions cannot be replaced.

**Rationale:** This gives the retroactivity rule a simple, deterministic state machine and prevents silent insertion or replacement of history.

## D-011 — Historical claims never float to the latest policy

**Decision:** Every approved claim remains bound to its explicit `policy_version`. A later policy revision does not mutate the claim or its prior governed allocation.

**Rationale:** This is the central implementation of “no unilateral retroactive rule changes.”

## D-012 — Governed allocations keep the prototype arithmetic

**Decision:** v0.2 retains the prototype's distributable-value calculation and deterministic largest-remainder allocation.

**Rationale:** Milestone 2 governs the legitimacy around the calculation rather than changing the prototype's arithmetic basis.

**Limitation:** Integer weights remain illustrative. Their fairness is not established by this release.

## D-013 — Claim amount must equal the claimant's governed allocation share

**Decision:** v0.2 approves a claim only if `amount_minor` equals the sum of governed allocation amounts for contributions in the attribution owned by that claimant.

**Ambiguity resolved:** The proposal defines a claim amount but does not specify whether v0.2 should accept arbitrary asserted amounts below, equal to, or above a calculated allocation.

**Rationale:** Exact equality makes the first governance kernel deterministic and prevents the claim object from becoming an unconstrained financial demand.

## D-014 — Proposed claims may reference a not-yet-approved policy version, but approval may not

**Decision:** A claim is allowed to exist as a `PROPOSED` assertion even if its referenced policy version is not approved. `approve_claim(...)` rejects it until the version exists with v0.2 governance approval.

**Rationale:** This preserves the distinction between asserting a claim and authorizing it, and directly supports the proposal's adversarial case.

## D-015 — Prevent duplicate claims by economic identity

**Decision:** A second active claim with the same `(claimant_id, attribution_id, policy_id, policy_version)` is rejected.

**Rationale:** Different `claim_id` strings must not allow the same governed share to be asserted twice.

## D-016 — Define overlapping-pool accounting identity

**Decision:** v0.2 treats pools with the same `(period, currency, evidence_reference)` as representing the same accounting identity for double-counting checks.

**Rationale:** The proposal requires protection against overlapping pools but does not provide a pool-overlap schema.

**Behavior:** Active approved/disputed/payable/paid claims sharing that accounting identity cannot exceed its distributable capacity. If two pools share the identity but disagree on distributable amount, approval is rejected as inconsistent accounting.

**Limitation:** Production accounting needs a stronger canonical value-event or ledger-entry identity.

## D-017 — Choose prevention rather than automatic reconciliation for double counting

**Decision:** v0.2 rejects duplicate or over-capacity claims. It does not automatically generate reconciliation adjustments.

**Rationale:** The proposal permits “prevented or explicitly reconciled.” Automatic reconciliation would require rules not supplied by the proposal.

## D-018 — Preserve immutable original records; replay current state from events

**Decision:** The original `AttributionRecord`, `Claim`, `Dispute`, and `Obligation` payloads are not overwritten when status changes. Current state is held in replayed state maps.

**Rationale:** This preserves history and makes dispute, payment, and reversal transitions inspectable.

## D-019 — Dispute review must be independent of both claimant and original adjudicator

**Decision:** The appeal reviewer cannot equal the claimant or the original claim decision maker.

**Rationale:** “Independent reviewer” is otherwise only descriptive text.

## D-020 — Uphold restores pre-dispute state; overturn reverses

**Decision:** A dispute records the claim's state immediately before dispute. `CLAIM_APPEAL_UPHOLD` restores that state. `CLAIM_APPEAL_OVERTURN` moves the claim to `REVERSED` and reverses an unpaid linked obligation.

**Rationale:** An appeal can occur before or after an obligation becomes payable. Restoring the exact prior state avoids silently changing economic posture merely because an appeal occurred.

## D-021 — Paid obligations are not automatically erased by claim appeal logic

**Decision:** An appeal overturn automatically reverses linked obligations only when they are not already `PAID`. A paid obligation requires an explicit later reversal/correction path.

**Rationale:** Undoing a completed payment has materially different accounting consequences and should not happen as a side effect of a claim-state change.

## D-022 — Payment without evidence is recorded but does not count

**Decision:** A reported payment with no supporting evidence creates `PAYMENT_REPORTED_UNVERIFIED`, leaves paid amount unchanged, and leaves the obligation `PAYABLE`.

**Rationale:** This implements “no silent nonpayment” and the adversarial payment-evidence case without discarding the fact that someone reported a payment.

## D-023 — All governance validation rejections leave a generic audit event

**Decision:** Public governance mutations are wrapped so a `ValueError` rejection writes `GOVERNANCE_ACTION_REJECTED` with action, subject, and reason.

**Rationale:** Economic Rule 7 requires rejections to remain visible, not merely disappear as exceptions.

**Exception:** A storage failure itself cannot be guaranteed to produce a rejection event because the ledger is the component that failed.

## D-024 — Use a deterministic governed allocation ID

**Decision:** `allocation_id` is derived from pool ID, policy ID/version, attribution ID, and hashes of their snapshots.

**Rationale:** Repeating an identical governed calculation should not create multiple economically distinct calculations merely because it was requested twice.

## D-025 — Reproduce historical allocation from stored snapshots

**Decision:** Each governed allocation stores pool, policy, and attribution snapshots plus their hashes. `reproduce_allocation(...)` recomputes from the recorded snapshots.

**Rationale:** A future policy version must not alter the reproducibility of an old calculation.

## D-026 — External integrity checkpoint is explicit, not automatic

**Decision:** The kernel can write and verify a separate checkpoint containing sequence, audit head hash, and audit-file SHA-256. It does not automatically overwrite that checkpoint after every event.

**Rationale:** A checkpoint that the same process silently updates alongside every ledger change is not meaningfully independent. Operational custody is left to the record keeper or a separate retaining party.

**Limitation:** If an attacker can rewrite both the audit and the retained checkpoint, this mechanism does not detect the attack. Signed or independently controlled retention remains a production requirement.

## D-027 — In-process concurrency is serialized with an RLock

**Decision:** Governance mutations use a re-entrant process-local lock.

**Rationale:** This is enough to make the included concurrent duplicate-approval test deterministic without adding non-standard dependencies.

**Limitation:** It is not a multi-process, multi-host, or database transaction mechanism.

## D-028 — Write failure publishes state only after the append succeeds

**Decision:** v0.2 relies on the inherited append-then-replay order. If append raises before success, the attempted governance record is not added to the in-memory replayed state.

**Rationale:** This preserves the prototype's append semantics while making the failure behavior testable.

**Limitation:** A partial low-level filesystem write is not turned into a full transactional journal by this milestone.

## D-029 — Governance identity checks remain local-label checks

**Decision:** The code enforces that recorded IDs differ where independence is required, but does not claim authentication, proof-of-personhood, institutional authorization, or Sybil resistance.

**Rationale:** The proposal identifies authenticated identity as a production need, but the supplied prototype has only local pseudonymous labels and Milestone 2 does not supply an identity service.

## D-030 — Governance records are explicitly non-legal

**Decision:** Code limitations and this specification repeatedly state that calculations, claims, and obligations are governance records rather than legal entitlements.

**Rationale:** The order explicitly forbids creating the appearance of a legal entitlement.

## D-031 — Evidence Sufficiency results confer no economic authority

**Decision:** No code path, decision rule, or release statement imports Evidence Sufficiency pass rates as evidence that attribution, allocation, governance, or legal validity is correct.

**Rationale:** The packet explicitly separates those workstreams.

## D-032 — No execution claims in builder artifacts

**Decision:** The manifest lists expected outcomes and commands for the record keeper, not observed results.

**Rationale:** Execution belongs to the record keeper under the packet's execution arrangement.

## D-033 — Manifest self-hash is reported outside the manifest file

**Decision:** `BUILD_MANIFEST.md` lists exact SHA-256 values for the other four returned files. Its own exact byte hash is reported in the enclosing return message/package metadata after the manifest is finalized.

**Ambiguity resolved:** The order asks the manifest to contain a SHA-256 for every returned file, including the manifest itself. Embedding the manifest's own exact SHA-256 changes the manifest bytes and therefore changes that SHA-256.

**Rationale:** Reporting the finalized manifest hash externally is the only way to provide the exact byte hash without falsely claiming a self-referential value. The manifest also states this explicitly.
