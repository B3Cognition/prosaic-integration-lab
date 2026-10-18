"""The Lab adapter consumes actual SDK receipts; transport is scripted offline."""
from copy import deepcopy
import importlib.util
import pytest
from lab_runner.handoffs.direct import execute_case
from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
from lab_runner.quality.contracts import digest,decode,encode


def adapter():
    assert importlib.util.find_spec('lab_runner.handoffs.diagnostics'),'grounded diagnostics adapter missing'
    from lab_runner.handoffs.diagnostics import diagnose_direct
    return diagnose_direct


@pytest.mark.parametrize('provider',['openai','anthropic'])
def test_scoped_handoff_diagnostics_pass_without_changing_original_receipts(tmp_path,provider):
    case=example_case()
    with fixture_provider(case,provider=provider) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='grounded')
        before=deepcopy(e);p.deny=True;report=adapter()(case,e)
        assert p.requests==3 and e==before
    assert {r:v['status'] for r,v in report['roles'].items()}==dict(worker='passed',critic='passed')


@pytest.mark.parametrize('provider',['openai','anthropic'])
def test_partial_critic_warning_is_not_complete_verification(tmp_path,provider):
    case=example_case();draft=correct_worker(case);draft['answer']['decision']='reject';draft['answer']['citations']=[]
    with fixture_provider(case,provider=provider) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='partial',mode='critic',draft=draft)
    receipt=e['receipts'][0];value=decode(receipt['result']['stdout']);value['issues']=['decision']
    receipt['result']['stdout']=encode(value).decode();e['receiptDigests']=[digest(receipt)]
    r=adapter()(case,e)['roles']['critic']
    assert r['status']=='failed' and r['coarseEscalationCorrect']
    assert r['missingIssueFields']==['citations'] and r['unsupportedIssueFields']==[]
    assert any(d['field']=='/issues' and d['evidenceRefs'] for d in r['diagnostics'])
    value['issues']=['decision','citations','status'];receipt['result']['stdout']=encode(value).decode();e['receiptDigests']=[digest(receipt)]
    assert adapter()(case,e)['roles']['critic']['unsupportedIssueFields']==['status']


@pytest.mark.parametrize('corruption',['source_hash','sample','assignment','invocation','receipt','worker_binding'])
def test_corrupt_or_foreign_evidence_cannot_manufacture_diagnostics(tmp_path,corruption):
    case=example_case()
    with fixture_provider(case) as p:e=execute_case(case,config=p.config,output=tmp_path,sample_id='scope')
    if corruption=='source_hash':e['journal'][0]['recordsSha256']='0'*64
    if corruption=='sample':e['journal'][0]['sampleId']='other'
    if corruption=='assignment':e['journal'][0]['assignmentId']='0'*64
    if corruption=='invocation':e['journal'][0]['invocationId']='other'
    if corruption=='receipt':e['receiptDigests'][0]='0'*64
    if corruption=='worker_binding':
        e['receipts'][1]['arguments']['artifact_bindings']['worker']['id']='other'
        e['receiptDigests']=[digest(r) for r in e['receipts']]
    r=adapter()(case,e)
    assert all(v['status']!='passed' for v in r['roles'].values())
    assert all(any(d['code']=='unverified_evidence' for d in v['diagnostics']) for v in r['roles'].values())


def test_worker_diagnostics_enumerate_all_fields_without_expected_value_disclosure(tmp_path):
    case=example_case()
    with fixture_provider(case) as p:e=execute_case(case,config=p.config,output=tmp_path,sample_id='fields',mode='worker')
    receipt=e['receipts'][0];worker=decode(receipt['result']['stdout'])
    worker.update(assignmentId='0'*64,status='missing');worker['answer']=dict(decision='reject',facts=[],citations=[])
    receipt['result']['stdout']=encode(worker).decode();e['receiptDigests']=[digest(receipt)]
    r=adapter()(case,e)['roles']['worker']
    assert {d['field'] for d in r['diagnostics']}=={'/assignmentId','/status','/answer/decision','/answer/facts','/answer/citations'}
    assert all(d['evidenceRefs'] for d in r['diagnostics'])
    assert 'expected' not in encode(r).decode() and 'observed' not in encode(r).decode()


@pytest.mark.parametrize('family',['missing','unread','conflict','extra_unread'])
def test_correct_nonready_reviews_have_empty_issue_lists_and_remain_explicit(tmp_path,family):
    case=example_case(family);draft=correct_worker(case,family)
    ids=['metrics'] if family=='unread' else ['metrics','incident'] if family=='extra_unread' else None
    with fixture_provider(case,family=family) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='nonready',mode='critic',draft=draft,record_ids=ids)
    r=adapter()(case,e)['roles']['critic']
    assert r['status']=='passed' and r['missingIssueFields']==r['unsupportedIssueFields']==[]


def test_truncated_output_is_unusable_and_not_semantic_guesswork(tmp_path):
    case=example_case()
    with fixture_provider(case,scenario='invalid_worker') as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='invalid')
    r=adapter()(case,e)
    assert r['roles']['worker']['status']=='failed'
    assert any(d['code'] in ('schema_mismatch','invalid_json','unusable_output') for d in r['roles']['worker']['diagnostics'])
    assert r['roles']['critic']['status']=='unavailable'
