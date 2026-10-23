import tempfile, unittest
from pathlib import Path
from evidence_judge import (SCHEMA_VERSION, Policy, GroundedEvidenceJudge, VersionedPolicyExtension,
    make_record, validate_evidence_record, gate_model_response, validate_response, SufficiencyPolicy, CandidateAssertion, EvidenceRecord)

class EvidenceJudgeTests(unittest.TestCase):
    def setUp(self):
        self.q = "What is the launch date for Orion?"
        self.d = "The Orion launch date is 14 June 2025. The Vega launch date is 19 July 2025."
        self.good = [{"source_span":"The Orion launch date is 14 June 2025.", "entity":"Orion", "attribute":"launch date", "value":"14 June 2025", "scope":{}, "assertion_type":"asserted", "relation":"states launch date"}]
        self.model = lambda q,d: make_record(q,d,self.good)

    def test_valid_exact_span_and_answer(self):
        out, trace = GroundedEvidenceJudge(self.model).judge(self.q,self.d,target_entity="Orion",target_attribute="launch date")
        self.assertEqual(out,"ANSWER: 14 June 2025"); self.assertTrue(trace['validation']['valid'])

    def test_span_not_in_dossier_rejected(self):
        bad = [dict(self.good[0],source_span="Orion launches on 14 June 2025.")]
        out,_ = GroundedEvidenceJudge(lambda q,d:make_record(q,d,bad)).judge(self.q,self.d,target_entity="Orion",target_attribute="launch date")
        self.assertTrue(out.startswith("ABSTAIN: evidence record rejected"))

    def test_wrong_entity_is_filtered(self):
        out,_ = GroundedEvidenceJudge(self.model).judge(self.q,self.d,target_entity="Vega",target_attribute="launch date")
        self.assertTrue(out.startswith("ABSTAIN:"))

    def test_conflicting_same_fact_abstains(self):
        c = self.good + [dict(self.good[0],source_span="The Orion launch date is 14 June 2025.",value="15 June 2025")]
        rec = validate_evidence_record(make_record(self.q,self.d,c),self.q,self.d)
        self.assertTrue(rec.valid)
        dec = SufficiencyPolicy().decide(rec.record,"Orion","launch date")
        self.assertEqual(dec.status,"ABSTAIN"); self.assertIn("contradictory",dec.reason)

    def test_hypothetical_not_asserted_support(self):
        c=[dict(self.good[0],assertion_type="hypothetical")]
        rec=validate_evidence_record(make_record(self.q,self.d,c),self.q,self.d)
        self.assertEqual(SufficiencyPolicy().decide(rec.record,"Orion","launch date").status,"ABSTAIN")

    def test_offsets_must_match_exact_span(self):
        c=[dict(self.good[0],source_start=0,source_end=4)]
        v=validate_evidence_record(make_record(self.q,self.d,c),self.q,self.d)
        self.assertFalse(v.valid); self.assertTrue(any('offsets' in e for e in v.errors))

    def test_dossier_hash_binding(self):
        r=make_record(self.q,self.d,self.good); r['dossier_sha256']='0'*64
        self.assertFalse(validate_evidence_record(r,self.q,self.d).valid)

    def test_response_gate_accepts_exact_forms(self):
        self.assertTrue(validate_response('ANSWER: 14 June 2025'))
        self.assertTrue(validate_response('ABSTAIN: conflicting evidence'))
        self.assertEqual(gate_model_response('ANSWER: x'),'ANSWER: x')

    def test_response_gate_rejects_malformed(self):
        for s in ('answer: x','ANSWER:x','ABSTAIN:','I think x','ANSWER: x\nABSTAIN: no'):
            with self.assertRaises(ValueError): gate_model_response(s)

    def test_policy_extension_no_silent_rule_mutation_and_auth(self):
        with tempfile.TemporaryDirectory() as td:
            from rre_minimal import RRE, verify_audit
            audit=Path(td)/'audit.jsonl'; pp=Path(td)/'policy.json'
            e=RRE(audit); original=dict(e.rules)
            ext=VersionedPolicyExtension(e,pp)
            self.assertEqual(e.rules,original)
            proposal=ext.propose({"version":"sufficiency/1.1","require_asserted":True},"clarify policy schema","test-failure-01")
            self.assertFalse(ext.apply(proposal,None)); self.assertEqual(ext.state['version'],1)
            self.assertTrue(ext.apply(proposal,"Named Reviewer")); self.assertEqual(ext.state['version'],2)
            self.assertTrue(verify_audit(audit)[0])

    def test_policy_state_survives_restart(self):
        with tempfile.TemporaryDirectory() as td:
            from rre_minimal import RRE
            audit=Path(td)/'audit.jsonl'; pp=Path(td)/'policy.json'
            e=RRE(audit); x=VersionedPolicyExtension(e,pp)
            p=x.propose({"version":"sufficiency/1.1"},"rationale","test",{"provider":"injected","model_id":"stub"})
            self.assertTrue(x.apply(p,"Reviewer"))
            e2=RRE(audit); x2=VersionedPolicyExtension(e2,pp)
            self.assertEqual(x2.state['version'],2); self.assertEqual(x2.state['model_config']['model_id'],'stub')

if __name__=='__main__': unittest.main(verbosity=2)
