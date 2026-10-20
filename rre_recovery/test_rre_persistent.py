import json, tempfile, unittest
from pathlib import Path
from rre_persistent import PersistentRRE, evaluate, verify_chain

class TestPersistentRRE(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.state=self.root/'state.json'; self.audit=self.root/'audit.jsonl'
    def test_initialization_does_not_truncate_existing_audit_history(self):
        r=PersistentRRE(self.state,self.audit); r.act(True)
        before=self.audit.read_bytes(); PersistentRRE(self.state,self.audit)
        after=self.audit.read_bytes()
        self.assertTrue(after.startswith(before)); self.assertGreater(len(after.splitlines()),len(before.splitlines()))
        self.assertTrue(verify_chain(self.audit)[0])
    def test_restart_restores_rules_and_version_identity(self):
        r=PersistentRRE(self.state,self.audit); r.commit_candidate({'missing_evidence':'report_unknown'},'good-fix')
        expected=r.snapshot(); restarted=PersistentRRE(self.state,self.audit)
        self.assertEqual(restarted.snapshot(),expected)
    def test_audit_chain_continues_verifiably_across_restart_boundary(self):
        PersistentRRE(self.state,self.audit).act(True); PersistentRRE(self.state,self.audit).act(False)
        ok,msg=verify_chain(self.audit); self.assertTrue(ok,msg)
        stages=[json.loads(x)['stage'] for x in self.audit.read_text().splitlines()]
        self.assertIn('RESTART_RESTORED',stages)
    def test_faulty_candidate_fails_heldout_verification(self):
        r=PersistentRRE(self.state,self.audit); r.commit_candidate({'missing_evidence':'report_unknown'},'good-fix')
        self.assertFalse(r.commit_candidate({'missing_evidence':'always_refuse'},'faulty'))
    def test_failed_candidate_is_not_retained_as_working_version(self):
        r=PersistentRRE(self.state,self.audit); r.commit_candidate({'missing_evidence':'report_unknown'},'good-fix'); before=r.snapshot()
        self.assertFalse(r.commit_candidate({'missing_evidence':'always_refuse'},'faulty'))
        self.assertEqual(r.snapshot(),before)
    def test_acknowledgment_acceptance_or_relabeling_cannot_override_failed_verification(self):
        r=PersistentRRE(self.state,self.audit); r.commit_candidate({'missing_evidence':'report_unknown'},'good-fix'); before=r.snapshot()
        self.assertFalse(r.commit_candidate({'missing_evidence':'always_refuse'},'good-fix',acknowledged=True,accepted=True))
        self.assertEqual(r.snapshot(),before)
    def test_rollback_preserves_prior_rules_version_and_evaluator_score(self):
        r=PersistentRRE(self.state,self.audit); r.commit_candidate({'missing_evidence':'report_unknown'},'good-fix')
        before=r.snapshot(); score_before=evaluate(r)['passed']
        self.assertFalse(r.commit_candidate({'missing_evidence':'always_refuse'},'bad-revision'))
        restarted=PersistentRRE(self.state,self.audit); score_after=evaluate(restarted)['passed']
        self.assertEqual(restarted.snapshot(),before); self.assertEqual(score_after,score_before); self.assertEqual(score_after,8)
        self.assertTrue(verify_chain(self.audit)[0])

if __name__=='__main__': unittest.main(verbosity=2)

class TestAdversarialIsolation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name); self.r=PersistentRRE(root/'state.json',root/'audit.jsonl')
        self.r.commit_candidate({'missing_evidence':'report_unknown'},'baseline')

    def assert_rejected_candidate_preserves_live_behavior(self, candidate):
        before=self.r.snapshot()
        behavior_before=(self.r.act(True),self.r.act(False))
        durable_before=(self.r.state_path.read_bytes(),)
        self.assertFalse(self.r.commit_candidate(candidate,'adversarial'))
        self.assertEqual(self.r.snapshot(),before)
        self.assertEqual((self.r.act(True),self.r.act(False)),behavior_before)
        self.assertEqual(self.r.state_path.read_bytes(),durable_before[0])

    def test_rejected_empty_candidate_preserves_snapshot_and_behavior_without_restart(self):
        self.assert_rejected_candidate_preserves_live_behavior({})

    def test_rejected_always_refuse_candidate_preserves_snapshot_and_behavior_without_restart(self):
        self.assert_rejected_candidate_preserves_live_behavior({'missing_evidence':'always_refuse'})

    def test_rejected_revert_to_guess_candidate_preserves_snapshot_and_behavior_without_restart(self):
        self.assert_rejected_candidate_preserves_live_behavior({'missing_evidence':'guess'})

    def test_captured_snapshot_is_deeply_frozen_against_later_live_changes(self):
        captured=self.r.snapshot(); frozen=json.dumps(captured,sort_keys=True)
        self.r.commit_candidate({'missing_evidence':'report_unknown'},'another-valid-commit')
        self.r.rules['extra']={'nested':['later mutation']}
        self.assertEqual(json.dumps(captured,sort_keys=True),frozen)
        self.assertNotIn('extra',captured['rules'])
