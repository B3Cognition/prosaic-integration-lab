import copy
import pytest
from lab_runner.gates import validate,export

def receipt(mode='audit'):
    return {'mode':mode,'passed':True,'cleanup':'verified','dependency_mode':'released',
        'test_returncode':0,'test_count':{'audit':82,'identity':19,'ingress':5}[mode],
        'payload_audit':'verified','released_manifest_sha256':'247a2b1b1d64b2f4ec318a6b6aec51c28b691fb41018044f8bac571c089d53c7',
        'skipped':0,'failed_tests':[],'host_architecture':'arm64',
        'images':{'consumer':'sha256:'+'1'*64,'postgres':'postgres:16@sha256:'+'2'*64}}

@pytest.mark.parametrize('patch',[{'passed':False},{'cleanup':'failed'},{'skipped':1},
    {'test_count':76},{'test_returncode':1},{'failed_tests':['test_failed']},
    {'dependency_mode':'candidate'},{'error':'EngineError'},{'host_architecture':'unknown'},
    {'payload_audit':None},{'released_manifest_sha256':'wrong'}])
def test_required_gate_rejects_incomplete_or_nonrelease_receipt(patch):
    item=receipt(); item.update(patch)
    with pytest.raises(ValueError): validate(item,'audit',16,candidate=False)

def test_required_gate_requires_exact_mode_and_database_major():
    with pytest.raises(ValueError): validate(receipt(),'identity',16,candidate=False)
    with pytest.raises(ValueError): validate(receipt(),'audit',18,candidate=False)

@pytest.mark.parametrize('item',[None,[],{'images':None}])
def test_malformed_receipts_fail_closed_and_have_safe_export(item):
    with pytest.raises(ValueError): validate(item,'audit',16,candidate=False)
    assert export(item)['passed'] is False

def test_candidate_receipts_require_matching_explicit_manifest():
    item=receipt(); item['dependency_mode']='candidate'
    with pytest.raises(ValueError): validate(item,'audit',16,candidate=True,manifest_sha='3'*64)
    item['candidate_manifest_sha256']='3'*64
    validate(item,'audit',16,candidate=True,manifest_sha='3'*64)

def test_safe_export_does_not_copy_arbitrary_receipt_fields():
    item=receipt(); item.update(token='PRIVATE',error='PRIVATE',failed_tests=['PRIVATE'])
    assert 'PRIVATE' not in str(export(item))
    assert export(item)['passed'] is False
