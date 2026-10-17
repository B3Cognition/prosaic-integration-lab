"""Admit immutable synthetic history and retrieve only within a trusted tenant."""
from datetime import datetime
import re
from lab_runner.quality.contracts import decode,digest,encode,identifier,integer,sha


def fields(value,names):
    if type(value) is not dict or set(value)!=set(names):raise ValueError('invalid memory fields')


def timestamp(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',value):
        raise ValueError('invalid memory timestamp')
    datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ')
    return value


def text(value,maximum):
    if type(value) is not str or len(value.encode('utf-8'))>maximum:
        raise ValueError('invalid memory text')
    return value


def tokens(value):
    return set(re.findall('[a-z0-9]+',value.casefold()))


class Corpus:
    """Global admission is trusted configuration; all query identities are local."""
    def __init__(self,document,historical_sources):
        document=decode(encode(document,262144),262144)
        historical_sources=decode(encode(historical_sources,262144),262144)
        fields(document,('version','episodes'));fields(historical_sources,('version','sources'))
        integer(document['version'],1,1);integer(historical_sources['version'],1,1)
        episodes=document['episodes'];sources=historical_sources['sources']
        if type(episodes) is not list or len(episodes)>128 or type(sources) is not list or len(sources)>512:
            raise ValueError('memory corpus limit')
        source_map={};partitions={};histories={};seen=set()
        for source in sources:
            fields(source,('tenantId','sourceId','sourceVersion','record'))
            identifier(source['tenantId']);identifier(source['sourceId']);integer(source['sourceVersion'],1,1000000)
            if type(source['record']) is not dict:raise ValueError('invalid historical source')
            key=(source['tenantId'],source['sourceId'],source['sourceVersion'])
            if key in source_map:raise ValueError('duplicate historical source')
            source_map[key]=source
            histories.setdefault(source['tenantId'],[]).append(source)
        for episode in episodes:
            fields(episode,('episodeId','tenantId','observedAt','tags','note','sourceRefs'))
            tenant=identifier(episode['tenantId']);eid=identifier(episode['episodeId'])
            timestamp(episode['observedAt']);text(episode['note'],1024)
            if (tenant,eid) in seen:raise ValueError('duplicate memory episode')
            seen.add((tenant,eid))
            if type(episode['tags']) is not list or len(episode['tags'])>8:raise ValueError('invalid memory tags')
            for tag in episode['tags']:text(tag,64)
            refs=episode['sourceRefs']
            if type(refs) is not list or not 1<=len(refs)<=4:raise ValueError('invalid memory references')
            ref_seen=set()
            for ref in refs:
                fields(ref,('sourceId','sourceVersion','sourceSha256'))
                identifier(ref['sourceId']);integer(ref['sourceVersion'],1,1000000);sha(ref['sourceSha256'])
                key=(tenant,ref['sourceId'],ref['sourceVersion'])
                if key in ref_seen:raise ValueError('duplicate memory reference')
                ref_seen.add(key)
                if key not in source_map or digest(source_map[key]['record'])!=ref['sourceSha256']:
                    raise ValueError('unverified historical reference')
            partitions.setdefault(tenant,[]).append(episode)
        # Immutable canonical bytes prevent caller mutation through input/results.
        self.__partitions={tenant:encode(dict(episodes=sorted(partitions.get(tenant,[]),key=lambda e:e['episodeId']),
            sources=sorted(histories.get(tenant,[]),key=lambda s:(s['sourceId'],s['sourceVersion']))))
            for tenant in set(partitions)|set(histories)}

    def _partition(self,tenant_id):
        identifier(tenant_id)
        return decode(self.__partitions.get(tenant_id,encode(dict(episodes=[],sources=[]))))

    def tenant_digest(self,tenant_id):
        return digest(self._partition(tenant_id))

    def retrieve(self,tenant_id,query,as_of):
        query=text(query,8192);timestamp(as_of)
        partition=self._partition(tenant_id);query_tokens=tokens(query)
        eligible=[e for e in partition['episodes'] if e['observedAt']<=as_of]
        scored=[]
        for e in eligible:
            score=len(query_tokens & tokens(e['note']+' '+' '.join(e['tags'])))
            if score:scored.append((score,e))
        # Stable sorts keep score/date descending with ID ascending on ties.
        scored.sort(key=lambda row:row[1]['episodeId'])
        scored.sort(key=lambda row:row[1]['observedAt'],reverse=True)
        scored.sort(key=lambda row:row[0],reverse=True)
        result=[]
        for _,episode in scored:
            projected={k:v for k,v in episode.items() if k!='tenantId'}
            if len(encode(result+[projected]))<=4096:result.append(projected)
            if len(result)==3:break
        return dict(corpusDigest=digest(partition),querySha256=digest(query),asOf=as_of,
                    episodes=result,resultSha256=digest(result),resultBytes=len(encode(result)),
                    eligibleCount=len(eligible),candidateCount=len(scored))
