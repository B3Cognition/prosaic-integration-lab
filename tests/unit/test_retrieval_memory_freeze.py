from copy import deepcopy
import pytest
from lab_runner.quality.contracts import digest
from test_retrieval_memory_runner import bundle


def test_ordered_freeze_binds_corpus_code_and_evaluation_without_live_calls():
    from lab_runner.memory.freeze import development_manifest,evaluation_manifest,verify
    b=bundle();dev=development_manifest(b['corpus'],b['historicalSources'])
    assert {'runner.py','suite.py','token_admission.py'}<=set(dev['qualityDependencies'])
    suite={k:b[k] for k in ('version','suiteId','cases')};evaluation=evaluation_manifest(suite,dev)
    verify(b,dev,evaluation)
    changed=deepcopy(b);changed['corpus']['episodes'][0]['note']='tuned after evaluation'
    with pytest.raises(ValueError):verify(changed,dev,evaluation)
    changed=deepcopy(b);changed['cases'][0]['expected']['decision']='reject'
    with pytest.raises(ValueError):verify(changed,dev,evaluation)
    changed=deepcopy(dev);changed['proseDigest']=digest('changed')
    with pytest.raises(ValueError):verify(b,changed,evaluation)


def test_archived_sdk_profile_tampering_invalidates_current_development_freeze(tmp_path,monkeypatch):
    import shutil
    import lab_runner.memory.freeze as freeze
    original=freeze.files
    quality=tmp_path/'quality'
    shutil.copytree(original('lab_runner.quality'),quality,ignore=shutil.ignore_patterns('__pycache__'))
    monkeypatch.setattr(freeze,'files',lambda package:quality if package=='lab_runner.quality' else original(package))
    b=bundle();dev=freeze.development_manifest(b['corpus'],b['historicalSources'])
    evaluation=freeze.evaluation_manifest({k:b[k] for k in ('version','suiteId','cases')},dev)
    freeze.verify(b,dev,evaluation)
    archived=quality/'data/sdk-provenance-pre-unified.json'
    archived.write_bytes(archived.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='development freeze drift'):
        freeze.verify(b,dev,evaluation)


def test_runtime_release_preserves_archived_memory_lineage_and_all_benchmark_inputs():
    import hashlib
    from importlib.resources import files
    from lab_runner.quality.contracts import decode
    from lab_runner.memory.freeze import verify
    root=files('lab_runner.memory').joinpath('data')
    old_dev_bytes=root.joinpath('development-freeze-runtime-0.9.7.json').read_bytes()
    old_eval_bytes=root.joinpath('evaluation-freeze-runtime-0.9.7.json').read_bytes()
    assert hashlib.sha256(old_dev_bytes).hexdigest()=='eeee1f1d10f060bebd987af0d45187c89ec8af257aba478b86f3ac41bcf72868'
    assert hashlib.sha256(old_eval_bytes).hexdigest()=='fe610c6b99e72b975a10b676284ff17f136dab11f3bb4f4f653d4639219044cd'
    old_dev,old_eval=decode(old_dev_bytes),decode(old_eval_bytes)
    dev=decode(root.joinpath('development-freeze.json').read_bytes())
    evaluation=decode(root.joinpath('evaluation-freeze.json').read_bytes())
    assert old_eval['developmentFreezeDigest']==digest(old_dev)
    assert evaluation['developmentFreezeDigest']==digest(dev)!=digest(old_dev)
    assert evaluation['suiteDigest']==old_eval['suiteDigest']
    assert set(dev['implementation'])==set(old_dev['implementation'])
    assert {k for k in dev['implementation'] if dev['implementation'][k]!=old_dev['implementation'][k]}=={'freeze.py'}
    changed={'sdk_provenance.py','suite.py','data/sdk-provenance-public.json','data/sdk-provenance-pre-unified.json'}
    assert set(dev['qualityDependencies'])==set(old_dev['qualityDependencies'])|{'data/sdk-provenance-pre-unified.json'}
    assert {k for k in dev['qualityDependencies'] if dev['qualityDependencies'][k]!=old_dev['qualityDependencies'].get(k)}==changed
    assert {k:v for k,v in dev.items() if k not in ('implementation','qualityDependencies')}=={
        k:v for k,v in old_dev.items() if k not in ('implementation','qualityDependencies')}
    frozen=decode(root.joinpath('retrieval-memory-v1.json').read_bytes())
    frozen.update(corpus=decode(root.joinpath('corpus.json').read_bytes()),
        historicalSources=decode(root.joinpath('historical-sources.json').read_bytes()))
    verify(frozen,dev,evaluation)


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


def test_new_history_preserves_released_evidence_byte_values():
    from importlib.resources import files
    from lab_runner.quality.contracts import decode
    root=files('lab_runner.memory').joinpath('data')
    episodes=decode(root.joinpath('corpus.json').read_bytes())['episodes']
    sources=decode(root.joinpath('historical-sources.json').read_bytes())['sources']
    assert digest(episodes[:26])=='4f7a2b0b9d0431bc3a0a07536226e8699c7e6f1656138a6bb34d2651f22cfcc6'
    assert digest(sources[:48])=='51c3eb27fb69ee393b16b08137b136d4fcdd5c666a9185dd348ec68c639ca24d'
    assert len(episodes)==38 and len(sources)==72
