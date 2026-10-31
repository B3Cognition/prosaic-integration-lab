"""Qualify source-archive Observatory assets without inference or graphics tools."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


REQUIRED = ('index.html', 'observatory.css', 'observatory.js', 'scene-renderer.js',
    'sample-runs.js', 'live-model.js', 'lab-connection.js', 'live-model.test.mjs',
    'lab-connection.test.mjs', 'README.md', 'VERIFICATION.md', 'vendor/manifest.json',
    'assets/runtime-core.glb', 'assets/runtime-core.blend', 'assets/runtime-core-preview.png',
    'assets/runtime-core.manifest.json', 'authoring/runtime_core.py')


def verify(source):
    root = (Path(source)/'prototypes/observatory').resolve()

    def asset(name):
        if (type(name) is not str or len(name)>256 or '\\' in name or
                PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts):
            raise ValueError('invalid Observatory asset path')
        path = root/name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('incomplete Observatory source distribution')
        return path

    for name in REQUIRED:
        asset(name)
    rows = json.loads(asset('vendor/manifest.json').read_text())
    if type(rows) is not list or not 1<=len(rows)<=256:
        raise ValueError('invalid Observatory vendor manifest')
    seen = set()
    for row in rows:
        if type(row) is not dict or type(row.get('path')) is not str:
            raise ValueError('invalid Observatory vendor manifest')
        name, digest, size = row['path'], row.get('sha256'), row.get('bytes')
        if (name in seen or type(digest) is not str or not re.fullmatch('[0-9a-f]{64}',digest)
                or type(size) is not int or not 0<size<=32*1024*1024):
            raise ValueError('invalid Observatory vendor manifest')
        seen.add(name)
        path = asset('vendor/'+name)
        if path.stat().st_size!=size or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Observatory vendor digest mismatch')
    model = asset('assets/runtime-core.glb')
    metadata = json.loads(asset('assets/runtime-core.manifest.json').read_text())
    if type(metadata) is not dict or model.stat().st_size!=metadata.get('glbBytes'):
        raise ValueError('Observatory model size mismatch')
    payload = model.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if payload[:4]!=b'glTF' or digest!=metadata.get('glbSha256'):
        raise ValueError('Observatory model digest mismatch')
    return {'passed':True, 'vendor_files':len(rows), 'glb_sha256':digest}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(verify(args.source_root),sort_keys=True))


if __name__=='__main__':
    main()
