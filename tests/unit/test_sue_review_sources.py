from copy import deepcopy
import importlib
import json
import hashlib
import sys

import pytest


def api():
    assert importlib.util.find_spec('prosaic_integration_lab.sue_review') is not None, 'SUE review is not implemented'
    from prosaic_integration_lab.sue_review import contracts, sources
    return contracts, sources


def test_disabled_and_lifetime_settings():
    c, _ = api()
    assert c.ReviewSettings.from_mapping(None).enabled is False
    enabled = c.ReviewSettings.from_mapping({'enabled': True})
    assert enabled.lifetime_s == 86400 and enabled.max_calls == 28
    assert c.ReviewSettings.from_mapping({'enabled': True, 'lifetime_s': 172800}).lifetime_s == 172800
    for value in ({'enabled': False, 'lifetime_s': 3}, {'enabled': True, 'lifetime_s': True}, {'enabled': True, 'lifetime_s': 604801}, {'enabled': True, 'max_calls': 29}):
        with pytest.raises(c.ReviewError): c.ReviewSettings.from_mapping(value)


def test_exact_sources_line_mapping_and_detached_identity():
    c, s = api()
    original = [{'sourceId': 'spec', 'text': 'Exact 🙂\r\nSecond line\r\n', 'revision': 'r1'}]
    frozen = s.freeze_documents(original)
    assert frozen['sources'][0]['text'] == original[0]['text']
    assert s.source_lines(frozen) == ['Exact 🙂', 'Second line']
    assert frozen['lineMap'] == [{'sourceId': 'spec', 'sourceLine': 1}, {'sourceId': 'spec', 'sourceLine': 2}]
    changed = deepcopy(original); changed[0]['revision'] = 'r2'
    assert s.freeze_documents(changed)['sourcesSha256'] != frozen['sourcesSha256']
    changed = deepcopy(original); changed[0]['reference'] = 'new-ref'
    assert s.freeze_documents(changed)['sourcesSha256'] != frozen['sourcesSha256']
    original[0]['text'] = 'mutated'
    assert frozen['sources'][0]['text'] == 'Exact 🙂\r\nSecond line\r\n'
    with pytest.raises(c.ReviewError): s.freeze_documents([{'sourceId': 'a', 'text': 'x'*65537}])
    with pytest.raises(c.ReviewError): s.freeze_documents([{'sourceId': 'a', 'text': 'x'}]*2)


def test_strict_decoder_rejects_duplicate_nonfinite_and_depth():
    c, _ = api()
    for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}', '['*70+'0'+']'*70):
        with pytest.raises(c.ReviewError): c.decode(raw)


def test_selected_capture_has_trusted_scope_and_full_provenance_digest():
    c, s = api()
    source = {'record_id':'r1','text_sha256':c.text_digest('hello'),'revision':'v1','representation':'original','wing':'project','captured_at':None,'source_id':'s1'}
    payload = {'schema_version':1,'sources':[source],'texts':['hello']}
    bundle = {**payload, 'digest': c.digest(payload)}
    scope = {'tenant_id':'tenant','actor_id':'alice','billing_account_id':'payer','namespace':'memory','binding_sha256':'a'*64,'allowed_wings':['project']}
    frozen = s.freeze_castle_snapshot({'bundle':bundle,'scope':scope}, expected_scope=scope)
    assert s.source_lines(frozen) == ['hello']
    other = deepcopy(scope);other['actor_id'] = 'bob'
    with pytest.raises(c.ReviewError): s.freeze_castle_snapshot({'bundle':bundle,'scope':other}, expected_scope=scope)
    with pytest.raises(c.ReviewError): s.freeze_castle_snapshot(bundle, expected_scope=scope)
    altered = deepcopy(payload);altered['sources'][0]['revision'] = 'v2'
    new = s.freeze_castle_snapshot({'bundle':{**altered,'digest':c.digest(altered)},'scope':scope}, expected_scope=scope)
    assert new['sourcesSha256'] != frozen['sourcesSha256']


def test_actual_castle_v1_snapshot_hash_survives_json_key_reordering():
    c, s = api()
    text = 'Exact 🙂\r\nSecond line\r\n'
    source = {'record_id':'r1','text_sha256':c.text_digest(text),'revision':'v1',
              'representation':'original','wing':'project','captured_at':None,'source_id':'s1'}
    # Castle protocol v1 hashes this exact field order, independently of the
    # outer response dataclass's order. JSON dictionaries may reorder in storage.
    payload = {'schema_version':1,'sources':[source],'texts':[text]}
    wire_hash = hashlib.sha256(json.dumps(payload,ensure_ascii=False,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert wire_hash != c.digest(payload)
    bundle = json.loads(json.dumps({**payload,'digest':wire_hash},sort_keys=True))
    scope = {'tenant_id':'tenant','actor_id':'alice','billing_account_id':'payer',
             'namespace':'memory','binding_sha256':'a'*64,'allowed_wings':['project']}
    frozen = s.freeze_castle_snapshot({'bundle':bundle,'scope':scope},expected_scope=scope)
    assert frozen['snapshotDigest'] == wire_hash
    assert frozen['sources'][0]['text'].encode() == text.encode()
    assert s.verify_frozen(frozen) == frozen
    for section in ('revision','wing','source_id'):
        forged = deepcopy(bundle)
        forged['sources'][0][section] = 'tampered'
        with pytest.raises(c.ReviewError):
            s.freeze_castle_snapshot({'bundle':forged,'scope':scope},expected_scope=scope)
    forged = deepcopy(bundle);forged['texts'][0] = text.replace('\r\n','\n')
    with pytest.raises(c.ReviewError):
        s.freeze_castle_snapshot({'bundle':forged,'scope':scope},expected_scope=scope)


@pytest.mark.parametrize('change', [
    {'schemaVersion': True}, {'sources': [True]}, {'capture': {'actor_id': 'forged'}},
    {'snapshotDigest': 'a'*64}, {'extra': 'ignored'},
    {'sources': [{'sourceId':'spec','text':'hello','revision':None,'reference':None,
                  'provenance': {'record_id':'forged'}, 'textSha256':'a'*64}]},
])
def test_rebound_frozen_input_still_requires_complete_admitted_shape(change):
    c, s = api()
    candidate = s.freeze_documents([{'sourceId':'spec','text':'hello'}])
    candidate.update(change)
    candidate.pop('sourcesSha256')
    candidate['sourcesSha256'] = c.digest(candidate)
    with pytest.raises(c.ReviewError):
        s.verify_frozen(candidate)
