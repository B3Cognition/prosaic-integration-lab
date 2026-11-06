"""Regressions for the candidate wheel builder's cache handling; offline, no build or network."""

from importlib.metadata import PackageNotFoundError
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def builder():
    sys.path.insert(0, str(ROOT / 'scripts'))
    try:
        import build_rule_admission_candidates as module
    finally:
        sys.path.remove(str(ROOT / 'scripts'))
    return module


def wheel(tmp_path, content=b'candidate wheel bytes'):
    from prosaic_integration_lab.dependencies import file_digest

    path = tmp_path / 'built' / 'b3_prosaic-0.4.1-py3-none-any.whl'
    path.parent.mkdir()
    path.write_bytes(content)
    return path, {'filename': path.name, 'sha256': file_digest(path)}


# Bug 7: a dangling symlink in the cache passed `exists()` and copyfile wrote through it.
def test_place_refuses_a_dangling_symlink_and_never_writes_through_it(builder, tmp_path):
    built, item = wheel(tmp_path)
    cache = tmp_path / 'cache'
    cache.mkdir()
    outside = tmp_path / 'outside.whl'
    (cache / item['filename']).symlink_to(outside)
    with pytest.raises(ValueError, match='symlink'):
        builder.place(built, cache, item)
    assert not outside.exists()


def test_place_refuses_a_live_symlink_even_to_identical_bytes(builder, tmp_path):
    built, item = wheel(tmp_path)
    cache = tmp_path / 'cache'
    cache.mkdir()
    (cache / item['filename']).symlink_to(built)
    with pytest.raises(ValueError, match='symlink'):
        builder.place(built, cache, item)


def test_place_refuses_bytes_that_differ_from_the_manifest(builder, tmp_path):
    built, item = wheel(tmp_path)
    with pytest.raises(ValueError, match='differ'):
        builder.place(built, tmp_path / 'cache', {**item, 'sha256': '0' * 64})
    assert not (tmp_path / 'cache' / item['filename']).exists()


def test_place_refuses_a_different_cached_wheel_and_accepts_an_identical_one(builder, tmp_path):
    built, item = wheel(tmp_path)
    cache = tmp_path / 'cache'
    cache.mkdir()
    (cache / item['filename']).write_bytes(b'something else')
    with pytest.raises(ValueError, match='differs'):
        builder.place(built, cache, item)
    (cache / item['filename']).unlink()
    assert builder.place(built, cache, item) == cache / item['filename']
    assert builder.place(built, cache, item) == cache / item['filename']
    assert (cache / item['filename']).read_bytes() == built.read_bytes()


# Bug 9: a missing build backend escaped as a raw PackageNotFoundError traceback.
def test_missing_build_backend_is_a_clear_refusal_before_any_fetch(builder, tmp_path, monkeypatch):
    def missing(name):
        raise PackageNotFoundError(name)

    monkeypatch.setattr(builder, 'version', missing)
    monkeypatch.setattr(builder, 'run', lambda *args, **kwargs: pytest.fail('fetched before checking the backend'))
    with pytest.raises(ValueError, match='rule-admission-build.lock'):
        builder.build({'source_commit': '0' * 40, 'source_repository': 'B3Cognition/prosaic'}, tmp_path)
