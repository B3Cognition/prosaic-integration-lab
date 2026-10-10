"""Audit selected distribution identities and the actual SDK import payloads."""
import argparse
from email.parser import BytesParser
import hashlib
from importlib.metadata import distributions
from importlib.machinery import PathFinder
from pathlib import Path
import zipfile
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from prosaic_integration_lab.dependencies import (SDK_NAMES, MAX_ARTIFACT_BYTES,
    cache_directory, file_digest, manifest_digest, normalize_name, sdk_manifest,
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
                for actual in root.rglob('*'):
                    if actual.is_symlink():
                        raise ValueError(f'unexpected import payload symlink: {module}')
                    if '__pycache__' in actual.relative_to(root).parts:
                        continue
                    if actual.is_symlink() or (actual.is_file() and actual.resolve() not in expected_files):
                        raise ValueError(f'unexpected import payload: {module}/{actual.relative_to(root)}')
    print('Installed release payloads match all five verified wheels')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('legacy_manifest', nargs='?', type=Path)
    parser.add_argument('legacy_wheel_dir', nargs='?', type=Path)
    parser.add_argument('legacy_sha', nargs='?')
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--wheel-dir', type=Path)
    parser.add_argument('--expected-sha')
    args = parser.parse_args()
    manifest = args.manifest or args.legacy_manifest or ROOT / 'dependencies/releases.json'
    wheel_dir = args.wheel_dir or args.legacy_wheel_dir or cache_directory(manifest, ROOT / '.cache/wheels')
    audit(manifest, wheel_dir, expected_sha=args.expected_sha or args.legacy_sha)


if __name__ == '__main__':
    main()
