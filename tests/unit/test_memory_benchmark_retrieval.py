import copy
import json

import pytest

from test_memory_benchmark_dataset import supplied
from lab_runner.memory_benchmark.dataset import freeze, load_frozen
from lab_runner.memory_benchmark.retrieval import prepare, fixture_provider, catalog_for


def bundle(tmp_path):
    path,policy,_=supplied(tmp_path);out=tmp_path/'frozen';freeze(path,policy,out)
    return out,load_frozen(out)


@pytest.mark.parametrize('arm',['manual','strict','expanded'])
def test_scoped_retrieval_exact_frames_and_zero_gold(tmp_path,arm):
    root,data=bundle(tmp_path);provider=fixture_provider(root,data)
    result=prepare(root,data,data['cases'][0],arm,provider=provider)
    assert result['memoryStatus']==('not_used' if arm=='manual' else 'available')
    assert sum(len(f['display'].encode()) for f in result['frames'].values())<=32768
    assert any('Decision: keep memory off.' in f['display'] for f in result['frames'].values())
    assert 'facets' not in json.dumps(result) and 'grading' not in json.dumps(result)
    for frame in result['frames'].values():
        for span in frame['bodySpans']:
            assert 0<=span['start']<span['end']<=len(frame['display'])
    if arm!='manual':
        assert provider.snapshots==1 and len(provider.fetches)==len(set(provider.fetches))
        assert result['sourceExpansion'] is (arm=='expanded')


def test_tampered_provider_or_wrong_scope_rejected_not_degraded_to_empty(tmp_path):
    root,data=bundle(tmp_path);provider=fixture_provider(root,data)
    original=provider.fetch
    def broken(*args,**kwargs):
        value=original(*args,**kwargs);value['provenance']['wing']='other';return value
    provider.fetch=broken
    with pytest.raises(ValueError):prepare(root,data,data['cases'][0],'expanded',provider=provider)


def test_unavailable_distinct_from_empty_and_no_fallback_files(tmp_path):
    root,data=bundle(tmp_path)
    class Unavailable:
        def health(self):raise OSError('not available')
    result=prepare(root,data,data['cases'][0],'strict',provider=Unavailable())
    assert result['memoryStatus']=='unavailable' and not result['frames']
    provider=fixture_provider(root,data);case=copy.deepcopy(data['cases'][0]);case['queries']=['not-in-the-corpus']
    result=prepare(root,data,case,'strict',provider=provider)
    assert result['memoryStatus']=='empty'


def test_adapter_unavailable_error_remains_distinct_from_bad_provenance(tmp_path):
    root,data=bundle(tmp_path)
    class AdapterUnavailable(RuntimeError):code='unavailable'
    class Provider:
        def health(self):raise AdapterUnavailable('unavailable')
    assert prepare(root,data,data['cases'][0],'strict',provider=Provider())['memoryStatus']=='unavailable'


def test_generic_catalog_preserves_original_validator_and_requires_explicit_host_scope(tmp_path):
    from lab_runner.memory_benchmark.context_expansion import validate_catalog
    root,data=bundle(tmp_path);catalog,_,_=catalog_for(root,data)
    with pytest.raises(ValueError):validate_catalog(catalog)
    validate_catalog(catalog,namespace=data['namespace'],wings=data['allowedWings'])
    with pytest.raises(ValueError):validate_catalog(catalog,namespace='another-owner',wings=data['allowedWings'])


def test_snapshot_mismatch_rejects_before_packet_is_returned(tmp_path):
    root,data=bundle(tmp_path);provider=fixture_provider(root,data)
    provider.snapshot=lambda *a,**k:{'tampered':True}
    with pytest.raises(ValueError):prepare(root,data,data['cases'][0],'strict',provider=provider)


def test_expansion_replays_identical_search_without_new_ranking(tmp_path):
    root,data=bundle(tmp_path);provider=fixture_provider(root,data)
    strict=prepare(root,data,data['cases'][0],'strict',provider=provider)
    def forbidden(*a,**kw):raise AssertionError('expanded reranked seeds')
    provider.search=forbidden
    expanded=prepare(root,data,data['cases'][0],'expanded',provider=provider,
        search_replay=[row['result'] for row in strict['audit'] if row['op']=='search'])
    assert expanded['selectedIds']==strict['selectedIds']
    assert [f['display'] for f in expanded['frames'].values() if f['kind']=='search']==[
        f['display'] for f in strict['frames'].values() if f['kind']=='search']


def test_independent_capture_validation_rejects_forged_manual_text_and_grants(tmp_path):
    from lab_runner.memory_benchmark.retrieval import validate_capture
    root,data=bundle(tmp_path);case=data['cases'][0]
    captured=prepare(root,data,case,'manual')
    validate_capture(root,data,case,captured)
    frame=next(f for f in captured['frames'].values() if f['kind']=='open')
    frame['display']=frame['display'].replace('off.','yes.')
    with pytest.raises(ValueError):validate_capture(root,data,case,captured)


def test_late_provider_response_cannot_become_admitted_context(tmp_path,monkeypatch):
    from lab_runner.memory_benchmark import retrieval
    root,data=bundle(tmp_path);provider=fixture_provider(root,data);clock=[0.0]
    monkeypatch.setattr(retrieval.time,'monotonic',lambda:clock[0])
    old=provider.search
    def late(*a,**kw):clock[0]=301;return old(*a,**kw)
    provider.search=late
    with pytest.raises(TimeoutError):prepare(root,data,data['cases'][0],'strict',provider=provider)


def test_castle_wire_snapshot_digest_survives_canonical_evidence_roundtrip(tmp_path):
    from lab_runner.memory_benchmark.retrieval import validate_capture
    from lab_runner.memory_benchmark.storage import encoded,sha
    root,data=bundle(tmp_path);provider=fixture_provider(root,data);old=provider.snapshot
    def wire_snapshot(*args,**kwargs):
        value=old(*args,**kwargs)
        # Public Castle MemorySource declaration order; not sorted JSON keys.
        payload={k:value[k] for k in ('schema_version','sources','texts')}
        value['digest']=sha(json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode())
        return value
    provider.snapshot=wire_snapshot
    for arm in ('strict','expanded'):
        value=prepare(root,data,data['cases'][0],arm,provider=provider)
        assert validate_capture(root,data,data['cases'][0],value)==value
        saved=json.loads(encoded(value))
        assert validate_capture(root,data,data['cases'][0],saved)==saved
        altered=copy.deepcopy(saved);altered['snapshot']['digest']='0'*64
        with pytest.raises(ValueError,match='snapshot digest'):
            validate_capture(root,data,data['cases'][0],altered)
        altered=copy.deepcopy(saved);altered['snapshot']['texts'][0]+='forged'
        with pytest.raises(ValueError,match='snapshot exact source'):
            validate_capture(root,data,data['cases'][0],altered)
