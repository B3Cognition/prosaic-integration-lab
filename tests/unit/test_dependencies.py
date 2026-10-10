import hashlib
import json
from pathlib import Path

import pytest

from prosaic_integration_lab.dependencies import cache_directory, verified_wheel_paths, verify_dependencies


def test_historical_neighbor_is_not_an_install_input(tmp_path):
    root = tmp_path / 'wheels'
    manifest = tmp_path / 'releases.json'
    payload = b'active verified bytes'
    manifest.write_text(json.dumps({'artifacts': [{
        'distribution': 'b3-prosaic', 'version': '0.4.0',
        'filename': 'b3_prosaic-0.4.0-py3-none-any.whl',
        'sha256': hashlib.sha256(payload).hexdigest()}]}))
    cache = cache_directory(manifest, root)
    cache.mkdir(parents=True)
    active = cache / 'b3_prosaic-0.4.0-py3-none-any.whl'
    active.write_bytes(payload)
    (root / 'prosaic-0.3.1-py3-none-any.whl').write_bytes(b'historical')
    assert verified_wheel_paths(manifest, cache) == (active,)
    assert cache.name == hashlib.sha256(manifest.read_bytes()).hexdigest()


@pytest.mark.parametrize('field,value', [
    ('filename', '../escape.whl'), ('filename', 'sub\\\\escape.whl'),
    ('filename', 'x' * 256 + '.whl'), ('sha256', 'bad'),
])
def test_rejects_invalid_identity_before_opening_payload(tmp_path, field, value):
    _, manifest = fixture(tmp_path)
    data = json.loads(manifest.read_text())
    data['artifacts'][0][field] = value
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        verify_dependencies(manifest, tmp_path)


@pytest.mark.parametrize('duplicate_filename', [True, False])
def test_duplicate_artifact_identity_is_rejected(tmp_path, duplicate_filename):
    _, manifest = fixture(tmp_path)
    data = json.loads(manifest.read_text())
    item = data['artifacts'][0]
    item['distribution'] = 'fixture'
    item['version'] = '1.0'
    other = {**item, 'sha256': '0' * 64}
    if not duplicate_filename:
        other['filename'] = 'other.whl'
        other['distribution'] = 'Fixture'
    data['artifacts'].append(other)
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='duplicate'):
        verify_dependencies(manifest, tmp_path)


def test_same_version_conflicting_payloads_have_separate_caches(tmp_path):
    _, manifest = fixture(tmp_path)
    first = cache_directory(manifest, tmp_path)
    data = json.loads(manifest.read_text())
    data['artifacts'][0]['sha256'] = '0' * 64
    manifest.write_text(json.dumps(data))
    assert cache_directory(manifest, tmp_path) != first


def test_manifest_change_cannot_return_an_unverified_wheel(tmp_path, monkeypatch):
    from prosaic_integration_lab import dependencies
    artifact, manifest = fixture(tmp_path)
    original = dependencies.file_digest
    def concurrent_change(path):
        checksum = original(path)
        data = json.loads(manifest.read_text())
        data['artifacts'][0]['filename'] = 'unverified.whl'
        manifest.write_text(json.dumps(data))
        return checksum
    monkeypatch.setattr(dependencies, 'file_digest', concurrent_change)
    with pytest.raises(ValueError, match='manifest changed'):
        verified_wheel_paths(manifest, tmp_path)


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
