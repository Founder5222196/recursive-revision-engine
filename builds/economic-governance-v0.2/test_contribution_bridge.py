import tempfile, unittest
from pathlib import Path
from contribution_bridge import *
class BridgeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.path=Path(self.tmp.name)/'audit.jsonl'; self.b=ContributionBridge(self.path)
 def test_verified_change(self): self.assertEqual(self.b.verify_contribution(example_contribution())['status'],'VERIFIED')
 def test_acknowledgment_is_not_change(self):
  c=example_contribution(); c=Contribution(**{**c.__dict__,'tests':(BehavioralTest('ack','ABSTAIN','ANSWER: guess','I understand'),)})
  r=self.b.verify_contribution(c); self.assertEqual(r['status'],'REJECTED'); self.assertTrue(any('does not match expected' in e for e in r['errors']))
 def test_baseline_already_passed_is_rejected(self):
  c=example_contribution(); c=Contribution(**{**c.__dict__,'tests':(BehavioralTest('same','42','42','42'),)})
  self.assertEqual(self.b.verify_contribution(c)['status'],'REJECTED')
 def test_self_review_rejected(self):
  c=example_contribution(); c=Contribution(**{**c.__dict__,'reviewer_id':c.contributor_id}); self.assertEqual(self.b.verify_contribution(c)['status'],'REJECTED')
 def test_unverified_contribution_cannot_be_weighted(self):
  r=self.b.approve_policy(AllocationPolicy('p',1,'points',{'ghost':1},'g','ref','appeal')); self.assertEqual(r['status'],'REJECTED')
 def test_policy_required_before_allocation(self):
  self.b.register_value_pool(ValuePool('pool','period','USD',1,0,'basis','evidence','reviewer'))
  with self.assertRaisesRegex(ValueError,'unapproved'): self.b.calculate_allocation('pool','y')
 def test_allocation_conserves_minor_units(self):
  self.b.verify_contribution(example_contribution()); self.b.register_value_pool(ValuePool('pool','period','USD',10001,2000,'basis','evidence','reviewer'))
  self.b.approve_policy(AllocationPolicy('policy',1,'points',{'contrib-001':2},'authority','approval','appeal'))
  r=self.b.calculate_allocation('pool','policy'); self.assertEqual(r['status'],'CALCULATED_NOT_PAID'); self.assertEqual(sum(r['allocations_minor'].values()),8001)
 def test_equal_weights_split_deterministically(self):
  c=example_contribution(); self.b.verify_contribution(c); c2=Contribution(**{**c.__dict__,'contribution_id':'c2','contributor_id':'other','artifact_sha256':sha('other'),'reviewer_id':'reviewer2'}); self.b.verify_contribution(c2)
  self.b.register_value_pool(ValuePool('pool','period','USD',101,0,'basis','evidence','reviewer')); self.b.approve_policy(AllocationPolicy('policy',1,'points',{'contrib-001':1,'c2':1},'authority','approval','appeal'))
  self.assertEqual(self.b.calculate_allocation('pool','policy')['allocations_minor'],{'contrib-001':50,'c2':51})
 def test_restart_and_tamper_detection(self):
  self.b.verify_contribution(example_contribution()); original=self.path.read_text(); b2=ContributionBridge(self.path); self.assertIn('contrib-001',b2.contributions)
  self.path.write_text(original.replace('VERIFIED','FAKED',1))
  with self.assertRaisesRegex(ValueError,'invalid audit hash'): ContributionBridge(self.path)
 def test_ids_immutable(self):
  c=example_contribution(); self.b.verify_contribution(c)
  with self.assertRaisesRegex(ValueError,'immutable'): self.b.verify_contribution(c)
if __name__=='__main__': unittest.main(verbosity=2)
