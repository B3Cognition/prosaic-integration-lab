"""Download and verify immutable release wheels; does not install or infer."""
import argparse
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from prosaic_integration_lab.dependencies import (MAX_ARTIFACT_BYTES, cache_directory,
    manifest_digest, sdk_manifest, verify_dependencies)


def prepare(manifest: Path, cache_root: Path) -> Path:
    before = manifest_digest(manifest)
    data = sdk_manifest(manifest)
    cache = cache_directory(manifest, cache_root)
    cache.mkdir(parents=True, exist_ok=True)
    for item in data['artifacts']:
        path = cache / item['filename']
        if not path.exists():
            if not isinstance(item.get('url'), str) or not item['url'].startswith('https://'):
                raise ValueError('missing immutable HTTPS artifact URL; supply explicit candidate wheels')
            digest, size = hashlib.sha256(), 0
            deadline = time.monotonic() + 120
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=cache, suffix='.download', delete=False) as target:
                    temporary = Path(target.name)
                    with urllib.request.urlopen(item['url'], timeout=30) as response:
                        read_chunk = getattr(response, 'read1', response.read)
                        while chunk := read_chunk(1024 * 1024):
                            size += len(chunk)
                            if size > MAX_ARTIFACT_BYTES:
                                raise ValueError('download exceeds size limit')
                            if time.monotonic() > deadline:
                                raise ValueError('download exceeds time limit')
                            digest.update(chunk)
                            target.write(chunk)
                    target.flush()
                    os.fsync(target.fileno())
                if digest.hexdigest() != item['sha256']:
                    raise ValueError('download checksum mismatch')
                temporary.replace(path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
    if manifest_digest(manifest) != before:
        raise ValueError('manifest changed during download')
    verify_dependencies(manifest, cache)
    return cache


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'dependencies/releases.json')
    parser.add_argument('--cache-root', type=Path, default=ROOT / '.cache/wheels')
    args = parser.parse_args()
    print('Verified all five selected wheels:', prepare(args.manifest, args.cache_root))


if __name__ == '__main__':
    main()
