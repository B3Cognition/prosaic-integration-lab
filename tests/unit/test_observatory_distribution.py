import json
from pathlib import Path
import shutil

import pytest

from scripts.observatory_source_smoke import verify

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def source(tmp_path):
    shutil.copytree(ROOT/'prototypes/observatory', tmp_path/'prototypes/observatory')
    return tmp_path


def test_observatory_source_has_complete_runtime_and_verified_assets(source):
    result = verify(source)
    assert result['passed'] is True
    assert result['vendor_files'] == 23
    assert result['glb_sha256'] == '2cd4dd1b49a15204a23d80fa7b1e17cf5affb5e46643060640b196b8e73c455c'


@pytest.mark.parametrize('name', ['index.html', 'assets/runtime-core.glb',
    'assets/runtime-core.blend', 'vendor/fonts/IBM-PLEX-OFL.txt'])
def test_missing_observatory_assets_fail_source_qualification(source, name):
    (source/'prototypes/observatory'/name).unlink()
    with pytest.raises(ValueError):
        verify(source)


def test_modified_vendor_code_cannot_qualify(source):
    path = source/'prototypes/observatory/vendor/three/three.module.js'
    path.write_bytes(path.read_bytes() + b'changed')
    with pytest.raises(ValueError):
        verify(source)


def test_vendor_manifest_cannot_escape_extracted_source(source):
    path = source/'prototypes/observatory/vendor/manifest.json'
    rows = json.loads(path.read_text())
    rows[0]['path'] = '../../outside'
    path.write_text(json.dumps(rows))
    with pytest.raises(ValueError):
        verify(source)
