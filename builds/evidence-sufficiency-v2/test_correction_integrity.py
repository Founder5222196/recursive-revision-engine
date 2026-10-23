"""Development-only Correction Integrity Gate protocol checks; not independent sign-off."""
import tempfile, unittest
from pathlib import Path
from evidence_judge import VersionedPolicyExtension
from rre_minimal import RRE, verify_audit

class CorrectionIntegrityTests(unittest.TestCase):
    def test_unauthorized_stale_and_authorized_lifecycle(self):
        with tempfile.TemporaryDirectory() as td:
            audit=Path(td)/'audit.jsonl'; policy=Path(td)/'judge.json'
            r=RRE(audit); ext=VersionedPolicyExtension(r,policy)
            baseline={'version':ext.state['version'],'policy':dict(ext.state['policy']),'model_config':dict(ext.state['model_config'])}
            p=ext.propose({'version':'sufficiency/1.1','require_asserted':True},'prevent hypothetical support','dev-case-01')
            self.assertFalse(ext.apply(p,'')); self.assertEqual(ext.state['version'],1)
            self.assertTrue(ext.apply(p,'Development Reviewer')); self.assertEqual(ext.state['version'],2)
            self.assertFalse(ext.apply(p,'Development Reviewer')) # stale proposal
            r2=RRE(audit); ext2=VersionedPolicyExtension(r2,policy)
            self.assertEqual(ext2.state['version'],2)
            self.assertTrue(verify_audit(audit)[0])
            self.assertTrue(ext2.rollback(baseline,'Development Reviewer'))
            r3=RRE(audit); ext3=VersionedPolicyExtension(r3,policy)
            self.assertEqual(ext3.state['version'],1)
            self.assertTrue(verify_audit(audit)[0])

    def test_rollback_requires_named_authority(self):
        with tempfile.TemporaryDirectory() as td:
            r=RRE(Path(td)/'audit.jsonl'); ext=VersionedPolicyExtension(r,Path(td)/'p.json')
            old=dict(ext.state); p=ext.propose({'version':'sufficiency/1.1'},'test','x')
            self.assertTrue(ext.apply(p,'Reviewer'))
            self.assertFalse(ext.rollback(old,'')); self.assertEqual(ext.state['version'],2)

if __name__=='__main__': unittest.main(verbosity=2)
