# RRE Economic Governance Kernel v0.2 — Build Manifest

**Milestone:** RRE Economic Governance — Milestone 2  
**Target:** Economic Governance Kernel v0.2  
**Builder status:** authored return candidate; **not executed, not compiled, not verified by the builder**  
**Execution authority:** record keeper (Muse), per the supplied build packet

## 1. Baseline identifiers supplied by the packet

These values are copied from the corrected packet and are not reconstructed from memory:

- `contribution_bridge.py` prototype source SHA-256: `35bc3e672a76d00378690daa0bda97caac49434d296dda36e8b4e041a170868c`
- `evidence_judge.py` released judge source, revision `stage2-ext-2026-10-23-r3-rule-a-b`, SHA-256: `fc3b0970e11014935605be972a6c4feb393d6111a05ddb6aa77a3b340fc767b9`

The Evidence Sufficiency track remains separate and supplies no evidence that the economic-governance model works.

## 2. Returned files and SHA-256

Exact hashes over the finalized returned bytes:

| File | SHA-256 |
| --- | --- |
| `economic_governance.py` | `f600de88f145983bd92d9a6a6a717431ea1bd5caffb1e9d77ba9f05f3497492a` |
| `test_economic_governance.py` | `77f4e5b5d61a69f9bc2c56141dc5a1a77cdf1fdf15159fccf5b5a84adbcd2c72` |
| `ECONOMIC_GOVERNANCE_SPEC.md` | `eb3caefaf7c45fc7d424679daa4856ea01d97cd5e05484c6d9c1e577820c0c58` |
| `GOVERNANCE_DECISIONS.md` | `395087baaf855237d4f4efc08ded28aab174732e5e5ee1aeb3ff079b78d4366b` |
| `BUILD_MANIFEST.md` | **Exact finalized hash is supplied outside this file in the enclosing return/package metadata.** Embedding the file's own exact SHA-256 would change the bytes being hashed. |

No sixth checksum artifact is added because the order requires exactly five deliverables.

## 3. Files required beside this return for execution

The record keeper should place the returned files beside the unchanged baseline files:

- `contribution_bridge.py`
- `test_contribution_bridge.py`

The builder has not modified either baseline file.

## 4. Exact commands for the record keeper

Run from the directory containing the baseline files and the five returned files.

### Syntax/import check

```bash
python -m py_compile contribution_bridge.py economic_governance.py test_contribution_bridge.py test_economic_governance.py
```

### Prototype regression suite

```bash
python -m unittest -v test_contribution_bridge.py
```

### Milestone 2 governance suite

```bash
python -m unittest -v test_economic_governance.py
```

### Combined suite

```bash
python -m unittest -v test_contribution_bridge.py test_economic_governance.py
```

## 5. Expected results — not observed results

Everything in this section is an **EXPECTATION** for the record keeper to verify. The builder did not execute these commands.

### 5.1 Prototype regression suite

**EXPECTED:** the unchanged prototype suite contains 10 tests and all 10 pass, preserving the baseline behavior described in the packet.

Expected prototype test names:

1. `test_verified_change`
2. `test_acknowledgment_is_not_change`
3. `test_baseline_already_passed_is_rejected`
4. `test_self_review_rejected`
5. `test_unverified_contribution_cannot_be_weighted`
6. `test_policy_required_before_allocation`
7. `test_allocation_conserves_minor_units`
8. `test_equal_weights_split_deterministically`
9. `test_restart_and_tamper_detection`
10. `test_ids_immutable`

### 5.2 Governance suite

**EXPECTED:** 21 governance tests are discovered and all 21 pass.

#### Section 6 adversarial cases — each has its own named test

1. `test_verified_contribution_has_no_attribution_record_allocation_rejected`  
   **EXPECTED:** governed allocation is rejected when no attribution record is supplied.

2. `test_attribution_references_unrelated_value_pool_allocation_rejected`  
   **EXPECTED:** an approved attribution for one pool cannot authorize allocation from a different pool.

