"""RRE Contribution-to-Value Bridge prototype 0.1; Python 3.10+, stdlib only.
Experimental: records evidence and calculates hypothetical allocations; never pays money.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import hashlib, json, os, time

def canonical(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def sha(x: Any) -> str:
    return hashlib.sha256((x if isinstance(x, str) else canonical(x)).encode()).hexdigest()

@dataclass(frozen=True)
class BehavioralTest:
    case_id: str
    expected: str
    before: str
    after: str
@dataclass(frozen=True)
class Contribution:
    contribution_id: str
    contributor_id: str
    artifact_sha256: str
    description: str
    provenance: str
    baseline_version: str
    candidate_version: str
    tests: tuple[BehavioralTest, ...]
    reviewer_id: str
    verification_note: str
@dataclass(frozen=True)
class ValuePool:
    pool_id: str
    period: str
    currency: str
    gross_value_minor: int
    attributable_costs_minor: int
    measurement_basis: str
    evidence_reference: str
    independently_reviewed_by: str
@dataclass(frozen=True)
class AllocationPolicy:
    policy_id: str
    version: int
    basis: str
    weights: dict[str, int]
    approved_by: str
    approval_reference: str
    dispute_process: str

class ContributionBridge:
    """Append-only local hash-chain ledger; reviewer/contributor IDs are not authenticated."""
    def __init__(self, audit_path: str | Path):
        self.path = Path(audit_path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.events = self._load() if self.path.exists() and self.path.stat().st_size else []
        self.contributions, self.pools, self.policies = {}, {}, {}
        for e in self.events: self._replay(e['event_type'], e['payload'])
    def _load(self):
        out=[]; prev='GENESIS'
        for seq,line in enumerate(self.path.read_text(encoding='utf-8').splitlines(),1):
            e=json.loads(line); body={k:v for k,v in e.items() if k!='hash'}
            if e.get('sequence')!=seq or e.get('previous_hash')!=prev: raise ValueError(f'invalid audit sequence/link at line {seq}')
            if e.get('hash')!=sha(body): raise ValueError(f'invalid audit hash at line {seq}')
            out.append(e); prev=e['hash']
        return out
    def _record(self, typ, payload):
        body={'sequence':len(self.events)+1,'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'event_type':typ,'payload':payload,'previous_hash':self.events[-1]['hash'] if self.events else 'GENESIS'}
        e={**body,'hash':sha(body)}
        with self.path.open('a',encoding='utf-8') as f: f.write(canonical(e)+'\n'); f.flush(); os.fsync(f.fileno())
        self.events.append(e); self._replay(typ,payload); return e
    def _replay(self,typ,p):
        if typ=='CONTRIBUTION_VERIFIED': self.contributions[p['contribution']['contribution_id']]=p
        elif typ=='VALUE_POOL_REGISTERED': self.pools[p['pool']['pool_id']]=p
        elif typ=='ALLOCATION_POLICY_APPROVED': self.policies[p['policy']['policy_id']]=p
    def verify_contribution(self,c: Contribution):
        if c.contribution_id in self.contributions: raise ValueError('contribution_id already exists; records are immutable')
        errors=[]
        for field in ('contribution_id','contributor_id','description','provenance','reviewer_id','verification_note','baseline_version','candidate_version'):
            if not getattr(c,field).strip(): errors.append(f'missing {field}')
        if c.contributor_id==c.reviewer_id: errors.append('reviewer must differ from contributor')
        if len(c.artifact_sha256)!=64 or any(ch not in '0123456789abcdef' for ch in c.artifact_sha256): errors.append('artifact_sha256 must be lowercase SHA-256')
        if c.baseline_version==c.candidate_version: errors.append('baseline and candidate versions must differ')
        if not c.tests: errors.append('at least one behavioral test required')
        for i,t in enumerate(c.tests):
            if not t.case_id.strip(): errors.append(f'test[{i}] missing case_id')
            if t.after!=t.expected: errors.append(f'test[{i}] revised behavior does not match expected output')
            if t.before==t.expected: errors.append(f'test[{i}] does not show a baseline failure corrected by candidate')
        if errors:
            self._record('CONTRIBUTION_REJECTED',{'contribution_id':c.contribution_id,'contributor_id':c.contributor_id,'errors':errors,'candidate_sha256':sha(asdict(c))})
            return {'status':'REJECTED','errors':errors}
        p={'contribution':asdict(c),'status':'VERIFIED','verification':{'test_count':len(c.tests),'reviewer_id':c.reviewer_id,'candidate_sha256':sha(asdict(c))}}
        self._record('CONTRIBUTION_VERIFIED',p)
        return {'status':'VERIFIED','contribution_id':c.contribution_id,'evidence_hash':p['verification']['candidate_sha256'],'test_count':len(c.tests)}
    def register_value_pool(self,p: ValuePool):
        if p.pool_id in self.pools: raise ValueError('pool_id already exists; records are immutable')
        errors=[]
        if not p.period.strip(): errors.append('missing measurement period')
        if len(p.currency)!=3 or not p.currency.isalpha(): errors.append('currency must be a 3-letter code')
        if not isinstance(p.gross_value_minor,int) or not isinstance(p.attributable_costs_minor,int) or min(p.gross_value_minor,p.attributable_costs_minor)<0: errors.append('value/costs must be nonnegative integer minor units')
        if not p.measurement_basis.strip(): errors.append('missing measurement basis')
        if not p.evidence_reference.strip(): errors.append('missing value evidence reference')
        if not p.independently_reviewed_by.strip(): errors.append('missing independent reviewer')
        if errors:
            self._record('VALUE_POOL_REJECTED',{'pool':asdict(p),'errors':errors}); return {'status':'REJECTED','errors':errors}
        net=max(0,p.gross_value_minor-p.attributable_costs_minor)
        self._record('VALUE_POOL_REGISTERED',{'pool':asdict(p),'distributable_minor':net})
        return {'status':'REGISTERED','pool_id':p.pool_id,'distributable_minor':net,'currency':p.currency}
    def approve_policy(self,p: AllocationPolicy):
        if p.policy_id in self.policies: raise ValueError('policy_id already exists; policies are immutable')
        errors=[]
        if p.version<1: errors.append('version must be >= 1')
        if not p.basis.strip(): errors.append('missing allocation basis')
        if not p.weights or any(not isinstance(v,int) or v<=0 for v in p.weights.values()): errors.append('weights must be positive integers')
        if not p.approved_by.strip() or not p.approval_reference.strip(): errors.append('missing approving authority/reference')
        if not p.dispute_process.strip(): errors.append('missing dispute/appeal process')
        unknown=sorted(set(p.weights)-set(self.contributions))
        if unknown: errors.append('weights reference unverified/unknown contributions: '+', '.join(unknown))
        if errors:
            self._record('ALLOCATION_POLICY_REJECTED',{'policy':asdict(p),'errors':errors}); return {'status':'REJECTED','errors':errors}
        payload={'policy':asdict(p),'status':'APPROVED','policy_sha256':sha(asdict(p))}
        self._record('ALLOCATION_POLICY_APPROVED',payload)
        return {'status':'APPROVED','policy_id':p.policy_id,'policy_sha256':payload['policy_sha256']}
    def calculate_allocation(self,pool_id,policy_id):
        if pool_id not in self.pools: raise ValueError('unknown/unregistered value pool')
        if policy_id not in self.policies: raise ValueError('unknown/unapproved allocation policy')
        pool=self.pools[pool_id]['pool']; policy=self.policies[policy_id]['policy']
        net=max(0,pool['gross_value_minor']-pool['attributable_costs_minor']); weights=policy['weights']; total=sum(weights.values())
        amounts={k:(net*v)//total for k,v in weights.items()}; remainders={k:(net*v)%total for k,v in weights.items()}; remainder=net-sum(amounts.values())
        for k in sorted(weights,key=lambda k:(-remainders[k],k))[:remainder]: amounts[k]+=1
        result={'status':'CALCULATED_NOT_PAID','pool_id':pool_id,'policy_id':policy_id,'currency':pool['currency'],'gross_value_minor':pool['gross_value_minor'],'costs_minor':pool['attributable_costs_minor'],'distributable_minor':net,'basis':policy['basis'],'weights':weights,'allocations_minor':amounts,'governance':{k:policy[k] for k in ('approved_by','approval_reference','dispute_process')},'limitations':['Value causation and measurement are not independently proved by this prototype.','Reviewer labels are not authenticated identities.','This calculation creates no legal entitlement and executes no payment.']}
        self._record('ALLOCATION_CALCULATED',result); return result

def example_contribution():
    return Contribution('contrib-001','contributor-alias-7',sha('example-candidate-artifact-v1'),'Correction changes missing-evidence behavior from guessing to abstaining.','demo://correction-proposal/001','judge-v1','judge-v2',(BehavioralTest('missing-fact-01','ABSTAIN','ANSWER: guessed value','ABSTAIN'),BehavioralTest('answerable-01','ANSWER: 42','ABSTAIN','ANSWER: 42')),'independent-reviewer-alias-2','Illustrative reproducible case; reviewer identity is not authenticated.')
def demo(audit_path='bridge_audit.jsonl'):
    b=ContributionBridge(audit_path); c=b.verify_contribution(example_contribution())
    p=b.register_value_pool(ValuePool('pool-demo-001','demo-period-2026','USD',10000,2000,'Illustrative net benefit, not real revenue evidence','demo://value-measurement/001','reviewer-alias-2'))
    a=b.approve_policy(AllocationPolicy('policy-demo-001',1,'Illustrative contribution points; 2:1 weighting',{'contrib-001':2},'governance-reviewer-alias-3','demo://approval/001','Appeal to a reviewer not involved in the original decision'))
    alloc=b.calculate_allocation('pool-demo-001','policy-demo-001') if c['status']=='VERIFIED' and p['status']=='REGISTERED' and a['status']=='APPROVED' else None
    return {'contribution':c,'value_pool':p,'policy':a,'allocation':alloc,'audit_events':len(b.events),'audit_head':b.events[-1]['hash']}
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--audit',default='bridge_audit.jsonl'); args=ap.parse_args(); print(json.dumps(demo(args.audit),indent=2))
