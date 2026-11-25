"""Compatibility CLI for the packaged SDK payload auditor."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from prosaic_integration_lab.dependencies import cache_directory
from prosaic_integration_lab.sdk_audit import audit, installed_family, wheel_payloads

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
