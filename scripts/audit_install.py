"""Audit release identities and installed wheel payloads without private APIs."""
import hashlib
from importlib.metadata import distribution
import json
from pathlib import Path
import zipfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from prosaic_integration_lab.dependencies import verify_dependencies


def audit(manifest: Path, wheel_dir: Path, *, expected_sha=None):
    if expected_sha is not None and hashlib.sha256(manifest.read_bytes()).hexdigest() != expected_sha:
        raise ValueError('manifest checksum mismatch')
    verify_dependencies(manifest,wheel_dir)
    for item in json.loads(manifest.read_text())['artifacts']:
        installed = distribution(item['distribution'])
        if installed.version != item['version']:
            raise ValueError('installed release version mismatch')
        with zipfile.ZipFile(wheel_dir / item['filename']) as wheel:
            for name in wheel.namelist():
                if name.endswith('/') or name.endswith('/RECORD'):
                    continue
                target = Path(installed.locate_file(name))
                if not target.is_file() or hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(wheel.read(name)).digest():
                    raise ValueError(f'installed release payload mismatch: {name}')
    print('Installed release payloads match all five verified wheels')


if __name__ == '__main__':
    import sys
    audit(Path(sys.argv[1]), Path(sys.argv[2]),expected_sha=sys.argv[3] if len(sys.argv)>3 else None)
