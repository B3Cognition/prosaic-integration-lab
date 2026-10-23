"""Trusted metadata controls scope, freshness and ranking; note text is data."""
from lab_runner.quality.contracts import decode,encode,digest,identifier,integer,sha
from lab_runner.memory.corpus import Corpus,fields,timestamp


def topics(value):
    if type(value) is not list or not 1<=len(value)<=8:
        raise ValueError('bounded trusted topics required')
    for topic in value:identifier(topic)
    if len(set(value))!=len(value):raise ValueError('duplicate trusted topic')
    return sorted(value)


class ScopedCorpus:
    """Read-only host policy over unchanged v1 history; no model authorization."""
    def __init__(self,document,historical_sources,metadata):
        document=decode(encode(document,262144),262144)
        historical_sources=decode(encode(historical_sources,262144),262144)
        metadata=decode(encode(metadata,262144),262144)
        Corpus(document,historical_sources)
        fields(metadata,('version','episodes','currentSources'));integer(metadata['version'],1,1)
        if (type(metadata['episodes']) is not list or len(metadata['episodes'])>128 or
                type(metadata['currentSources']) is not list or len(metadata['currentSources'])>512):
            raise ValueError('scope metadata bound')
        episodes={(e['tenantId'],e['episodeId']):e for e in document['episodes']}
        scoped={};current={};partitions={}
        for row in metadata['episodes']:
            fields(row,('tenantId','episodeId','entityId','topics','expiresAt'))
            for key in ('tenantId','episodeId','entityId'):identifier(row[key])
            topics(row['topics']);key=(row['tenantId'],row['episodeId'])
            if key in scoped or key not in episodes:raise ValueError('ambiguous episode metadata')
            if row['expiresAt'] is not None:
                timestamp(row['expiresAt'])
                if row['expiresAt']<=episodes[key]['observedAt']:raise ValueError('invalid episode expiry')
            scoped[key]=dict(row,topics=topics(row['topics']))
        if scoped.keys()!=episodes.keys():raise ValueError('incomplete episode metadata')
        for ref in metadata['currentSources']:
            fields(ref,('tenantId','sourceId','sourceVersion','sourceSha256'))
            identifier(ref['tenantId']);identifier(ref['sourceId']);integer(ref['sourceVersion'],1,1000000);sha(ref['sourceSha256'])
            key=(ref['tenantId'],ref['sourceId'])
            if key in current:raise ValueError('ambiguous current reference')
            current[key]=ref
        tenants={e['tenantId'] for e in document['episodes']}|{s['tenantId'] for s in historical_sources['sources']}|{r['tenantId'] for r in current.values()}
        for tenant in tenants:
            partitions[tenant]=encode(dict(
                episodes=sorted([e for e in document['episodes'] if e['tenantId']==tenant],key=lambda e:e['episodeId']),
                sources=sorted([s for s in historical_sources['sources'] if s['tenantId']==tenant],key=lambda s:(s['sourceId'],s['sourceVersion'])),
                metadata=sorted([s for (t,_),s in scoped.items() if t==tenant],key=lambda s:s['episodeId']),
                currentSources=sorted([r for (t,_),r in current.items() if t==tenant],key=lambda r:r['sourceId'])))
        self.__partitions=partitions

    def _partition(self,tenant_id):
        identifier(tenant_id)
        return decode(self.__partitions.get(tenant_id,encode(dict(episodes=[],sources=[],metadata=[],currentSources=[]))))

    def tenant_digest(self,tenant_id):
        return digest(self._partition(tenant_id))

    def retrieve(self,tenant_id,entity_id,query_topics,as_of):
        identifier(entity_id);query_topics=topics(query_topics);timestamp(as_of)
        partition=self._partition(tenant_id)
        metadata={r['episodeId']:r for r in partition['metadata']}
        refs={r['sourceId']:r for r in partition['currentSources']}
        decisions={};candidates=[];eligible=0
        for episode in partition['episodes']:
            eid=episode['episodeId'];scope=metadata[eid];reason=None
            if scope['entityId']!=entity_id:reason='entityMismatch'
            elif episode['observedAt']>as_of:reason='future'
            elif scope['expiresAt'] is not None and scope['expiresAt']<=as_of:reason='expired'
            elif any(r['sourceId'] not in refs for r in episode['sourceRefs']):reason='sourceUnavailable'
            elif any(any(refs[r['sourceId']][k]!=r[k] for k in ('sourceVersion','sourceSha256')) for r in episode['sourceRefs']):reason='sourceChanged'
            else:
                eligible+=1
                score=len(set(query_topics)&set(scope['topics']))
                if score:candidates.append((score,episode))
                else:reason='noTopic'
            if reason:decisions[eid]=reason
        candidates.sort(key=lambda r:r[1]['episodeId'])
        candidates.sort(key=lambda r:r[1]['observedAt'],reverse=True)
        candidates.sort(key=lambda r:r[0],reverse=True)
        selected=[]
        for _,episode in candidates:
            projected={k:v for k,v in episode.items() if k!='tenantId'}
            eid=episode['episodeId']
            if len(selected)==3:decisions[eid]='rankLimit'
            elif len(encode(selected+[projected]))>4096:decisions[eid]='byteLimit'
            else:selected.append(projected);decisions[eid]='selected'
        query=dict(entityId=entity_id,topics=query_topics,asOf=as_of)
        policy=digest(dict(version=1,metadata=partition['metadata'],currentSources=partition['currentSources']))
        return dict(corpusDigest=digest(partition),policyDigest=policy,querySha256=digest(query),asOf=as_of,
            episodes=selected,resultSha256=digest(selected),resultBytes=len(encode(selected)),
            eligibleCount=eligible,candidateCount=len(candidates),
            decisions=[dict(episodeId=eid,reason=reason) for eid,reason in sorted(decisions.items())])
