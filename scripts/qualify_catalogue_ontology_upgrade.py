"""Run the cross-version recovery witness in an owned Lab stack."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]


def main():
    from lab_runner.stack import OwnedStack
    from lab_runner.catalogue_ontology import validate_manifest
    from prosaic_integration_lab.dependencies import manifest_digest, sdk_manifest

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--released-python', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--consumer-image', required=True)
    parser.add_argument('--postgres-version', type=int, choices=(16, 18), required=True)
    parser.add_argument('--export', type=Path, required=True)
    args = parser.parse_args()
    validate_manifest(sdk_manifest(args.manifest))
    stack = OwnedStack(postgres_major=args.postgres_version, candidate=True,
                       candidate_manifest=args.manifest, consumer_image=args.consumer_image)
    try:
        stack.start()
        stack.verify_owned()
        with tempfile.TemporaryDirectory(prefix='ontology-upgrade-') as directory:
            directory = Path(directory).resolve()
            for phase, python in (('save', args.released_python.absolute()), ('resume', sys.executable)):
                subprocess.run([str(python), '-I', str(ROOT / 'tests/catalogue_ontology_upgrade/witness.py'),
                                phase, str(directory), '--config', str(stack.secrets / 'host.json')],
                               cwd=directory, check=True, timeout=60)
    finally:
        stack.stop()
    args.export.parent.mkdir(parents=True, exist_ok=True)
    args.export.write_text(json.dumps({'status': 'passed', 'backends': ['file', 'postgres'],
        'cleanup': stack.manifest['cleanup'], 'manifest_sha256': manifest_digest(args.manifest),
        'postgres_major': args.postgres_version}, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
