"""Required real owned-stack operational observations; no infrastructure skips."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

from lab_runner.qualification import run
from lab_runner.workload import Events

def short_profile():
    profile=json.loads(Path('configs/qualification.synthetic.json').read_text())
    profile.update(duration_s=2,window_s=1,arrivals_per_second=3,users=3,
        maximum_calls=10,maximum_records=10000)
    return profile

def test_real_fairness_reads_growth_and_usage_are_measured(lab):
    directory=Path(lab['fixture_manifest']).parent
    result=run(lab,short_profile(),Events(directory))
    assert result['qualification']=='qualified'
    assert result['fixture_passed'] is True and result['fairness_passed'] is True
    assert result['counts']['offered']==6 and result['counts']['completed']==6
    assert result['counts']['read_samples']==6 and result['counts']['read_failures']==0
    assert result['growth']['records_after']-result['growth']['records_before']==6
    assert result['accounting_reconciled'] is True and result['tool_latency_p95_s']>=0

@pytest.mark.parametrize('mode',['legacy','native'])
def test_real_restore_cli_reports_measured_markers_and_verified_cleanup(lab,tmp_path,mode):
    manifest=json.loads(Path(lab['fixture_manifest']).read_text())
    profile=tmp_path/'restore-profile.json';profile.write_text(json.dumps(short_profile()))
    arguments=[sys.executable,'-m','lab_runner','qualify-recovery','--profile',str(profile),
        '--postgres-version',str(manifest['postgres_major']),'--consumer-image',manifest['images']['consumer']]
    if mode=='native':arguments+=['--mode','native']
    if lab.get('dependency_mode')=='candidate':arguments+=['--candidate','--candidate-manifest',lab['candidate_manifest']]
    process=subprocess.run(arguments,
        capture_output=True,text=True,timeout=300)
    result=next(json.loads(line) for line in process.stdout.splitlines() if line.startswith('{'))
    assert process.returncode==0 and result['qualification']=='qualified'
    assert result['acknowledged_markers']==2 and result['observed_rpo_s']==0
    assert result['observed_rto_s']>=0 and result['redispatch_detected'] is False
    assert result['cleanup']=='verified' and result['logical_restore_only'] is True
    if mode=='native':
        assert result['native_verified'] is True and result['native_runs']==4 and result['native_proposals']==3
        for field in ('proposal_verified','reference_verified','bundle_verified','reservation_verified',
            'snapshot_verified','receipt_document_verified','interaction_verified','native_usage_verified',
            'journal_verified','domain_verified','completed_claim_verified','uncertain_claim_verified'):
            assert result[field] is True
