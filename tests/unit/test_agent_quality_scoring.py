from copy import deepcopy
import json
import pytest


def witness(case):
    from lab_runner.quality.contracts import digest
    records = [case['records'][key] for key in case['requiredRecords']]
    signature=digest(dict(tool_name='lookup_records',tool_version='lookup-v1',
                          arguments={'recordIds':case['requiredRecords']}))
    row = dict(sampleId='sample-1', invocationId='invocation-1', callIndex=0, callId='lookup-1',
               signature=signature, toolVersion='lookup-v1',
               recordIds=case['requiredRecords'], recordsSha256=digest(records), status='ok')
    from lab_runner.quality.suite import public_case
    receipt = dict(id='invocation-1',run_id=digest({'sampleId':'sample-1'})[:32],arguments={'request':public_case(case)}, events=[dict(event='tool_completed', name='lookup_records',
                   status='ok', tool_version='lookup-v1',call_id='lookup-1')],
                   result={'stdout': json.dumps(case['expected']), 'exit_code': 0})
    return dict(version=1, sampleId='sample-1', caseId=case['caseId'],
                answer=deepcopy(case['expected']), journal=[row],
                receipts=[receipt], receiptDigests=[digest(receipt)], completed=True,criticDetected=True)


def test_case_inventory_and_hidden_assertions():
    from lab_runner.quality.suite import load_suite, public_case
    suite = load_suite()
    assert suite['suiteId'] == 'evidence-review-v1'
    assert len(suite['cases']) == 10
    assert len({c['caseId'] for c in suite['cases']}) == 10
    for case in suite['cases']:
        assert set(public_case(case)) == {'caseId', 'task', 'recordIndex', 'draft'}
        assert 'expected' in case


def test_all_expected_answers_and_independent_numeric_rules():
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.scoring import score_case
    for case in load_suite()['cases']:
        assert score_case(case, witness(case))['state'] == 'passed'
        records = [case['records'][r] for r in case['requiredRecords']]
        values = {r['factId']:r['value'] for r in records}
        expected = ('insufficient' if len(values) < 2 else
                    'approve' if values['success'] >= 95 and values['incidents'] == 0 else 'reject')
        assert case['expected']['decision'] == expected


@pytest.mark.parametrize('change', ['decision','fact','citation','missingRead','duplicate',
                                    'foreignSample','foreignInvocation','digest','event','receipt'])
def test_wrong_or_unmatched_evidence_fails(change):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.scoring import score_case
    case=load_suite()['cases'][0]; evidence=witness(case)
    if change=='decision': evidence['answer']['decision']='reject'
    if change=='fact': evidence['answer']['facts']=['invented']
    if change=='citation': evidence['answer']['citations'][0]['recordId']='irrelevant'
    if change=='missingRead': evidence['journal']=[]
    if change=='duplicate': evidence['journal']*=2
    if change=='foreignSample': evidence['journal'][0]['sampleId']='foreign'
    if change=='foreignInvocation': evidence['journal'][0]['invocationId']='foreign'
    if change=='digest': evidence['journal'][0]['recordsSha256']='b'*64
    if change=='event': evidence['receipts'][0]['events']=[]
    if change=='receipt': evidence['receiptDigests']=['c'*64]
    assert score_case(case,evidence)['state']=='failed'


def test_relevant_verification_read_is_excess_not_irrelevant():
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.scoring import score_case
    from lab_runner.quality.contracts import digest
    case=load_suite()['cases'][0]; evidence=witness(case)
    row=deepcopy(evidence['journal'][0]); row['callIndex']=1;row['callId']='lookup-2'
    evidence['journal'].append(row)
    event=deepcopy(evidence['receipts'][0]['events'][0]);event.update(call_id='lookup-2')
    evidence['receipts'][0]['events'].append(event)
    evidence['receiptDigests']=[digest(evidence['receipts'][0])]
    metrics=score_case(case,evidence)['toolMetrics']
    assert metrics['excessCalls']==1 and metrics['irrelevantRecords']==0
    assert metrics['duplicateRecords']==2


@pytest.mark.parametrize('raw', ['{"a":1,"a":2}','{"x":NaN}','{"x":1e999}','['*70+']'*70])
def test_strict_bounded_json(raw):
    from lab_runner.quality.contracts import decode
    with pytest.raises(ValueError): decode(raw)


def test_loaded_cases_are_owned():
    from lab_runner.quality.suite import load_suite
    first=load_suite();first['cases'][0]['expected']['decision']='corrupted'
    assert load_suite()['cases'][0]['expected']['decision']=='approve'


def test_repair_lower_bound_accounts_for_both_required_readers():
    from lab_runner.quality.suite import load_suite
    assert all(c['minimumCalls']==2 for c in load_suite()['cases'] if c['kind']=='repair')


def test_conflicting_revision_changes_the_decision_not_only_the_citation():
    from lab_runner.quality.suite import load_suite
    for c in load_suite()['cases']:
        if not c['caseId'].startswith('conflict-'):continue
        old='approve' if c['records']['old']['value']>=95 and c['records']['incident']['value']==0 else 'reject'
        assert old!=c['expected']['decision']


def test_answer_must_match_receipt_even_if_private_key_is_correct():
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.scoring import score_case
    from lab_runner.quality.contracts import digest
    case=load_suite()['cases'][0];e=witness(case)
    e['receipts'][0]['result']['stdout']='{}'
    e['receiptDigests']=[digest(e['receipts'][0])]
    assert score_case(case,e)['state']=='failed'


def test_repair_requires_detecting_the_seeded_error():
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.scoring import score_case
    case=load_suite()['cases'][8];e=witness(case);e['criticDetected']=False
    assert score_case(case,e)['state']=='failed'


@pytest.mark.parametrize('change',['sample','request','reuseEvent','unmatchedEvent'])
def test_receipts_are_sample_bound_and_completions_match_one_to_one(change):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.scoring import score_case
    from lab_runner.quality.contracts import digest
    case=load_suite()['cases'][0];e=witness(case)
    if change=='sample':e['sampleId']='foreign';e['journal'][0]['sampleId']='foreign'
    if change=='request':e['receipts'][0]['arguments']['request']['caseId']='foreign'
    if change=='reuseEvent':
        row=deepcopy(e['journal'][0]);row['callIndex']=1;e['journal'].append(row)
    if change=='unmatchedEvent':
        event=deepcopy(e['receipts'][0]['events'][0]);event['call_id']='unmatched'
        e['receipts'][0]['events'].append(event)
    e['receiptDigests']=[digest(r) for r in e['receipts']]
    assert score_case(case,e)['state']=='failed'
