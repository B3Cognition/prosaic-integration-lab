"""Download and verify immutable release wheels; does not install or infer."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from prosaic_integration_lab.dependencies import verify_dependencies


def main():
    manifest = ROOT / 'dependencies/releases.json'
    cache = ROOT / '.cache/wheels'
    cache.mkdir(parents=True, exist_ok=True)
    for item in json.loads(manifest.read_text())['artifacts']:
        path = cache / item['filename']
        if not path.exists():
            with urllib.request.urlopen(item['url'], timeout=60) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != item['sha256']:
                raise ValueError('download checksum mismatch')
            temporary = path.with_suffix('.download')
            temporary.write_bytes(content)
            temporary.replace(path)
    verify_dependencies(manifest, cache)
    print('Verified all five released wheels')


if __name__ == '__main__':
    main()
