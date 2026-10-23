from copy import deepcopy
import json
import pytest
from jsonschema import Draft202012Validator
from memory_helpers import development


def test_fact_schema_distinguishes_labels_from_record_ids_without_selecting_sources():
    from lab_runner.memory.contracts import answer_schema
    case,_,_,_=development();schema=answer_schema(case)
    assert set(schema['properties']['facts']['items']['enum'])=={'success','incidents'}
    cite=schema['properties']['citations']['items']['properties']
    assert set(cite['factId']['enum'])=={'success','incidents'}
    assert set(cite['recordId']['enum'])==set(case['records'])
    bad=deepcopy(case['expected']);bad['facts']=[case['requiredRecords'][0]]
    assert list(Draft202012Validator(schema).iter_errors(bad))
    assert not list(Draft202012Validator(schema).iter_errors(case['expected']))


def test_contract_never_reads_private_assertions_values_or_memory():
    from lab_runner.memory.contracts import answer_schema,feedback
    case,_,_,_=development();before=answer_schema(case)
    changed=deepcopy(case);changed['expected']='PRIVATE-CANARY';changed['requiredRecords']='PRIVATE-CANARY'
    changed['goldEpisodes']=['PRIVATE-CANARY'];changed['records']='PRIVATE-CANARY'
    assert answer_schema(changed)==before
    for code in ('decision','facts','citations'):
        text=feedback([code]);assert 'PRIVATE-CANARY' not in text and 'target' not in text
        assert 'approve' not in text and 'reject' not in text


def test_schema_keeps_observer_and_old_source_decoys_accessible():
    from lab_runner.memory.contracts import answer_schema
    case,_,_,_=development();row=deepcopy(case['recordIndex'][0]);row.update(recordId='old-source',revision=0)
    case['recordIndex'].append(row)
    row=deepcopy(row);row.update(recordId='observer-source',authority='observer',revision=99)
    case['recordIndex'].append(row)
    schema=answer_schema(case)
    assert {'old-source','observer-source'}<=set(schema['properties']['citations']['items']['properties']['recordId']['enum'])


def test_public_contract_explains_authority_first_absence_first_and_field_roles():
    from lab_runner.memory.execution import PROSE
    from lab_runner.memory.contracts import feedback
    assert 'authority before revision' in PROSE
    assert 'recordId only in citations' in PROSE
    assert 'absence before numeric conditions' in PROSE
    assert 'at most one' in PROSE
    assert 'factId labels' in feedback(['facts'])
    assert 'observer' in feedback(['citations']).casefold()
    assert 'absence before numeric conditions' in feedback(['decision'])


def test_grounding_helper_changes_bind_resume_and_schema_identity():
    from lab_runner.memory.execution import code_digest
    from lab_runner.memory.runner import identity
    from lab_runner.memory.contracts import answer_schema
    from lab_runner.quality.contracts import digest
    from test_retrieval_memory_runner import bundle
    b=bundle()
    assert identity(b)['schemaDigest']==digest({c['caseId']:answer_schema(c) for c in b['cases']})
    assert len(code_digest())==64


@pytest.mark.parametrize('package,target',[('lab_runner.memory','contracts.py'),('lab_runner.quality','token_admission.py')])
def test_helper_source_drift_blocks_saved_context_before_retrieval(tmp_path,monkeypatch,package,target):
    import lab_runner.memory.execution as execution
    case,corpus,_,_=development();path=tmp_path/'prepared.json'
    execution.freeze(case,corpus,'enabled',path);before=execution.code_digest();original=execution.files
    class ChangedText:
        def read_text(self,**kw):return original(package).joinpath(target).read_text(**kw)+'\n# changed contract\n'
    class ChangedRoot:
        def joinpath(self,name):return ChangedText() if name==target else original(package).joinpath(name)
    monkeypatch.setattr(execution,'files',lambda requested:ChangedRoot() if requested==package else original(requested))
    assert execution.code_digest()!=before
    def forbidden(*a,**kw):raise AssertionError('retrieval despite contract drift')
    monkeypatch.setattr(corpus,'retrieve',forbidden)
    with pytest.raises(ValueError,match='drift'):execution.freeze(case,corpus,'enabled',path)


def test_case_identity_changes_do_not_change_implementation_identity():
    from lab_runner.memory.runner import identity
    from test_retrieval_memory_runner import bundle
    b=bundle();before=identity(b);b['cases'][0]['caseId']='development-renamed'
    after=identity(b)
    assert after['suiteDigest']!=before['suiteDigest'] and after['schemaDigest']!=before['schemaDigest']
    assert after['implementationDigest']==before['implementationDigest']


@pytest.mark.parametrize('scenario',['repair_fact_ids','repair_source','repair_absence'])
def test_native_grounding_repairs_require_feedback_and_fresh_lookup(tmp_path,scenario):
    from lab_runner.memory.execution import execute_case
    from lab_runner.memory.scoring import score_case
    from lab_runner.memory.fixture import fixture_provider
    case,corpus,_,_=development();case['caseId']='development-grounding'
    if scenario=='repair_absence':
        case['records']={k:r for k,r in case['records'].items() if not(r['factId']=='incidents' and r['authority']=='auditor')}
        case['recordIndex']=[r for r in case['recordIndex'] if r['recordId'] in case['records']]
        case['requiredRecords']=[k for k in case['requiredRecords'] if k in case['records']]
        case['expected']=dict(decision='insufficient',facts=['success'],citations=[dict(factId='success',recordId='metrics')])
    with fixture_provider([case],scenario) as p:
        e=execute_case(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture-a',output=tmp_path,sample_id='grounding')
    assert p.requests==4 and len(e['journal'])==2 and e['completed']
    assert score_case(case,e)['state']=='passed'
    message=e['receipts'][1]['arguments']['validation_feedback']
    assert message and 'expected' not in message and 'target' not in message
    if scenario=='repair_source':assert 'authority before revision' in message
    if scenario=='repair_absence':assert 'absence before numeric conditions' in message
