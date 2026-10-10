"""Historical upgrade inputs and retained host assets, never fake receipts."""
import copy
import json
from pathlib import Path

import pytest


def test_baseline_image_manifest_mismatch_precedes_any_resource_allocation():
    from lab_runner.legacy_upgrade import BASELINE_COMMIT, baseline_digest, validate_baseline
    digest=baseline_digest()
    image={'Id':'sha256:'+'1'*64,'Config':{'Labels':{
        'io.prosaic.lab.baseline-source':BASELINE_COMMIT,
        'io.prosaic.lab.release-manifest':digest,
        'io.prosaic.lab.dependency-mode':'released'}}}
    validate_baseline(image,Path('dependencies/releases-lab-0.2.0.json'))
    for field in ('io.prosaic.lab.baseline-source','io.prosaic.lab.release-manifest','io.prosaic.lab.dependency-mode'):
        bad=copy.deepcopy(image);bad['Config']['Labels'][field]='wrong'
        with pytest.raises(ValueError):validate_baseline(bad,Path('dependencies/releases-lab-0.2.0.json'))


def test_historical_manifest_changed_bytes_are_never_baseline(tmp_path):
    from lab_runner.legacy_upgrade import validate_manifest
    manifest=tmp_path/'baseline.json'
    data=json.loads(Path('dependencies/releases-lab-0.2.0.json').read_text())
    data['artifacts'][0]['sha256']='1'*64
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError):validate_manifest(manifest)


def test_retained_legacy_assets_use_original_hash_and_reject_altered_directory(tmp_path):
    import shutil
    from prosaic_integration_lab.execution import retained_workflows
    from prosaic_integration_lab.config import assets_hash
    retained=tmp_path/'retained';shutil.copytree(Path('assets'),retained)
    identity=assets_hash(retained)
    registry=retained_workflows({'legacy_bundles':{identity:{'assets':str(retained)}}})
    assert registry[identity]['synthetic'].definition['start']=='author'
    (retained/'runtime.yml').write_text('altered')
    with pytest.raises(ValueError):retained_workflows({'legacy_bundles':{identity:{'assets':str(retained)}}})


def test_retained_historical_assets_match_exact_released_snapshot():
    from prosaic_integration_lab.config import assets_hash
    assert assets_hash(Path('assets/legacy-0.2.0'))=='ab357d93f93026d1563b70915320a1ab7ac1e8ae1eca76b1743c7cf3c9a36614'


def test_upgrade_fixture_cannot_export_private_snapshots():
    from lab_runner.legacy_upgrade import public_summary
    result=public_summary({'runs':[{'run_id':'PRIVATE','receipt':'SECRET'}]*5,
        'baseline_manifest_sha256':'a'*64,'baseline_source':'b'*40,'baseline_image':'sha256:'+'c'*64,
        'baseline_payload_audit':'verified','migration':'v2-to-v3','private_assets':'TOKEN'})
    assert result['legacy_fixture_count']==5
    assert not any(value in json.dumps(result) for value in ('PRIVATE','SECRET','TOKEN'))
