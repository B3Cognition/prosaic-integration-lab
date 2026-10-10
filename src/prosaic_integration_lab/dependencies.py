"""Bounded verification of immutable manifest-selected artifacts."""
import hashlib
import json
from pathlib import Path
import re

MAX_MANIFEST_BYTES = 256 * 1024
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
SDK_NAMES = frozenset({'prosaic', 'prosaic-runtime', 'prosaic-runtime-postgres',
                       'prosaic-harness', 'prosaic-harness-postgres'})


def normalize_name(name: str) -> str:
    return re.sub(r'[-_.]+', '-', name).lower()


def manifest_bytes(manifest_path: Path) -> bytes:
    with Path(manifest_path).open('rb') as source:
        content = source.read(MAX_MANIFEST_BYTES + 1)
    if len(content) > MAX_MANIFEST_BYTES:
        raise ValueError('manifest exceeds size limit')
    return content


def manifest_digest(manifest_path: Path) -> str:
    return hashlib.sha256(manifest_bytes(manifest_path)).hexdigest()


def cache_directory(manifest_path: Path, cache_root: Path) -> Path:
    return Path(cache_root) / manifest_digest(manifest_path)


def read_manifest(manifest_path: Path) -> dict:
    data = json.loads(manifest_bytes(manifest_path))
    if not isinstance(data, dict) or not isinstance(data.get('artifacts'), list):
        raise ValueError('invalid artifact manifest')
    if not 1 <= len(data['artifacts']) <= 32:
        raise ValueError('invalid artifact cardinality')
    filenames, distributions = set(), set()
    for artifact in data['artifacts']:
        if not isinstance(artifact, dict):
            raise ValueError('invalid artifact entry')
        filename = artifact.get('filename')
        if (not isinstance(filename, str) or not filename or len(filename) > 255 or
                Path(filename).name != filename or '\\' in filename or
                not filename.endswith('.whl')):
            raise ValueError('invalid artifact filename')
        if filename in filenames:
            raise ValueError('duplicate artifact filename')
        filenames.add(filename)
        name = artifact.get('distribution')
        if name is not None:
            if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', name):
                raise ValueError('invalid artifact distribution')
            name = normalize_name(name)
            if name in distributions:
                raise ValueError('duplicate artifact distribution')
            distributions.add(name)
        if not isinstance(artifact.get('sha256'), str) or not re.fullmatch(r'[a-f0-9]{64}', artifact['sha256']):
            raise ValueError('invalid artifact checksum')
    return data


def sdk_manifest(manifest_path: Path) -> dict:
    """Require a complete legacy or renamed SDK family at execution boundaries."""
    from packaging.utils import parse_wheel_filename
    from packaging.version import Version
    data = read_manifest(manifest_path)
    names = {normalize_name(item.get('distribution', '')) for item in data['artifacts']}
    if names not in (SDK_NAMES, {'b3-' + name for name in SDK_NAMES}):
        raise ValueError('SDK manifest must select exactly five distributions from one family')
    for item in data['artifacts']:
        try:
            wheel_name, wheel_version, _, _ = parse_wheel_filename(item['filename'])
            version = Version(item['version'])
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError('invalid wheel identity/version') from error
        if wheel_name != normalize_name(item['distribution']) or wheel_version != version:
            raise ValueError('wheel identity/version mismatch')
    return data


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    size = 0
    with Path(path).open('rb') as source:
        while chunk := source.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_ARTIFACT_BYTES:
                raise ValueError('artifact exceeds size limit')
            digest.update(chunk)
    return digest.hexdigest()


def _verify_artifacts(data: dict, artifact_dir: Path) -> None:
    for artifact in data['artifacts']:
        filename = artifact['filename']
        path = Path(artifact_dir) / filename
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'missing artifact or unsafe symlink: {filename}')
        if file_digest(path) != artifact['sha256']:
            raise ValueError(f'artifact checksum mismatch: {filename}')


def verify_dependencies(manifest_path: Path, artifact_dir: Path) -> None:
    _verify_artifacts(read_manifest(manifest_path), artifact_dir)


def verified_wheel_paths(manifest_path: Path, artifact_dir: Path) -> tuple[Path, ...]:
    before = manifest_digest(manifest_path)
    data = read_manifest(manifest_path)
    _verify_artifacts(data, artifact_dir)
    if manifest_digest(manifest_path) != before:
        raise ValueError('manifest changed during artifact verification')
    return tuple(Path(artifact_dir) / item['filename'] for item in data['artifacts'])
