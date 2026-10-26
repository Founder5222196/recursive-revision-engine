# RRE Economic Governance Kernel v0.2 — Normative Specification

**Status:** Milestone 2 release-candidate specification. This document defines the behavior implemented by `economic_governance.py`. It extends the ContributionBridge prototype without modifying the prototype source or its tests.

**Important boundary:** records produced by this kernel are governance records. A recorded claim, decision, obligation, payment status, or allocation does **not** by itself create a legal entitlement, wage, royalty, ownership interest, debt enforceable at law, or transfer of funds. Legal enforceability requires an appropriate agreement, recognized legal framework, and applicable enforcement mechanism.

## 1. Purpose

The kernel moves RRE from a hypothetical contribution-to-value calculation toward an auditable governance process that separates:

1. verified technical contribution;
2. attribution of measured value to that contribution;
3. rule-making authority;
4. individual claim adjudication;
5. dispute and appeal handling; and
6. tracking of an authorized obligation and its payment evidence.

The governing principle is separation of powers: the system owner must not be able to verify a contribution, decide that the contribution deserves economic recognition, determine the governing allocation rule, adjudicate the contributor's own claim, and silently decide whether an approved obligation remains visible.

## 2. Relationship to ContributionBridge v0.1

`EconomicGovernanceKernel` subclasses `ContributionBridge`.

The prototype's source file and tests remain unchanged. Its existing records retain their original meaning:

- `Contribution` records technical provenance and behavioral evidence.
- `ValuePool` records supplied value measurements and costs.
- `AllocationPolicy` records a versioned allocation rule.
- the prototype's `CALCULATED_NOT_PAID` output remains a hypothetical calculation, not payment or legal entitlement.

The governance kernel strengthens operations invoked through v0.2:

- direct legacy policy approval is rejected through the governance kernel;
- a governed allocation requires an approved `AttributionRecord` and an explicitly approved v0.2 policy version;
- new claims require approved attribution and independent adjudication;
- policy history, disputes, obligations, payments, reversals, and rejection events remain replayable from the append-only audit log.

A historical prototype policy found in an existing audit log is preserved as historical evidence, but it is not sufficient by itself for a new v0.2 governed allocation or claim because it lacks a v0.2 `GovernanceDecision`.

## 3. First-class governance records

### 3.1 AttributionRecord

Required proposal fields:

- `attribution_id`
- `contribution_ids`
- `pool_id`
- `system_id`
- `period`
- `method_version`
- `evidence_refs`
- `reviewer`
- `status`
- `limitations`

Implementation addition:

- `evidence_sources`: one explicit source classification per `evidence_ref`, either `OPERATOR_SUPPLIED` or `INDEPENDENT_REVIEWED`.

The source classification is itself a governance assertion, not authenticated proof of independence. The kernel does not infer independent verification from an unlabeled reference.

A new attribution starts in `PROPOSED` state. Approval requires:

- all referenced contributions are verified in the prototype ledger;
- the referenced value pool exists;
- attribution period equals the pool accounting period;
- the value pool's own `evidence_reference` appears in the attribution evidence set;
- every evidence reference has exactly one source classification;
- the recorded attribution reviewer is not one of the attributed contributors; and
- an `ATTRIBUTION_APPROVAL` `GovernanceDecision` is issued by that recorded reviewer.

### 3.2 GovernanceDecision

Required proposal fields:

- `decision_id`
- `subject_id`
- `decision_type`
- `policy_version`
- `eligible_participants`
- `approval_evidence`
- `conflicts`
- `reasoning`
- `effective_at`

Implementation addition:

- `decided_by`: the actor responsible for the decision.

`decided_by` is required because self-adjudication cannot be enforced from prose alone. `policy_version` is `None` for decisions that are not governed by an allocation policy, such as attribution approval or reversal.

Decision records are immutable after they are written.

### 3.3 Claim

Required proposal fields:

- `claim_id`
- `claimant_id`
- `attribution_id`
- `policy_id`
- `amount_minor`
- `currency`
- `status`
- `decision_id`

Implementation addition:

- `policy_version`: the exact policy version under which the claim is asserted.

A new claim starts in `PROPOSED` state with an empty `decision_id`. The original claim record is immutable. Current state and current decision linkage are replayed from later audit events rather than by rewriting the original record.

A claim may be proposed only when its attribution is approved and the claimant owns at least one contribution inside that attribution. Proposal alone creates no entitlement.

A claim may be approved only when:

- the referenced policy version has explicit v0.2 governance approval;
- the attribution remains approved;
- claim currency matches the attributed value pool;
- the policy's weighted contributions are within the approved attribution scope;
- the claimed amount exactly matches the claimant's share under the governed deterministic allocation;
- the adjudicator is not the claimant; and
- approval would not duplicate an already active claim or exceed the capacity of an overlapping value pool.

### 3.4 Dispute

Fields:

- `dispute_id`
- `claim_id`
- `grounds`
- `submitted_at`
- `reviewer`
- `evidence_refs`
- `decision`
- `remedy`
- `appeal_status`

A new dispute must have `appeal_status = OPEN` and must not pre-populate a decision or remedy.

