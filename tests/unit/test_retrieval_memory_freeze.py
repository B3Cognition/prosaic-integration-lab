from copy import deepcopy
import pytest
from lab_runner.quality.contracts import digest
from test_retrieval_memory_runner import bundle


def test_ordered_freeze_binds_corpus_code_and_evaluation_without_live_calls():
    from lab_runner.memory.freeze import development_manifest,evaluation_manifest,verify
    b=bundle();dev=development_manifest(b['corpus'],b['historicalSources'])
    assert {'runner.py','suite.py'}<=set(dev['qualityDependencies'])
    suite={k:b[k] for k in ('version','suiteId','cases')};evaluation=evaluation_manifest(suite,dev)
    verify(b,dev,evaluation)
    changed=deepcopy(b);changed['corpus']['episodes'][0]['note']='tuned after evaluation'
    with pytest.raises(ValueError):verify(changed,dev,evaluation)
    changed=deepcopy(b);changed['cases'][0]['expected']['decision']='reject'
    with pytest.raises(ValueError):verify(changed,dev,evaluation)
    changed=deepcopy(dev);changed['proseDigest']=digest('changed')
    with pytest.raises(ValueError):verify(b,changed,evaluation)


def test_packaged_historical_corpus_is_admitted_before_evaluation_freeze():
    from importlib.resources import files
    from lab_runner.memory.corpus import Corpus
    from lab_runner.quality.contracts import decode
    root=files('lab_runner.memory').joinpath('data')
    c=Corpus(decode(root.joinpath('corpus.json').read_bytes()),decode(root.joinpath('historical-sources.json').read_bytes()))
    r=c.retrieve('alpha','orchid rollout','2026-02-01T00:00:00Z')
    ids=[e['episodeId'] for e in r['episodes']]
    assert 'orchid-prior' in ids and 'orchid-future' not in ids
    assert not any('FOREIGN-TENANT-SECRET' in e['note'] for e in r['episodes'])
