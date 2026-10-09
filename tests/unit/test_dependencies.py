import hashlib
import json
from pathlib import Path

import pytest

from prosaic_integration_lab.dependencies import verify_dependencies


def fixture(tmp_path):
    artifact = tmp_path / 'fixture.whl'
    artifact.write_bytes(b'verified release artifact')
    manifest = tmp_path / 'releases.json'
    manifest.write_text(json.dumps({'artifacts': [{
        'filename': artifact.name,
        'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'url': 'https://github.com/example/project/releases/download/v1/fixture.whl',
    }]}))
    return artifact, manifest


def test_valid_artifact_is_accepted(tmp_path):
    _, manifest = fixture(tmp_path)
    verify_dependencies(manifest, tmp_path)


def test_modified_artifact_is_rejected(tmp_path):
    artifact, manifest = fixture(tmp_path)
    artifact.write_bytes(b'changed bytes')
    with pytest.raises(ValueError, match='checksum'):
        verify_dependencies(manifest, tmp_path)


def test_missing_artifact_is_rejected(tmp_path):
    artifact, manifest = fixture(tmp_path)
    artifact.unlink()
    with pytest.raises(ValueError, match='missing'):
        verify_dependencies(manifest, tmp_path)


@pytest.mark.parametrize('filename', ['../escape.whl', '/tmp/escape.whl'])
def test_artifact_path_cannot_escape_cache(tmp_path, filename):
    _, manifest = fixture(tmp_path)
    data = json.loads(manifest.read_text())
    data['artifacts'][0]['filename'] = filename
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='filename'):
        verify_dependencies(manifest, tmp_path)
