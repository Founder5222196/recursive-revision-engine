import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from contribution_bridge import AllocationPolicy, Contribution, ValuePool, example_contribution, sha, canonical
from economic_governance import (
    APPROVED,
    DISPUTED,
    PAID,
    PAYABLE,
    PROPOSED,
    REVERSED,
    AttributionRecord,
    Claim,
    Dispute,
    EconomicGovernanceKernel,
    GovernanceDecision,
    Obligation,
)


class EconomicGovernanceTests(unittest.TestCase):
    """Milestone 2 adversarial suite.

    Each Section 6 adversarial case is a separately named test below. Additional
    tests cover concurrency, malformed records, duplicate submissions, and write
    failures as required by the proposal.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "audit.jsonl"
        self.k = EconomicGovernanceKernel(self.path)

        c1 = example_contribution()
        self.assertEqual(self.k.verify_contribution(c1)["status"], "VERIFIED")
        c2 = Contribution(
            **{
                **c1.__dict__,
                "contribution_id": "contrib-002",
                "contributor_id": "contributor-alias-8",
                "artifact_sha256": sha("candidate-2"),
                "reviewer_id": "independent-reviewer-alias-9",
            }
        )
        self.assertEqual(self.k.verify_contribution(c2)["status"], "VERIFIED")

        self.k.register_value_pool(
            ValuePool(
                "pool-main",
                "2026-Q3",
                "USD",
                10000,
                0,
                "Illustrative governed value",
                "evidence://pool-main",
                "value-reviewer-1",
            )
        )
        self._approve_attribution()
        self._approve_policy_v1()

    # ---------- fixture builders ----------

    def _decision(self, decision_id, subject_id, decision_type, decided_by, policy_version=None):
        return GovernanceDecision(
            decision_id=decision_id,
            subject_id=subject_id,
            decision_type=decision_type,
            policy_version=policy_version,
            eligible_participants=(decided_by,),
            approval_evidence=f"evidence://decision/{decision_id}",
            conflicts=(),
            reasoning="Test fixture decision with explicit authority and rationale.",
            effective_at="2026-08-31T12:00:00Z",
            decided_by=decided_by,
        )

    def _attribution(self, attribution_id="attr-main", pool_id="pool-main", period="2026-Q3", evidence_ref="evidence://pool-main"):
        return AttributionRecord(
            attribution_id=attribution_id,
            contribution_ids=("contrib-001", "contrib-002"),
            pool_id=pool_id,
            system_id="system-rre-demo",
            period=period,
            method_version="attrib-v1",
            evidence_refs=(evidence_ref,),
            evidence_sources=((evidence_ref, "INDEPENDENT_REVIEWED"),),
            reviewer="attribution-reviewer-1",
            status=PROPOSED,
            limitations=("Illustrative attribution for tests.",),
        )

    def _approve_attribution(self):
        self.k.propose_attribution(self._attribution())
        self.k.approve_attribution(
            "attr-main",
            self._decision("decision-attr-1", "attr-main", "ATTRIBUTION_APPROVAL", "attribution-reviewer-1"),
        )

    def _approve_policy_v1(self):
        policy = AllocationPolicy(
            "policy-main",
            1,
            "Equal governed shares",
            {"contrib-001": 1, "contrib-002": 1},
            "governance-reviewer-1",
            "evidence://policy/1",
            "Independent appeal reviewer required",
        )
        self.k.approve_policy_version(
            policy,
            self._decision("decision-policy-1", "policy-main", "POLICY_APPROVAL", "governance-reviewer-1", 1),
        )
        return policy

    def _propose_claim(self, claim_id="claim-1", claimant="contributor-alias-7", policy_version=1, amount=5000, currency="USD"):
        claim = Claim(
            claim_id=claim_id,
            claimant_id=claimant,
            attribution_id="attr-main",
            policy_id="policy-main",
            policy_version=policy_version,
            amount_minor=amount,
            currency=currency,
            status=PROPOSED,
        )
        self.k.propose_claim(claim)
        return claim

    def _approve_claim(self, claim_id="claim-1", reviewer="claims-reviewer-1", decision_id="decision-claim-1"):
        claim = self.k.claims[claim_id]
        return self.k.approve_claim(
            claim_id,
            self._decision(decision_id, claim_id, "CLAIM_APPROVAL", reviewer, claim["policy_version"]),
        )

    def _approved_claim(self, claim_id="claim-1"):
        self._propose_claim(claim_id=claim_id)
        self._approve_claim(claim_id=claim_id, decision_id=f"decision-{claim_id}")
        return self.k.claims[claim_id]

    def _obligation(self, claim_id="claim-1", obligation_id="obligation-1"):
        return Obligation(
            obligation_id=obligation_id,
            claim_id=claim_id,
            debtor="operator-1",
            creditor=self.k.claims[claim_id]["claimant_id"],
            amount_due_minor=self.k.claims[claim_id]["amount_minor"],
            amount_paid_minor=0,
            due_date="2026-09-30",
            payment_evidence=(),
            status=PAYABLE,
        )

    # ---------- Section 6 adversarial cases ----------

    def test_verified_contribution_has_no_attribution_record_allocation_rejected(self):
        with self.assertRaisesRegex(ValueError, "attribution record required"):
            self.k.calculate_allocation("pool-main", "policy-main", attribution_id=None, policy_version=1)

    def test_attribution_references_unrelated_value_pool_allocation_rejected(self):
        self.k.register_value_pool(
            ValuePool(
                "pool-other",
                "2026-Q3",
                "USD",
                10000,
                0,
                "Other value",
                "evidence://pool-other",
                "value-reviewer-2",
            )
        )
        with self.assertRaisesRegex(ValueError, "unrelated value pool"):
            self.k.calculate_allocation("pool-other", "policy-main", attribution_id="attr-main", policy_version=1)

    def test_claim_references_unapproved_policy_version_cannot_be_approved(self):
        self._propose_claim(policy_version=2)
        with self.assertRaisesRegex(ValueError, "unapproved policy version"):
            self.k.approve_claim(
                "claim-1",
                self._decision("decision-claim-v2", "claim-1", "CLAIM_APPROVAL", "claims-reviewer-1", 2),
            )
        self.assertEqual(self.k.claim_states["claim-1"], PROPOSED)

    def test_reviewer_attempts_to_approve_own_claim_rejected(self):
        self._propose_claim()
        with self.assertRaisesRegex(ValueError, "self-adjudication"):
            self.k.approve_claim(
                "claim-1",
                self._decision(
                    "decision-self",
                    "claim-1",
                    "CLAIM_APPROVAL",
                    "contributor-alias-7",
                    1,
                ),
            )
        self.assertEqual(self.k.claim_states["claim-1"], PROPOSED)

    def test_two_claims_consume_same_value_twice_duplicate_allocation_prevented(self):
        self._approved_claim("claim-1")
        self._propose_claim(claim_id="claim-duplicate")
        with self.assertRaisesRegex(ValueError, "duplicate claim"):
            self._approve_claim(
                claim_id="claim-duplicate",
                reviewer="claims-reviewer-2",
                decision_id="decision-claim-duplicate",
            )
        self.assertEqual(self.k.claim_states["claim-duplicate"], PROPOSED)

    def test_operator_attempts_to_replace_approved_policy_retroactively_rejected(self):
        replacement = AllocationPolicy(
            "policy-main",
            1,
            "Retroactive rewrite",
            {"contrib-001": 2, "contrib-002": 1},
            "governance-reviewer-1",
            "evidence://policy/rewrite",
            "appeal",
        )
        with self.assertRaisesRegex(ValueError, "retroactive policy replacement"):
            self.k.approve_policy_version(
                replacement,
                self._decision(
                    "decision-policy-rewrite",
                    "policy-main",
                    "POLICY_CORRECTION",
                    "governance-reviewer-1",
                    1,
                ),
            )

    def test_claim_disputed_after_initial_approval_enters_disputed_history_intact(self):
        self._approved_claim("claim-1")
        old_decision_id = self.k.claim_decisions["claim-1"]
        dispute = Dispute(
            "dispute-1",
            "claim-1",
            "Attribution scope challenged",
            "2026-08-31T13:00:00Z",
            "appeal-reviewer-1",
            ("evidence://appeal/1",),
            "",
            "",
            "OPEN",
        )
        result = self.k.open_dispute(dispute)
        self.assertEqual(result["status"], DISPUTED)
        self.assertEqual(self.k.claim_states["claim-1"], DISPUTED)
        self.assertIn(old_decision_id, self.k.decisions)
        self.assertIn("dispute-1", self.k.disputes)

    def test_independent_reviewer_overturns_decision_new_decision_and_remedy_recorded_old_preserved(self):
        self._approved_claim("claim-1")
        old_decision_id = self.k.claim_decisions["claim-1"]
        self.k.open_dispute(
            Dispute(
                "dispute-1",
                "claim-1",
                "Material attribution challenge",
                "2026-08-31T13:00:00Z",
                "appeal-reviewer-1",
                (),
                "",
                "",
                "OPEN",
            )
        )
        result = self.k.resolve_dispute(
            "dispute-1",
            self._decision(
                "decision-appeal-overturn",
                "claim-1",
                "CLAIM_APPEAL_OVERTURN",
                "appeal-reviewer-1",
                1,
            ),
            "Reverse claim; preserve original decision and record correction.",
        )
        self.assertEqual(result["status"], REVERSED)
        self.assertEqual(result["old_decision_id"], old_decision_id)
        self.assertIn(old_decision_id, self.k.decisions)
        self.assertIn("decision-appeal-overturn", self.k.decisions)
        self.assertEqual(self.k.dispute_resolutions["dispute-1"]["remedy"], result["remedy"])

    def test_approved_obligation_partial_payment_outstanding_balance_accurate(self):
        self._approved_claim("claim-1")
        self.k.create_obligation(self._obligation())
        result = self.k.record_payment("obligation-1", 2000, "evidence://payment/partial")
        self.assertEqual(result["status"], PAYABLE)
        self.assertEqual(result["amount_paid_minor"], 2000)
        self.assertEqual(result["outstanding_minor"], 3000)
        self.assertEqual(self.k.obligation_balance("obligation-1")["outstanding_minor"], 3000)

    def test_payment_reported_without_supporting_evidence_remains_unverified(self):
        self._approved_claim("claim-1")
        self.k.create_obligation(self._obligation())
        result = self.k.record_payment("obligation-1", 2000, "")
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertEqual(result["amount_paid_minor"], 0)
        self.assertEqual(self.k.obligation_balance("obligation-1")["status"], PAYABLE)
        self.assertEqual(self.k.obligation_balance("obligation-1")["outstanding_minor"], 5000)

    def test_audit_file_modified_or_truncated_integrity_failure_against_checkpoint(self):
        checkpoint = Path(self.tmp.name) / "checkpoint.json"
        self.k.write_checkpoint(checkpoint)
        original = self.path.read_text(encoding="utf-8")

        with self.subTest("truncated"):
            lines = original.splitlines()
            self.path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checkpoint"):
                EconomicGovernanceKernel(self.path, checkpoint)

        self.path.write_text(original, encoding="utf-8")
        with self.subTest("coordinated-rewrite-with-valid-local-chain"):
            events = [json.loads(line) for line in original.splitlines()]
            events[0]["payload"]["status"] = "ALTERED"
            previous = "GENESIS"
            rewritten = []
            for sequence, event in enumerate(events, 1):
                body = {k: v for k, v in event.items() if k != "hash"}
                body["sequence"] = sequence
                body["previous_hash"] = previous
                event = {**body, "hash": sha(body)}
                rewritten.append(canonical(event))
                previous = event["hash"]
            self.path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
            # Local chain is internally valid after coordinated rewriting, but the
            # independently retained checkpoint must still reject it.
            with self.assertRaisesRegex(ValueError, "checkpoint"):
                EconomicGovernanceKernel(self.path, checkpoint)

    def test_ledger_restart_reload_reproduces_claims_decisions_disputes_and_balances(self):
        self._approved_claim("claim-1")
        self.k.create_obligation(self._obligation())
        self.k.record_payment("obligation-1", 2000, "evidence://payment/1")
        self.k.open_dispute(
            Dispute(
                "dispute-1",
                "claim-1",
                "Review calculation",
                "2026-08-31T13:00:00Z",
                "appeal-reviewer-1",
                (),
                "",
                "",
                "OPEN",
            )
        )
        self.k.resolve_dispute(
            "dispute-1",
            self._decision(
                "decision-appeal-uphold",
                "claim-1",
                "CLAIM_APPEAL_UPHOLD",
                "appeal-reviewer-1",
                1,
            ),
            "Uphold claim and restore payable state.",
        )

        reloaded = EconomicGovernanceKernel(self.path)
        self.assertIn("claim-1", reloaded.claims)
        self.assertIn("decision-claim-1", reloaded.decisions)
        self.assertIn("decision-appeal-uphold", reloaded.decisions)
        self.assertIn("dispute-1", reloaded.disputes)
        self.assertEqual(reloaded.claim_states["claim-1"], PAYABLE)
        self.assertEqual(reloaded.obligation_balance("obligation-1")["amount_paid_minor"], 2000)
        self.assertEqual(reloaded.obligation_balance("obligation-1")["outstanding_minor"], 3000)

    def test_allocation_recalculated_under_different_policy_historical_original_reproducible(self):
        first = self.k.calculate_allocation(
            "pool-main",
            "policy-main",
            attribution_id="attr-main",
            policy_version=1,
        )
        policy_v2 = AllocationPolicy(
            "policy-main",
            2,
            "Two-to-one governed shares",
            {"contrib-001": 2, "contrib-002": 1},
            "governance-reviewer-1",
            "evidence://policy/2",
            "Independent appeal reviewer required",
        )
        self.k.approve_policy_version(
            policy_v2,
            self._decision(
                "decision-policy-2",
                "policy-main",
                "POLICY_CORRECTION",
                "governance-reviewer-1",
                2,
            ),
        )
        second = self.k.calculate_allocation(
            "pool-main",
            "policy-main",
            attribution_id="attr-main",
            policy_version=2,
        )
        replay = self.k.reproduce_allocation(first["allocation_id"])
        self.assertTrue(replay["matches_recorded"])
        self.assertEqual(replay["allocations_minor"], first["allocations_minor"])
        self.assertNotEqual(first["allocations_minor"], second["allocations_minor"])
        self.assertEqual(first["policy_version"], 1)
        self.assertEqual(second["policy_version"], 2)

    def test_currency_or_accounting_period_inconsistent_cross_pool_calculation_rejected(self):
        bad_attr = self._attribution(
            attribution_id="attr-wrong-period",
            period="2026-Q4",
        )
        self.k.propose_attribution(bad_attr)
        with self.assertRaisesRegex(ValueError, "accounting period"):
            self.k.approve_attribution(
                "attr-wrong-period",
                self._decision(
                    "decision-wrong-period",
                    "attr-wrong-period",
                    "ATTRIBUTION_APPROVAL",
                    "attribution-reviewer-1",
                ),
            )

        self._propose_claim(claim_id="claim-eur", currency="EUR")
        with self.assertRaisesRegex(ValueError, "currency"):
            self._approve_claim(
                claim_id="claim-eur",
                reviewer="claims-reviewer-2",
                decision_id="decision-claim-eur",
            )

    def test_contribution_passes_behavioral_tests_but_value_attribution_fails_claim_not_approved(self):
        bad = self._attribution(
            attribution_id="attr-unsupported",
            evidence_ref="evidence://not-the-pool",
        )
        self.k.propose_attribution(bad)
        with self.assertRaisesRegex(ValueError, "supported link"):
            self.k.approve_attribution(
                "attr-unsupported",
                self._decision(
                    "decision-attr-unsupported",
                    "attr-unsupported",
                    "ATTRIBUTION_APPROVAL",
                    "attribution-reviewer-1",
                ),
            )
        self.assertEqual(self.k.attribution_states["attr-unsupported"], PROPOSED)
        with self.assertRaisesRegex(ValueError, "approved attribution"):
            self.k.propose_claim(
                Claim(
                    "claim-unsupported",
                    "contributor-alias-7",
                    "attr-unsupported",
                    "policy-main",
                    1,
                    5000,
                    "USD",
                    PROPOSED,
                )
            )

    # ---------- additional required adversarial coverage ----------

    def test_concurrency_serializes_duplicate_claim_approval(self):
        self._propose_claim("claim-a")
        self._propose_claim("claim-b")

        def approve(claim_id, reviewer, decision_id):
            try:
                return self._approve_claim(claim_id, reviewer, decision_id)["status"]
            except ValueError as exc:
                return f"ERROR:{exc}"

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(
                executor.map(
                    lambda args: approve(*args),
                    [
                        ("claim-a", "claims-reviewer-a", "decision-claim-a"),
                        ("claim-b", "claims-reviewer-b", "decision-claim-b"),
                    ],
                )
            )
        self.assertEqual(sum(outcome == APPROVED for outcome in outcomes), 1)
        self.assertEqual(sum(outcome.startswith("ERROR:duplicate claim") for outcome in outcomes), 1)

    def test_malformed_record_rejected(self):
        malformed = AttributionRecord(
            attribution_id="attr-malformed",
            contribution_ids=("contrib-001", 7),  # type: ignore[arg-type]
            pool_id="pool-main",
            system_id="system",
            period="2026-Q3",
            method_version="v1",
            evidence_refs=("evidence://pool-main",),
            evidence_sources=(("evidence://pool-main", "INDEPENDENT_REVIEWED"),),
            reviewer="reviewer",
            status=PROPOSED,
        )
        with self.assertRaisesRegex(ValueError, "malformed record"):
            self.k.propose_attribution(malformed)

    def test_duplicate_submission_rejected(self):
        a = self._attribution(attribution_id="attr-dup")
        self.k.propose_attribution(a)
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.k.propose_attribution(a)

    def test_failure_during_write_does_not_publish_in_memory_governance_record(self):
        a = self._attribution(attribution_id="attr-write-fail")
        before_events = len(self.k.events)
        with mock.patch.object(Path, "open", side_effect=OSError("simulated write failure")):
            with self.assertRaisesRegex(OSError, "simulated write failure"):
                self.k.propose_attribution(a)
        self.assertEqual(len(self.k.events), before_events)
        self.assertNotIn("attr-write-fail", self.k.attributions)

    def test_evidence_source_classification_distinguishes_operator_and_independent_records(self):
        ref = "evidence://pool-main"
        a = AttributionRecord(
            attribution_id="attr-source-classified",
            contribution_ids=("contrib-001",),
            pool_id="pool-main",
            system_id="system-rre-demo",
            period="2026-Q3",
            method_version="attrib-v1",
            evidence_refs=(ref,),
            evidence_sources=((ref, "OPERATOR_SUPPLIED"),),
            reviewer="attribution-reviewer-2",
            status=PROPOSED,
            limitations=("Source classification is recorded; identity is not authenticated.",),
        )
        self.k.propose_attribution(a)
        self.assertEqual(
            self.k.attributions["attr-source-classified"]["evidence_sources"],
            ((ref, "OPERATOR_SUPPLIED"),),
        )

    def test_full_payment_transitions_payable_to_paid(self):
        self._approved_claim("claim-1")
        self.k.create_obligation(self._obligation())
        result = self.k.record_payment("obligation-1", 5000, "evidence://payment/full")
        self.assertEqual(result["status"], PAID)
        self.assertEqual(self.k.claim_states["claim-1"], PAID)
        self.assertEqual(result["outstanding_minor"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