A dispute may be opened against an `APPROVED` or `PAYABLE` claim. The appeal reviewer must differ from both:

- the claimant; and
- the original claim adjudicator.

Opening a dispute changes the current claim state to `DISPUTED` while preserving the original claim and decision records. If a payable obligation exists, its current state also becomes `DISPUTED`.

Resolution requires a new immutable `GovernanceDecision` by the recorded appeal reviewer:

- `CLAIM_APPEAL_UPHOLD` restores the claim's pre-dispute state and restores a disputed obligation to `PAYABLE`;
- `CLAIM_APPEAL_OVERTURN` changes the claim to `REVERSED` and reverses any linked obligation that has not already been paid.

The original decision remains preserved and the remedy is recorded with the new decision.

### 3.5 Obligation

Fields:

- `obligation_id`
- `claim_id`
- `debtor`
- `creditor`
- `amount_due_minor`
- `amount_paid_minor`
- `due_date`
- `payment_evidence`
- `status`

A new obligation may be created only from an `APPROVED` claim and must:

- identify a creditor equal to the claim claimant;
- have `amount_due_minor` equal to the approved claim amount;
- begin with `amount_paid_minor = 0`;
- begin without payment evidence; and
- begin in `PAYABLE` state.

The original obligation record is immutable. Current paid amount, evidence list, and state are reconstructed from payment events.

## 4. State-transition model

The kernel uses the following state vocabulary:

- `PROPOSED`
- `APPROVED`
- `DISPUTED`
- `PAYABLE`
- `PAID`
- `REVERSED`

### 4.1 Attribution

Allowed path:

`PROPOSED -> APPROVED -> REVERSED`

An approved attribution cannot be reversed while an active approved, disputed, payable, or paid claim still depends on it. Dependent claims must first be resolved or reversed.

### 4.2 Claim

Primary paths:

`PROPOSED -> APPROVED`

`APPROVED -> DISPUTED -> APPROVED`

`APPROVED -> DISPUTED -> REVERSED`

`APPROVED -> PAYABLE -> PAID`

`PAYABLE -> DISPUTED -> PAYABLE`

`PAYABLE -> DISPUTED -> REVERSED`

A claim is not silently rewritten when its state changes. State transitions are audit events.

### 4.3 Obligation

Primary paths:

`PAYABLE -> PAID`

`PAYABLE -> DISPUTED -> PAYABLE`

`PAYABLE -> DISPUTED -> REVERSED`

`PAYABLE or PAID -> REVERSED` only through an explicit `OBLIGATION_REVERSAL` decision.

Partial payment leaves the obligation `PAYABLE` and preserves the exact outstanding balance.

## 5. Governing economic invariants

### Rule 1 — No automatic entitlement from verification alone

A verified contribution is an evidentiary fact only. A claim cannot be approved without approved attribution, an approved v0.2 policy version, and independent claim adjudication.

### Rule 2 — No allocation without attribution

`EconomicGovernanceKernel.calculate_allocation(...)` requires:

- `attribution_id`;
- `policy_version`;
- attribution in `APPROVED` state;
- attribution `pool_id` equal to the requested pool;
- matching accounting period; and
- policy contribution scope contained by the attribution scope.

Missing or unrelated attribution causes rejection.

### Rule 3 — No unilateral retroactive rule changes

Policy versions are append-only.

- first governance version must be version `1` and use a `POLICY_APPROVAL` decision;
- later versions must increment exactly by one and use `POLICY_CORRECTION`;
- an already approved `(policy_id, version)` cannot be replaced;
- historical allocations retain snapshots and their original policy version;
- existing claims retain their original policy version.

### Rule 4 — No self-adjudication

The kernel rejects claim approval when `decision.decided_by == claim.claimant_id`.

Attribution approval similarly rejects a reviewer who is one of the attributed contributors. Appeal reviewers must be independent of the claimant and original claim adjudicator.

These are software checks over recorded identifiers. They are not production identity authentication.

### Rule 5 — No double counting

The kernel prevents:

1. a second active claim for the same claimant, attribution, policy ID, and policy version; and
2. approved claim amounts from exceeding the capacity of a value pool or another pool with the same accounting identity.

The accounting identity is:

`(period, currency, evidence_reference)`

Pools sharing that identity must also agree on distributable amount; otherwise approval is rejected as inconsistent overlapping accounting.

This v0.2 implementation chooses prevention rather than an automatic reconciliation adjustment. Reconciliation requires an explicit later design.

### Rule 6 — No silent nonpayment

An approved claim becomes `PAYABLE` only when an obligation is created. Partial payments remain visible. An unpaid balance is never removed by recalculating an allocation.

A reported payment without evidence produces a `PAYMENT_REPORTED_UNVERIFIED` audit event and does not increase `amount_paid_minor` or transition the obligation to `PAID`.

### Rule 7 — No invisible governance

Accepted governance actions are append-only audit events. Rejected governance actions produce `GOVERNANCE_ACTION_REJECTED` events when a governance method rejects the action with a validation error.

Approvals, policy revisions, appeals, payments, unverified payment reports, reversals, and governed allocations are all separately traceable.

