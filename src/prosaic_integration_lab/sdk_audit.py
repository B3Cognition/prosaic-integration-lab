"""Audit selected distribution identities and the actual SDK import payloads."""
from email.parser import BytesParser
import hashlib
from importlib.metadata import distributions
from importlib.machinery import PathFinder
from importlib.util import cache_from_source, MAGIC_NUMBER
import marshal
from pathlib import Path
from types import CodeType
import zipfile
import sys
from .dependencies import (SDK_NAMES, MAX_ARTIFACT_BYTES,
    file_digest, manifest_digest, normalize_name, sdk_manifest,
    verified_wheel_paths)


def wheel_payloads(manifest, wheel_dir):
    """Validate wheel METADATA and produce an unambiguous installed-file map."""
    paths = verified_wheel_paths(manifest, wheel_dir)
    data = sdk_manifest(manifest)
    payloads = {}
    import_owners = {}
    for item, path in zip(data['artifacts'], paths, strict=True):
        with zipfile.ZipFile(path) as wheel:
            entries = wheel.infolist()
            if len(entries) > 10000 or sum(e.file_size for e in entries) > MAX_ARTIFACT_BYTES:
                raise ValueError('wheel payload exceeds limits')
            names = [e.filename for e in entries]
            if len(set(names)) != len(names):
                raise ValueError('duplicate wheel payload')
            for name in names:
                if ('\\' in name or name.startswith('/') or '..' in Path(name).parts or
                        any(part.endswith('.data') for part in Path(name).parts)):
                    raise ValueError('unsafe or unsupported SDK wheel payload path')
            metadata_names = [name for name in names if name.endswith('.dist-info/METADATA')]
            if len(metadata_names) != 1:
                raise ValueError('wheel METADATA cardinality mismatch')
            metadata = BytesParser().parsebytes(wheel.read(metadata_names[0]))
            if (normalize_name(metadata.get('Name', '')) != normalize_name(item['distribution']) or
                    metadata.get('Version') != item['version']):
                raise ValueError('wheel METADATA identity/version mismatch')
            files = {}
            for entry in entries:
                name = entry.filename
                if name.endswith('/') or name.endswith('/RECORD'):
                    continue
                files[name] = hashlib.sha256(wheel.read(name)).hexdigest()
                if '.dist-info' not in name:
                    if name in import_owners:
                        raise ValueError(f'conflicting shared import payload in wheels: {name}')
                    import_owners[name] = item['distribution']
            payloads[normalize_name(item['distribution'])] = (item, files)
    return payloads


def installed_family(payloads):
    """Reject old/new mixtures and foreign ownership of shared import files."""
    expected = set(payloads)
    all_sdk_names = SDK_NAMES | {'b3-' + name for name in SDK_NAMES}
    import_files = {name for _, files in payloads.values() for name in files
                    if '.dist-info' not in name}
    installed = {}
    for dist in distributions():
        name = normalize_name(dist.metadata.get('Name', ''))
        if name in all_sdk_names and name not in expected:
            raise ValueError(f'unexpected SDK distribution: {name}; use a fresh environment')
        if name in expected:
            if name in installed:
                raise ValueError(f'duplicate installed SDK distribution: {name}')
            installed[name] = dist
        elif any(str(file) in import_files for file in dist.files or ()):
            raise ValueError(f'conflicting shared import distribution: {name}')
    return installed


def verify_cached_payload(cache, sources):
    """Check executable cache code against the verified source, not its header."""
    selected = sources.get(cache)
    if selected is None:
        raise ValueError('unexpected cached import payload')
    source, expected_hash, optimization = selected
    if file_digest(source) != expected_hash:
        raise ValueError('installed release payload mismatch before cache validation')
    with cache.open('rb') as stream:
        payload = stream.read(MAX_ARTIFACT_BYTES + 1)
    if (len(payload) > MAX_ARTIFACT_BYTES or len(payload) < 16 or payload[:4] != MAGIC_NUMBER or
            int.from_bytes(payload[4:8], 'little') not in {0, 1, 3}):
        raise ValueError('invalid cached import payload')
    try:
        cached = marshal.loads(payload[16:])
        if not isinstance(cached, CodeType):
            raise ValueError('cache does not contain code')
        # co_filename is diagnostic metadata. Using it for compilation permits
        # equivalent caches generated through an environment path alias; no
        # cached code is executed. Marshal reference/interning encodings are not
        # canonical, so compare code semantics and metadata recursively instead.
        expected = compile(source.read_bytes(), cached.co_filename, 'exec',
                           dont_inherit=True, optimize=optimization)
        if not same_executable_code(cached, expected):
            raise ValueError('cache code differs from verified source')
    except (ValueError, TypeError, EOFError) as error:
        raise ValueError('modified cached import payload') from error


def same_executable_code(cached, expected):
    # Code equality compares typed constants and executable attributes, but
    # excludes diagnostic/exception-table fields on some Python versions.
    if (cached != expected or cached.co_filename != expected.co_filename or
            cached.co_linetable != expected.co_linetable or
            cached.co_exceptiontable != expected.co_exceptiontable):
        return False
    return all(not isinstance(actual, CodeType) or same_executable_code(actual, wanted)
               for actual, wanted in zip(cached.co_consts, expected.co_consts, strict=True))


def audit(manifest: Path, wheel_dir: Path, *, expected_sha=None):
    if expected_sha is not None and manifest_digest(manifest) != expected_sha:
        raise ValueError('manifest checksum mismatch')
    payloads = wheel_payloads(manifest, wheel_dir)
    installed = installed_family(payloads)
    for name, (item, files) in payloads.items():
        dist = installed.get(name)
        if dist is None or dist.version != item['version']:
            raise ValueError('installed release version mismatch')
        for filename, expected in files.items():
            target = Path(dist.locate_file(filename))
            if not target.is_file() or target.is_symlink() or file_digest(target) != expected:
                raise ValueError(f'installed release payload mismatch: {filename}')
            if filename.endswith('/__init__.py') and len(Path(filename).parts) == 2:
                module = Path(filename).parts[0]
                # Resolve without importing or executing any SDK module.
                spec = PathFinder.find_spec(module, sys.path)
                if spec is None or spec.origin is None or Path(spec.origin).resolve() != target.resolve():
                    raise ValueError(f'actual import payload mismatch: {module}')
                root = target.parent
                expected_files = {Path(dist.locate_file(filename)).resolve() for filename in files
                                  if Path(filename).parts[0] == module}
                cache_sources = {}
                for source_name, source_hash in files.items():
                    if Path(source_name).parts[0] == module and source_name.endswith('.py'):
                        source = Path(dist.locate_file(source_name))
                        for optimization in range(3):
                            cache_path = Path(cache_from_source(str(source),
                                optimization='' if optimization == 0 else str(optimization)))
                            cache_sources[cache_path] = (source, source_hash, optimization)
                for actual in root.rglob('*'):
                    if actual.is_symlink():
                        raise ValueError(f'unexpected import payload symlink: {module}')
                    if '__pycache__' in actual.relative_to(root).parts:
                        if actual.is_file():
                            verify_cached_payload(actual, cache_sources)
                        continue
                    if actual.is_symlink() or (actual.is_file() and actual.resolve() not in expected_files):
                        raise ValueError(f'unexpected import payload: {module}/{actual.relative_to(root)}')
    print('Installed release payloads match all five verified wheels')
