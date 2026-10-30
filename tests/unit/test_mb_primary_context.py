"""Synthetic checks for preserving the original local-evidence floor."""
import copy
import hashlib

from lab_runner.memory_benchmark.budget_views import EvidenceBudget

try:
    from lab_runner.memory_benchmark.primary_context import plan_primary_context, ValidatedFetchCache
except ModuleNotFoundError:
    plan_primary_context = ValidatedFetchCache = None


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def record(source, index, text, role='neighbor'):
    return dict(recordId=f'{source}{index}', textSha256=sha(text), text=text,
        path=f'exports/note-{source}-fixture.md', sourceId=sha(source),
        sourceFileSha256=sha('source '+source), wing='notes', revision='r1',
        namespace='fixture', contextRole=role, chunkIndex=index,
        startChar=index*800, endChar=index*800+len(text), startLine=index+1,endLine=index+1)


def window(source='a', text='x'*650, seed=3):
    local=[record(source,i,text) for i in range(7)]
    # Source offsets, rather than text length or matching, define adjacency.
    position=0
    for r in local:
        r.update(startChar=position,endChar=position+len(r['text']))
        position=r['endChar']
    local[seed]['contextRole']='seed';local[0]['contextRole']='sourceIntroduction'
    related=[record(source+'related',i,'q'*650,'relatedIntroduction') for i in range(2)]
    related[1].update(startChar=650,endChar=1300)
    s=local[seed]
    heading=(f'source="{s["path"]}" sourceSha256={s["sourceFileSha256"]} '
        f'sourceId={s["sourceId"]} wing=notes revision=r1 namespace=fixture')
    return dict(seedId=s['recordId'],heading=heading,
        records=[s,local[0],*related,local[seed-1],local[seed+1],local[seed-2],local[seed+2]])


def plan(windows, **kwargs):
    assert plan_primary_context is not None, 'primary local-evidence floor is not implemented'
    return plan_primary_context(windows,**kwargs)


def test_furthest_local_record_survives_introductions_and_related_priority():
    frames=plan([window()])
    assert frames[0]['baselineRetainedIds']==['a1','a2','a3','a4','a5']
    assert set(frames[0]['retainedIds']) >= {'a1','a2','a3','a4','a5'}
    assert 'x'*650 in frames[0]['display']
    assert frames[0]['bytes'] <= 5120


def test_future_local_floor_is_reserved_before_earlier_extras():
    frames=plan([window('a'),window('b')],limit=9000,used=250)
    assert set(frames[0]['retainedIds']) >= {'a1','a2','a3','a4','a5'}
    assert set(frames[1]['retainedIds']) >= {'b1','b2','b3','b4','b5'}
    assert sum(f['bytes'] for f in frames)+250 <= 9000
    assert frames[0]['futureReservedBytes'] >= frames[1]['mandatoryBytes']


def test_duplicate_windows_free_room_for_introduction_without_losing_floor_union():
    frames=plan([window(),window()],limit=11000,used=250)
    assert set().union(*(set(f['retainedIds']) for f in frames)) >= {'a0','a1','a2','a3','a4','a5'}
    assert set(frames[1]['mandatoryIds'])=={'a3'}
    assert all(rid not in frames[1]['retainedIds'] for rid in ['a1','a2','a4','a5'])
    assert sum(f['bytes'] for f in frames)+250 <= 11000


def test_local_only_renderer_preserves_original_legacy_frame_exactly():
    w=window(text='plain\r\nŽ🙂')
    rows=sorted([r for r in w['records'] if r['sourceId']==sha('a') and 1<=r['chunkIndex']<=5],key=lambda r:r['chunkIndex'])
    legacy=EvidenceBudget().render_records(w['heading'],w['seedId'],rows)
    priority=sorted(rows,key=lambda r:(r['recordId']!=w['seedId'],abs(r['chunkIndex']-3),r['chunkIndex']))
    actual=EvidenceBudget().render_document_context(w['heading'],w['seedId'],priority)
    assert actual==legacy


def test_noncontiguous_groups_have_exact_offsets_and_related_own_identity():
    w=window(text='Ž\r\nÁ🙂')
    rows=[w['records'][0],w['records'][1],w['records'][2]]
    out=EvidenceBudget().render_document_context(w['heading'],w['seedId'],rows)
    assert '[gap chars=6:18]' in out['display']
    assert '[related source introduction]\n' in out['display']
    assert f'sourceId={sha("arelated")}' in out['display']
    assert 'role="seed"' not in out['display']
    texts={r['recordId']:r['text'] for r in rows}
    for span in out['bodySpans']:
        assert out['display'][span['start']:span['end']].encode()==texts[span['recordId']].encode()


def test_unicode_headers_status_bytes_and_tiny_remaining_cap_are_charged():
    w=window(text='Ž🙂'*180)
    frames=plan([w,w],limit=9000,used=1000+len('status: searched\n'.encode()))
    assert sum(f['bytes'] for f in frames) <= 7983
    assert all(f['bytes']==len(f['display'].encode())<=5120 for f in frames)
    assert all(f['mandatoryBytes']<=f['baselineBytes'] for f in frames)
    tiny=plan([w],limit=30,used=25)[0]
    assert tiny['bytes']<=5 and tiny['retainedIds']==[]


def test_cache_validates_once_and_returns_independent_exact_slices():
    from test_mb_document_context import fixture,Provider,NAMESPACE
    catalog,slices,sources,hit=fixture();provider=Provider(slices)
    assert ValidatedFetchCache is not None, 'validated fetch cache is not implemented'
    cache=ValidatedFetchCache(provider,catalog,NAMESPACE,['notes'])
    first=cache.fetch('a3',start_char=0,max_chars=800)
    first['provenance']['source_id']='modified';first['text']='modified'
    second=cache.fetch('a3',start_char=0,max_chars=800)
    assert second==slices['a3']
    assert provider.calls==[('a3',0,800)]
    broken=Provider(copy.deepcopy(slices));broken.slices['a2']['text']='tampered'
    import pytest
    with pytest.raises(ValueError):
        ValidatedFetchCache(broken,catalog,NAMESPACE,['notes']).fetch('a2',start_char=0,max_chars=800)


