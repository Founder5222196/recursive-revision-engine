from pathlib import Path
import json, subprocess, sys, hashlib, shutil
from rre_persistent import PersistentRRE, evaluate, verify_chain
ROOT=Path(__file__).parent
OUT=ROOT/'artifacts'; OUT.mkdir(exist_ok=True)
# Run the unmodified prototype's original tests.
orig=subprocess.run([sys.executable,'test_rre_minimal.py'],cwd=ROOT,text=True,capture_output=True)
# New test suite.
new=subprocess.run([sys.executable,'-m','unittest','-v','test_rre_persistent.py'],cwd=ROOT,text=True,capture_output=True)
# Deterministic milestone demonstration in clean artifact dir.
state=OUT/'working_state.json'; audit=OUT/'milestone_audit.jsonl'
for p in (state,audit):
    if p.exists(): p.unlink()
r=PersistentRRE(state,audit)
# Move from prototype default behavior to known-good v2 through held-out verification.
initial=r.snapshot(); good_ok=r.commit_candidate({'missing_evidence':'report_unknown'},'v0.2-good-correction')
known_good=r.snapshot(); score_before=evaluate(r)
# Simulate process death/restart; constructor must append rather than truncate.
del r
r=PersistentRRE(state,audit); restart_snapshot=r.snapshot()
# Bad candidate always refuses; labels cannot make it pass.
bad_ok=r.commit_candidate({'missing_evidence':'always_refuse'},'renamed-as-good',acknowledged=True,accepted=True)
restored=r.snapshot(); score_after=evaluate(r)
chain_ok,chain_msg=verify_chain(audit)
report={
 'milestone':'RRE persistent state + adversarial revision + rollback',
 'existing_modules_changed':[],
 'recovered_source_note':'rre_heldout_eval.py was reconstructed from the prior conversation summary because its source file was not found in the accessible Library; rre_minimal.py and test_rre_minimal.py are byte-preserved.',
 'original_tests':{'returncode':orig.returncode,'stdout':orig.stdout,'stderr':orig.stderr},
 'add_on_tests':{'returncode':new.returncode,'stdout':new.stdout,'stderr':new.stderr},
 'good_candidate_retained':good_ok,
 'known_good_before_restart':known_good,
 'restored_after_restart':restart_snapshot,
 'faulty_candidate_passed':bad_ok,
 'same_state_after_fault':restored==known_good,
 'known_good_evaluator_before_bad_candidate':score_before,
 'known_good_evaluator_after_bad_candidate':score_after,
 'audit_chain':{'ok':chain_ok,'message':chain_msg,'events':len(audit.read_text().splitlines())},
 'state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),
 'audit_sha256':hashlib.sha256(audit.read_bytes()).hexdigest(),
 'all_commands_passed':orig.returncode==0 and new.returncode==0 and good_ok and not bad_ok and restored==known_good and score_before['passed']==score_after['passed']==8 and chain_ok
}
(OUT/'milestone_report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
(OUT/'execution_results.txt').write_text('COMMAND: python test_rre_minimal.py\nEXIT: '+str(orig.returncode)+'\nSTDOUT:\n'+orig.stdout+'STDERR:\n'+orig.stderr+'\nCOMMAND: python -m unittest -v test_rre_persistent.py\nEXIT: '+str(new.returncode)+'\nSTDOUT:\n'+new.stdout+'STDERR:\n'+new.stderr+'\nDEMO SUMMARY:\n'+json.dumps({k:report[k] for k in ['good_candidate_retained','faulty_candidate_passed','same_state_after_fault','known_good_evaluator_before_bad_candidate','known_good_evaluator_after_bad_candidate','audit_chain','all_commands_passed']},indent=2)+'\n')
print('COMMAND: python test_rre_minimal.py')
print(orig.stdout,end=''); print(orig.stderr,end='',file=sys.stderr)
print('COMMAND: python -m unittest -v test_rre_persistent.py')
print(new.stdout,end=''); print(new.stderr,end='',file=sys.stderr)
print('DEMO SUMMARY:')
print(json.dumps({k:report[k] for k in ['good_candidate_retained','faulty_candidate_passed','same_state_after_fault','known_good_evaluator_before_bad_candidate','known_good_evaluator_after_bad_candidate','audit_chain','all_commands_passed']},indent=2))
if not report['all_commands_passed']: raise SystemExit(1)
