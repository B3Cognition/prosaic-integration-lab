"""Install only exact verified wheels from one complete SDK manifest."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from prosaic_integration_lab.dependencies import cache_directory, manifest_digest, verified_wheel_paths
from audit_install import installed_family, wheel_payloads


def install(manifest: Path, wheel_dir: Path, *, expected_sha=None):
    before = manifest_digest(manifest)
    if expected_sha is not None and before != expected_sha:
        raise ValueError('manifest checksum mismatch')
    paths = verified_wheel_paths(manifest, wheel_dir)
    installed_family(wheel_payloads(manifest, wheel_dir))
    if manifest_digest(manifest) != before:
        raise ValueError('manifest changed during verification')
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--force-reinstall',
                    *(str(path) for path in paths)], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'dependencies/releases.json')
    parser.add_argument('--wheel-dir', type=Path)
    parser.add_argument('--expected-sha')
    args = parser.parse_args()
    install(args.manifest, args.wheel_dir or cache_directory(args.manifest, ROOT / '.cache/wheels'),
            expected_sha=args.expected_sha)


if __name__ == '__main__':
    main()