### Rule 8 — No false claims of independence

Attribution evidence must explicitly classify each evidence reference as:

- `OPERATOR_SUPPLIED`; or
- `INDEPENDENT_REVIEWED`.

The kernel does not infer independence from the existence of an evidence reference or reviewer label. These local labels are still not authenticated identities.

## 6. Governed allocation calculation

The v0.2 governed calculation retains the prototype's arithmetic:

`distributable = max(0, gross_value_minor - attributable_costs_minor)`

Allocation remains proportional to positive integer policy weights. Integer minor units are assigned using the same deterministic largest-remainder rule used by the prototype.

The governance layer adds required evidence around the arithmetic. The calculation records:

- pool ID and pool snapshot;
- attribution ID and attribution snapshot;
- policy ID, explicit policy version, and policy snapshot;
- hashes of the three snapshots;
- governance decision references;
- currency, gross value, costs, distributable value, weights, and allocations;
- explicit limitations.

Its status remains `CALCULATED_NOT_PAID`.

Repeated calculation of the exact same governed inputs returns the same deterministic allocation identity. Historical allocations can be reproduced from their stored snapshots even after a later policy version is approved.

## 7. Claim amount rule

For v0.2, an approved claim amount must equal the deterministic allocation attributable to contributions owned by that claimant under the claim's exact attribution and policy version.

This is a deliberately narrow prototype rule. It does not establish that weighted allocation is economically fair, legally binding, or the right production methodology. Alternative bases such as labor, marginal value, negotiated shares, collective ownership, or other methods remain governance questions.

## 8. Dispute and remedy rule

A dispute is not a destructive edit. Opening or resolving a dispute adds events.

An overturn therefore produces:

- the preserved original claim decision;
- a new appeal decision;
- an explicit remedy;
- a visible `REVERSED` current state.

An uphold likewise records a new appeal decision and restores the pre-dispute current state.

## 9. Payment verification and balances

A payment changes a balance only when:

- the obligation is currently `PAYABLE`;
- the payment amount is a positive integer minor-unit amount;
- the payment does not exceed the amount due; and
- a nonempty supporting evidence reference is supplied.

`obligation_balance(...)` reports:

- amount due;
- amount paid;
- outstanding amount;
- current status; and
- accumulated verified payment-evidence references.

## 10. Audit replay, integrity, and checkpoints

The prototype hash chain remains the local append-only log mechanism.

The governance kernel adds an independently retainable checkpoint containing:

- event sequence number;
- audit head hash; and
- SHA-256 of the full audit text.

`verify_checkpoint(...)` compares the current ledger against that retained checkpoint. This detects valid-looking truncation or coordinated local hash-chain rewriting when the retained checkpoint itself was not also altered.

This is not a signature system and does not protect against an attacker who can rewrite both the ledger and the independently retained checkpoint. Production deployment requires independently controlled or signed retention.

## 11. Replay and restart

On restart, the kernel replays both prototype events and v0.2 events to reconstruct:

- contributions;
- value pools;
- historical prototype policies;
- governed policy versions;
- attributions and current states;
- governance decisions;
- claims and current states;
- disputes and resolutions;
- obligations, paid amounts, outstanding balances, and payment evidence; and
- governed allocation snapshots.

No replay step rewrites historical events.

## 12. Concurrency and write-failure semantics

v0.2 uses a re-entrant in-process lock around governance mutations so competing threads cannot simultaneously approve the same duplicate economic claim.

This is not a multi-process or distributed lock. Production concurrency requires an external transactional store or equivalent coordination mechanism.

The inherited append operation publishes in-memory state only after a successful append and `fsync`. A write failure that occurs before the append completes propagates to the caller and does not replay the attempted governance record into memory. A partial operating-system write remains a storage-layer risk that must be handled by a production transactional journal.

## 13. Release gates

### Engineering integrity

Required evidence includes schema validation, deterministic calculations, replay, immutable historical decisions, independently retained checkpoint comparison, and the adversarial suite.

### Attribution integrity

Unsupported or internally inconsistent contribution-to-pool links must be rejected. Uncertainty belongs in `limitations`; the kernel must not manufacture precision.

### Governance integrity

Policy versioning, decision authority, conflicts, self-adjudication prevention, dispute review, appeals, payments, and reversals must be represented by enforceable software transitions over the recorded identifiers.

### Economic and legal validity

This gate **cannot be established by software tests alone**. The allocation method, measurement method, causal attribution, identity/authentication model, institutional authority, agreements, and legal enforceability all require external review and evidence.

## 14. Separation from Evidence Sufficiency

Evidence Sufficiency results are a separate RRE workstream. No result from that track is evidence that this economic model is fair, causally valid, economically correct, or legally enforceable.

## 15. Test authority for this release candidate

`test_economic_governance.py` is intended to cover every adversarial case named in the Milestone 2 proposal, plus concurrency, malformed records, duplicate submissions, and write failures.

The unchanged `test_contribution_bridge.py` remains the authority for the prototype's original 10 behaviors.

Execution and verification are performed by the record keeper, not asserted by this specification.
