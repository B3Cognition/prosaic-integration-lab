"""Build an immutable consumer from an isolated public context and exact wheels."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from prosaic_integration_lab.dependencies import (cache_directory, manifest_bytes,
    manifest_digest, sdk_manifest, verified_wheel_paths)
from audit_install import wheel_payloads


def build(manifest: Path, wheel_dir: Path, tag: str, dependency_mode: str) -> str:
    if dependency_mode not in {'released', 'candidate'}:
        raise ValueError('invalid dependency mode')
    content = manifest_bytes(manifest)
    digest = hashlib.sha256(content).hexdigest()
    sdk_manifest(manifest)
    paths = verified_wheel_paths(manifest, wheel_dir)
    wheel_payloads(manifest, wheel_dir)
    if manifest_digest(manifest) != digest:
        raise ValueError('manifest changed during verification')
    with tempfile.TemporaryDirectory(prefix='prosaic-lab-build-') as temporary:
        context = Path(temporary)
        # Only public runtime inputs enter the context; caches, runs, credentials,
        # research and the Git checkout cannot be uploaded to the engine.
        public_directories = ('src', 'scripts', 'lab_runner', 'assets', 'containers')
        listing = subprocess.run(['git', 'ls-files', '-z', '--', *public_directories,
                                  'dependencies/requirements.lock'], cwd=ROOT,
                                 capture_output=True, text=True, check=True, timeout=15)
        # These explicitly named new helpers may not yet be committed during
        # local development; all other inputs must already be tracked.
        public_files = set(listing.stdout.split('\0')) - {''}
        public_files.update({'scripts/install_dependencies.py', 'scripts/build_consumer.py',
                             'scripts/audit_install.py'})
        for filename in sorted(public_files):
            relative = Path(filename)
            if (relative.is_absolute() or '..' in relative.parts or
                    (relative.parts[0] not in public_directories and filename != 'dependencies/requirements.lock')):
                raise ValueError('unsafe public build input')
            if '__pycache__' in relative.parts or relative.suffix == '.pyc':
                continue
            source = ROOT / relative
            if source.is_symlink() or any(parent.is_symlink() for parent in source.parents if parent != ROOT):
                raise ValueError('public build inputs must not contain symlinks')
            target_file = context / relative
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target_file)
        (context / 'dependencies').mkdir(exist_ok=True)
        snapshot = context / 'dependencies/releases.json'
        snapshot.write_bytes(content)
        target = context / '.cache/wheels' / digest
        target.mkdir(parents=True)
        for path in paths:
            shutil.copyfile(path, target / path.name)
        verified_wheel_paths(snapshot, target)
        if manifest_digest(manifest) != digest:
            raise ValueError('manifest changed during context snapshot')
        dockerfile = 'containers/Candidate.Dockerfile' if dependency_mode == 'candidate' else 'containers/Dockerfile'
        iidfile = context / 'image-id'
        subprocess.run(['docker', 'build', '-f', str(context / dockerfile), '--tag', tag,
                        '--build-arg', 'SDK_MANIFEST_SHA256=' + digest,
                        '--iidfile', str(iidfile), str(context)], check=True, timeout=900)
        if manifest_digest(manifest) != digest:
            raise ValueError('manifest changed during image build')
        identity = iidfile.read_text().strip()
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', identity):
            raise ValueError('engine did not emit an immutable image ID')
        return identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'dependencies/releases.json')
    parser.add_argument('--wheel-dir', type=Path)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--dependency-mode', choices=['released', 'candidate'], default='released')
    args = parser.parse_args()
    if args.dependency_mode == 'candidate' and args.manifest == ROOT / 'dependencies/releases.json':
        parser.error('candidate builds require an explicit candidate manifest')
    # Fail a missing/unresponsive engine boundedly, before any build mutation.
    subprocess.run(['docker', 'info'], check=True, capture_output=True, timeout=15)
    print(build(args.manifest, args.wheel_dir or cache_directory(args.manifest, ROOT / '.cache/wheels'),
                args.tag, args.dependency_mode))


if __name__ == '__main__':
    main()
