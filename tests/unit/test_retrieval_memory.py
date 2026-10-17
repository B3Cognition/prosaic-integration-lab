from copy import deepcopy
import json
import pytest
from lab_runner.quality.contracts import digest,encode


def corpus_data():
    source={'tenantId':'alpha','sourceId':'metrics','sourceVersion':1,'record':{'success':98}}
    episode={'episodeId':'prior','tenantId':'alpha','observedAt':'2026-01-01T00:00:00Z',
             'tags':['orchid','rollout'],'note':'Orchid metrics recorded previously.',
             'sourceRefs':[{'sourceId':'metrics','sourceVersion':1,'sourceSha256':digest(source['record'])}]}
    return {'version':1,'episodes':[episode]},{'version':1,'sources':[source]}


def load(document=None,sources=None):
    from lab_runner.memory.corpus import Corpus
    d,s=corpus_data()
    return Corpus(d if document is None else document,s if sources is None else sources)


def test_recall_is_tenant_scoped_and_does_not_mutate_or_expose_tenant():
    d,s=corpus_data();c=load(d,s)
    r=c.retrieve('alpha','ORCHID','2026-02-01T00:00:00Z')
    assert [x['episodeId'] for x in r['episodes']]==['prior']
    assert 'tenantId' not in r['episodes'][0]
    assert r['resultBytes']==len(encode(r['episodes']))
    assert r['resultSha256']==digest(r['episodes'])
    assert c.retrieve('beta','orchid','2026-02-01T00:00:00Z')['episodes']==[]
    d['episodes'][0]['note']='changed';s['sources'][0]['record']['success']=0
    r['episodes'][0]['note']='changed again'
    assert c.retrieve('alpha','orchid','2026-02-01T00:00:00Z')['episodes'][0]['note'].startswith('Orchid')


def test_foreign_only_valid_changes_preserve_all_local_retrieval_identity():
    d,s=corpus_data();before=load(d,s).retrieve('alpha','orchid','2026-02-01T00:00:00Z')
    foreign=deepcopy(d['episodes'][0]);foreign.update(tenantId='beta',episodeId='foreign',note='Orchid '*10)
    d['episodes'].append(foreign)
    fs=deepcopy(s['sources'][0]);fs['tenantId']='beta';s['sources'].append(fs)
    assert load(d,s).retrieve('alpha','orchid','2026-02-01T00:00:00Z')==before


def test_rank_uses_unique_overlap_then_newest_then_id_and_filters_future():
    d,s=corpus_data();base=d['episodes'][0]
    for name,date,note in [('z','2026-01-02','orchid orchid'),('a','2026-01-02','orchid'),
                           ('future','2027-01-01','orchid rollout'),('top','2026-01-01','orchid rollout')]:
        e=deepcopy(base);e.update(episodeId=name,observedAt=date+'T00:00:00Z',note=note,tags=[]);d['episodes'].append(e)
    d['episodes'][0]['tags']=[]
    r=load(d,s).retrieve('alpha','orchid rollout','2026-02-01T00:00:00Z')
    assert [e['episodeId'] for e in r['episodes']]==['top','a','z']
    assert r['eligibleCount']==4 and r['candidateCount']==4
    assert load(d,s).retrieve('alpha','unrelated','2026-02-01T00:00:00Z')['episodes']==[]


def test_whole_episode_byte_packing_and_maximum_three_results():
    d,s=corpus_data();base=d['episodes'][0]
    for i in range(3):
        src=deepcopy(s['sources'][0]);src['sourceId']='extra'+str(i);s['sources'].append(src)
        base['sourceRefs'].append({'sourceId':src['sourceId'],'sourceVersion':1,'sourceSha256':digest(src['record'])})
    base['note']='orchid '+('x'*1017)
    for name in ['second','third','fourth']:
        e=deepcopy(base);e['episodeId']=name
        if name=='fourth':e['note']='orchid';e['sourceRefs']=e['sourceRefs'][:1]
        d['episodes'].append(e)
    r=load(d,s).retrieve('alpha','orchid','2026-02-01T00:00:00Z')
    assert 1<=len(r['episodes'])<=3 and r['resultBytes']<=4096
    assert all(e['note'] in ('orchid',base['note']) for e in r['episodes'])
    assert any(e['episodeId']=='fourth' for e in r['episodes'])


@pytest.mark.parametrize('change',[
    lambda d,s:d.update(unexpected=True),
    lambda d,s:d['episodes'].append(deepcopy(d['episodes'][0])),
    lambda d,s:d['episodes'][0].update(observedAt='2026-01-01'),
    lambda d,s:d['episodes'][0].update(note='x'*1025),
    lambda d,s:d['episodes'][0]['sourceRefs'][0].update(sourceSha256='0'*64),
    lambda d,s:d['episodes'][0]['sourceRefs'][0].update(sourceId='absent'),
    lambda d,s:s['sources'].append(deepcopy(s['sources'][0])),
    lambda d,s:d['episodes'][0].update(tags=['x']*9),
    lambda d,s:d.update(version=True),
    lambda d,s:d['episodes'][0]['sourceRefs'][0].update(sourceVersion=True),
    lambda d,s:d['episodes'][0].update(tenantId='../escape'),
    lambda d,s:s.update(extra=[]),
])
def test_bad_admission_fails_closed(change):
    d,s=corpus_data();change(d,s)
    with pytest.raises(ValueError):load(d,s)


@pytest.mark.parametrize('tenant,query,as_of',[
    ('../bad','orchid','2026-02-01T00:00:00Z'),('alpha','x'*8193,'2026-02-01T00:00:00Z'),
    ('alpha','orchid','2026-02-01T00:00:00+00:00')])
def test_invalid_trusted_query_is_rejected(tenant,query,as_of):
    with pytest.raises(ValueError):load().retrieve(tenant,query,as_of)


def test_prepared_arm_context_differs_only_in_notes_and_has_no_private_answers():
    from lab_runner.memory.context import prepare
    case={'caseId':'sample','tenantId':'alpha','asOf':'2026-02-01T00:00:00Z','entity':'orchid',
          'topics':['rollout'],'task':'Review rollout','recordIndex':[{'recordId':'metrics','factId':'success','authority':'auditor','revision':2}],
          'expected':{'secret':'answer'},'goldEpisodes':['prior']}
    a=prepare(case,load(),'enabled');b=prepare(case,load(),'disabled')
    assert a['request']['recalledEpisodes'] and b['request']['recalledEpisodes']==[]
    assert {k:v for k,v in a['request'].items() if k!='recalledEpisodes'}=={k:v for k,v in b['request'].items() if k!='recalledEpisodes'}
    assert 'secret' not in json.dumps(a['request']) and 'tenantId' not in a['request']
    assert a['binding']!=b['binding']
    with pytest.raises(ValueError):prepare(case,load(),'arbitrary')
