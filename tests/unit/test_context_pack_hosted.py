import json
from pathlib import Path
import pytest


def manifest(train):return {'artifacts':[{'distribution':name,'version':version} for name,version in train.items()]}


def test_context_pack_train_is_explicit_and_legacy_candidates_keep_their_gates():
    from lab_runner.gates import CONTEXT_PACK_TRAIN,SENT_EFFORT_TRAIN,supports_context_packs,required_modes
    assert supports_context_packs(manifest(CONTEXT_PACK_TRAIN)) is True
    assert supports_context_packs(manifest(SENT_EFFORT_TRAIN)) is False
    assert 'context-packs' in required_modes(candidate=True,manifest=manifest(CONTEXT_PACK_TRAIN))
    assert 'context-packs' not in required_modes(candidate=True,manifest=manifest(SENT_EFFORT_TRAIN))
    assert 'context-packs' in required_modes(candidate=False,manifest=manifest(CONTEXT_PACK_TRAIN))


def test_stable_context_pack_train_is_supported_and_requires_released_acceptance():
    from lab_runner.gates import supports_context_packs,required_modes,SENT_EFFORT_TRAIN
    stable={**SENT_EFFORT_TRAIN,'b3-prosaic-runtime':'0.9.19',
        'b3-prosaic-harness':'0.9.13','b3-prosaic-harness-postgres':'0.4.2'}
    assert supports_context_packs(manifest(stable))
    assert 'context-packs' in required_modes(candidate=False,manifest=manifest(stable))
    assert 'context-packs' not in required_modes(candidate=False,manifest=manifest(SENT_EFFORT_TRAIN))


def test_released_pack_execution_uses_explicit_public_manifest(tmp_path):
    from lab_runner.context_packs import context_pack_manifest
    released=tmp_path/'released.json'
    assert context_pack_manifest(candidate=False,candidate_manifest=None,released_manifest=released)==released
    candidate=tmp_path/'candidate.json'
    assert context_pack_manifest(candidate=True,candidate_manifest=candidate,released_manifest=released)==candidate
    with pytest.raises(ValueError):context_pack_manifest(candidate=True,candidate_manifest=None,released_manifest=released)
    with pytest.raises(ValueError):context_pack_manifest(candidate=False,candidate_manifest=candidate,released_manifest=released)


def test_mixed_context_pack_train_is_refused():
    from lab_runner.gates import CONTEXT_PACK_TRAIN,supports_context_packs
    with pytest.raises(ValueError):supports_context_packs(manifest({**CONTEXT_PACK_TRAIN,'b3-prosaic-harness-postgres':'0.4.1'}))


def test_context_pack_curation_is_a_distinct_explicit_train():
    from scripts.prepare_sdk_candidates import CONTEXT_PACK_EXPECTED
    assert CONTEXT_PACK_EXPECTED['B3Cognition/prosaic']=={'b3-prosaic':'0.5.0'}
    assert CONTEXT_PACK_EXPECTED['B3Cognition/prosaic-runtime']['b3-prosaic-runtime']=='0.9.19'
    assert CONTEXT_PACK_EXPECTED['B3Cognition/prosaic-harness']['b3-prosaic-harness']=='0.9.13'


def test_candidate_feature_modes_cannot_be_mixed(tmp_path):
    from scripts.prepare_sdk_candidates import curate
    with pytest.raises(ValueError,match='mutually exclusive'):
        curate([],tmp_path/'manifest.json',tmp_path/'cache',context_assembly=True,context_packs=True)


def test_released_context_pack_train_preserves_original_core_and_recorder():
    from lab_runner.gates import CONTEXT_PACK_TRAIN
    root=Path(__file__).resolve().parents[2]
    current=json.loads((root/'dependencies/releases.json').read_text())
    previous=json.loads((root/'dependencies/releases-pre-context-packs-2026-11-09.json').read_text())
    assert {a['distribution']:a['version'] for a in current['artifacts']}==CONTEXT_PACK_TRAIN
    assert (root/'dependencies/releases.json').read_bytes()==(root/'dependencies/releases-reasoning.json').read_bytes()
    for name in ('b3-prosaic','b3-prosaic-runtime-postgres'):
        assert next(a for a in current['artifacts'] if a['distribution']==name)==next(a for a in previous['artifacts'] if a['distribution']==name)
    for a in current['artifacts']:
        assert a['url'].startswith('https://files.pythonhosted.org/packages/')
        assert len(a['source_commit'])==40 and len(a['sha256'])==64
