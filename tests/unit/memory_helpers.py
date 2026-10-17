from copy import deepcopy
from lab_runner.quality.contracts import digest
from lab_runner.quality.suite import load_suite


def development():
    from lab_runner.memory.corpus import Corpus
    case=deepcopy(load_suite()['cases'][0])
    case.update(tenantId='alpha',asOf='2026-02-01T00:00:00Z',entity='orchid',topics=['rollout'],goldEpisodes=['prior'])
    record={**case['records']['metrics'],'revision':1,'value':90}
    source={'tenantId':'alpha','sourceId':'metrics','sourceVersion':1,'record':record}
    episode={'episodeId':'prior','tenantId':'alpha','observedAt':'2026-01-01T00:00:00Z',
        'tags':['orchid','rollout'],'note':'Orchid previously failed. Verify current metrics and incident sources.',
        'sourceRefs':[{'sourceId':'metrics','sourceVersion':1,'sourceSha256':digest(record)}]}
    d={'version':1,'episodes':[episode]};s={'version':1,'sources':[source]}
    return case,Corpus(d,s),d,s
