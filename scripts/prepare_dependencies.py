"""Download and verify immutable release wheels; does not install or infer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from prosaic_integration_lab.dependencies import (MAX_ARTIFACT_BYTES, cache_directory,
    manifest_digest, sdk_manifest, verify_dependencies)


def open_download(url, deadline):
    """One anonymous API fallback for a known GitHub release gateway failure.

    The manifest and its checksum stay authoritative. No retries, alternate
    package versions, arbitrary origins or authenticated downloads are inferred.
    """
    def timeout():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError('download exceeds time limit')
        return min(30, remaining)

    try:
        return urllib.request.urlopen(url, timeout=timeout())
    except urllib.error.HTTPError as error:
        route = re.fullmatch(
            r'https://github\.com/B3Cognition/(prosaic(?:-runtime|-harness)?)/'
            r'releases/download/(v[0-9][A-Za-z0-9._-]*)/([A-Za-z0-9._-]+)', url)
        if error.code not in (502, 503, 504) or route is None:
            raise
        error.close()
    repository, tag, filename = route.groups()
    origin = 'https://api.github.com/repos/B3Cognition/' + repository
    request = urllib.request.Request(origin + '/releases/tags/' + tag,
        headers={'User-Agent': 'Prosaic-Lab-Release-Verification', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout()) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('release asset metadata exceeds size limit')
    metadata = json.loads(raw)
    if (not isinstance(metadata, dict) or metadata.get('tag_name') != tag
            or metadata.get('draft') is not False or not isinstance(metadata.get('assets'), list)):
        raise ValueError('release asset metadata mismatch')
    matches = [asset for asset in metadata['assets']
               if isinstance(asset, dict) and asset.get('name') == filename]
    if len(matches) != 1:
        raise ValueError('release asset identity mismatch')
    asset = matches[0]
    if (asset.get('browser_download_url') != url or not isinstance(asset.get('url'), str)
            or re.fullmatch(re.escape(origin) + r'/releases/assets/[0-9]+', asset['url']) is None
            or type(asset.get('size')) is not int or not 0 < asset['size'] <= MAX_ARTIFACT_BYTES):
        raise ValueError('release asset identity mismatch')
    request = urllib.request.Request(asset['url'], headers={
        'User-Agent': 'Prosaic-Lab-Release-Verification', 'Accept': 'application/octet-stream'})
    return urllib.request.urlopen(request, timeout=timeout())


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
                    with open_download(item['url'], deadline) as response:
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