3. `test_claim_references_unapproved_policy_version_cannot_be_approved`  
   **EXPECTED:** claim stays `PROPOSED`; approval is rejected.

4. `test_reviewer_attempts_to_approve_own_claim_rejected`  
   **EXPECTED:** self-adjudication is rejected in code.

5. `test_two_claims_consume_same_value_twice_duplicate_allocation_prevented`  
   **EXPECTED:** second economically duplicate claim is rejected.

6. `test_operator_attempts_to_replace_approved_policy_retroactively_rejected`  
   **EXPECTED:** replacement of an already approved policy version is rejected.

7. `test_claim_disputed_after_initial_approval_enters_disputed_history_intact`  
   **EXPECTED:** current state becomes `DISPUTED`; original decision remains stored.

8. `test_independent_reviewer_overturns_decision_new_decision_and_remedy_recorded_old_preserved`  
   **EXPECTED:** claim becomes `REVERSED`; old and new decisions plus remedy remain recorded.

9. `test_approved_obligation_partial_payment_outstanding_balance_accurate`  
   **EXPECTED:** partial payment leaves `PAYABLE` with exact remaining balance.

10. `test_payment_reported_without_supporting_evidence_remains_unverified`  
    **EXPECTED:** reported payment is audited but paid amount stays unchanged.

11. `test_audit_file_modified_or_truncated_integrity_failure_against_checkpoint`  
    **EXPECTED:** both valid-looking truncation and a locally rehashed coordinated rewrite fail against the independently retained checkpoint.

12. `test_ledger_restart_reload_reproduces_claims_decisions_disputes_and_balances`  
    **EXPECTED:** restart reproduces claim, decision, dispute, payable state, paid amount, and outstanding balance.

13. `test_allocation_recalculated_under_different_policy_historical_original_reproducible`  
    **EXPECTED:** policy v2 produces a different allocation while v1 remains reproducible from its recorded snapshot.

14. `test_currency_or_accounting_period_inconsistent_cross_pool_calculation_rejected`  
    **EXPECTED:** period mismatch and claim/pool currency mismatch are rejected.

15. `test_contribution_passes_behavioral_tests_but_value_attribution_fails_claim_not_approved`  
    **EXPECTED:** contribution remains verified; unsupported attribution cannot be approved; economic claim cannot proceed.

#### Additional proposal-required adversarial coverage

16. `test_concurrency_serializes_duplicate_claim_approval`  
    **EXPECTED:** exactly one concurrent duplicate claim approval succeeds and the other is rejected.

17. `test_malformed_record_rejected`  
    **EXPECTED:** malformed attribution structure is rejected.

18. `test_duplicate_submission_rejected`  
    **EXPECTED:** duplicate immutable record ID is rejected.

19. `test_failure_during_write_does_not_publish_in_memory_governance_record`  
    **EXPECTED:** simulated append failure propagates and does not publish the attempted record in replayed memory.

20. `test_evidence_source_classification_distinguishes_operator_and_independent_records`  
    **EXPECTED:** explicit operator-vs-independent evidence classification is retained.

21. `test_full_payment_transitions_payable_to_paid`  
    **EXPECTED:** fully evidenced payment transitions obligation and claim to `PAID` with zero outstanding balance.

## 6. Expected combined result

**EXPECTED, not observed:**

- 10 prototype tests pass.
- 21 governance tests pass.
- 31 total tests pass when both modules are run together.
- `py_compile` exits successfully with no syntax/import errors.

These statements are expectations only. They become results only after the record keeper performs the commands and records the actual output.

## 7. Release-gate status at return

No release gate is claimed passed by this builder return.

- **Engineering integrity:** pending record-keeper execution and adversarial verification.
- **Attribution integrity:** implemented as code/spec invariants; pending execution and review.
- **Governance integrity:** implemented as code/spec invariants; pending execution and institutional review.
- **Economic and legal validity:** not established by software tests and not claimed.

## 8. Legal/economic boundary

The returned code and documents create governance records only. They do not create or prove legal entitlement, economic causation, wage status, royalty status, ownership, or enforceable payment rights.
