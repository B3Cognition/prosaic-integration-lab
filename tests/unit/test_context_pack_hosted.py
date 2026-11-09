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
    assert 'context-packs' not in required_modes(candidate=False,manifest=manifest(CONTEXT_PACK_TRAIN))


def test_mixed_context_pack_train_is_refused():
    from lab_runner.gates import CONTEXT_PACK_TRAIN,supports_context_packs
    with pytest.raises(ValueError):supports_context_packs(manifest({**CONTEXT_PACK_TRAIN,'b3-prosaic-harness-postgres':'0.4.1'}))


def test_context_pack_curation_is_a_distinct_explicit_train():
    from scripts.prepare_sdk_candidates import CONTEXT_PACK_EXPECTED
    assert CONTEXT_PACK_EXPECTED['B3Cognition/prosaic']=={'b3-prosaic':'0.5.0'}
    assert CONTEXT_PACK_EXPECTED['B3Cognition/prosaic-runtime']['b3-prosaic-runtime']=='0.9.19.dev0'
    assert CONTEXT_PACK_EXPECTED['B3Cognition/prosaic-harness']['b3-prosaic-harness']=='0.9.13.dev0'


def test_candidate_feature_modes_cannot_be_mixed(tmp_path):
    from scripts.prepare_sdk_candidates import curate
    with pytest.raises(ValueError,match='mutually exclusive'):
        curate([],tmp_path/'manifest.json',tmp_path/'cache',context_assembly=True,context_packs=True)
