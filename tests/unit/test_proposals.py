import pytest


def canonical(text):
    from prosaic_integration_lab.proposals import canonical_proposal
    return canonical_proposal(text)


def test_canonical_transport_preserves_unicode_and_sorts_original_keys():
    assert canonical(' {"z":1.0,"a":"žluť"} ') == '{"a":"žluť","z":1.0}'
    assert canonical(b'{"b":2,"a":1}') == '{"a":1,"b":2}'


@pytest.mark.parametrize('text', ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}',
    '{"a":1e999}', '{"a":"\\ud800"}', b'\xff', '1', '[]', '{',
    '{"a":'+ '9'*5000 +'}', '{"a":'+'['*65+'0'+']'*65+'}',
    '{"a":['+','.join('0' for _ in range(65536))+']}', '{"a":"'+'x'*65536+'"}'],
    ids=['duplicate','nan','infinity','overflow','surrogate','utf8','scalar','array','syntax',
         'number','depth','nodes','bytes'])
def test_invalid_transport_has_fixed_error_without_private_body(text):
    with pytest.raises(ValueError, match='^invalid_request$'):
        canonical(text)


def test_canonical_limit_applies_after_unicode_encoding_and_raw_transport():
    with pytest.raises(ValueError, match='^invalid_request$'):
        canonical('{"a":"'+'é'*32768+'"}')
    with pytest.raises(ValueError, match='^invalid_request$'):
        canonical(' '*65536+'{}')


def test_transport_matches_public_sdk_original_envelope_bytes(proposal_text, bundle_factory):
    saved = bundle_factory().prepare_json(proposal_text)
    assert canonical(proposal_text) == saved.proposal_json


def test_native_request_hash_uses_separate_original_recipe():
    from prosaic_integration_lab.metadata import canonical_native_request, canonical_request
    assert canonical_native_request('a'*32, {'ž':1.0}) == ('native-run-v1\n'+
        '{"inputs":{"ž":1.0},"proposal_id":"'+ 'a'*32 +'"}')
    assert canonical_request({'task':'ž','workflow':'approval'}) == '{"task":"\\u017e","workflow":"approval"}'


@pytest.mark.parametrize('inputs', [float('nan'), {'a':'x'*65536}, {'a':object()}, {'a':'\ud800'}])
def test_native_request_bounds_are_fixed_before_reservation(inputs):
    from prosaic_integration_lab.metadata import canonical_native_request
    with pytest.raises(ValueError, match='^invalid_request$'):
        canonical_native_request('a'*32, inputs)


@pytest.fixture
def persistence(tmp_path,monkeypatch):
    from persistence_sql import database
    from prosaic_integration_lab.metadata import Metadata
    from prosaic_integration_lab.proposals import ProposalStore
    from prosaic_integration_lab.identity import Principal
    connect = database(tmp_path/'proposals.sqlite')
    proposals,metadata = ProposalStore('unused'),Metadata('unused')
    monkeypatch.setattr(proposals,'connection',connect)
    monkeypatch.setattr(metadata,'connection',connect)
    return proposals,metadata,Principal('tenant','actor','billing')


def store(proposals,principal,prepared,key='key',maximum=100):
    return proposals.reserve(principal,key,prepared,maximum_records=maximum,maximum_tenant_records=maximum)


def test_sql_owned_replay_retains_exact_original_across_bundle_upgrade_and_capacity(persistence,prepared_v1,prepared_v2):
    from prosaic_integration_lab.identity import Principal
    from fastapi import HTTPException
    proposals,_,principal = persistence
    first = store(proposals,principal,prepared_v1)
    assert first['proposal_json'] == prepared_v1.proposal_json
    assert first['reference'] == prepared_v1.reference.to_dict()
    assert first['policy_digest'] == prepared_v1.reference.bundle_identity
    assert store(proposals,principal,prepared_v2,maximum=1) == first
    assert proposals.replay(principal,'key',first['request_digest']) == first
    assert proposals.owned(Principal('tenant','stranger','other'),first['proposal_id']) is None
    with pytest.raises(HTTPException) as error:
        store(proposals,principal,prepared_v1,'new-key',maximum=1)
    assert error.value.status_code == 503


def test_sql_changed_body_conflicts_without_readmitting_original(persistence,prepared_v1,bundle_factory,proposal_text):
    from prosaic_integration_lab.metadata import RequestConflict
    proposals,_,principal = persistence
    first = store(proposals,principal,prepared_v1)
    changed = bundle_factory().prepare_json(proposal_text.replace('Accept žluť?','Changed?'))
    with pytest.raises(RequestConflict): store(proposals,principal,changed)
    with pytest.raises(RequestConflict): proposals.replay(principal,'key','a'*64)
    assert proposals.owned(principal,first['proposal_id']) == first


def test_sql_concurrent_admissions_return_one_frozen_bundle_reference(persistence,prepared_v1,prepared_v2):
    from concurrent.futures import ThreadPoolExecutor
    proposals,_,principal = persistence
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda prepared:store(proposals,principal,prepared),[prepared_v1,prepared_v2]))
    assert rows[0] == rows[1]
    assert rows[0]['reference'] in [prepared_v1.reference.to_dict(),prepared_v2.reference.to_dict()]


def test_sql_native_reservation_is_owned_frozen_and_atomically_linked(persistence,prepared_v1):
    from prosaic_integration_lab.identity import Principal
    from prosaic_integration_lab.metadata import RequestConflict
    from fastapi import HTTPException
    proposals,metadata,principal = persistence
    proposal = store(proposals,principal,prepared_v1)
    inputs = prepared_v1.workflow.prepare_inputs({})
    run = metadata.reserve_native(principal,'run-key',proposal,inputs,namespace='original',environment='sandbox')
    replay = metadata.reserve_native(Principal('tenant','actor','changed'),'run-key',proposal,{},
        namespace='current',environment='production',max_runs=1,max_tenant_runs=1)
    assert run == replay
    assert run['billing_account_id'] == 'billing' and run['namespace'] == 'original'
    assert run['environment'] == 'sandbox' and run['request'] == {'proposal_id':proposal['proposal_id'],'inputs':{}}
    with metadata.connection() as connection:
        assert connection.execute('SELECT * FROM lab_app.native_runs WHERE run_id=%s',(run['run_id'],)).fetchone() == {
            'run_id':run['run_id'],'proposal_id':proposal['proposal_id'],'tenant_id':'tenant','actor_id':'actor'}
    with pytest.raises(RequestConflict):
        metadata.reserve_native(principal,'run-key',proposal,{'changed':True},namespace='original',environment='sandbox')
    with pytest.raises(HTTPException) as error:
        metadata.reserve_native(Principal('tenant','stranger','other'),'other-run',proposal,{},namespace='original',environment='sandbox')
    assert error.value.status_code == 404

