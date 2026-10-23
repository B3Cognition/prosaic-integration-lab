"""Curate an explicit local candidate without replacing released dependency pins."""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil

from prosaic_integration_lab.dependencies import (cache_directory, file_digest,
    sdk_manifest, verified_wheel_paths)


def curate(runtime_wheel, expected_sha, source_commit, released_manifest, released_wheels, output):
    runtime_wheel, output = Path(runtime_wheel), Path(output)
    if not re.fullmatch('[0-9a-f]{64}', expected_sha) or file_digest(runtime_wheel) != expected_sha:
        raise ValueError('runtime wheel checksum mismatch')
    if not re.fullmatch('[0-9a-f]{40}', source_commit):
        raise ValueError('exact Runtime source commit required')
    if output.exists() or output.resolve() == Path(released_manifest).resolve():
        raise ValueError('candidate output must be new; released manifests are immutable')
    data = deepcopy(sdk_manifest(released_manifest))
    sources = {p.name: p for p in verified_wheel_paths(released_manifest, released_wheels)}
    selected = next(item for item in data['artifacts'] if item['distribution'] == 'b3-prosaic-runtime')
    if runtime_wheel.name != selected['filename']:
        raise ValueError('candidate Runtime wheel identity must match the compatible SDK train')
    selected.update(sha256=expected_sha, source_commit=source_commit)
    selected.pop('url', None)
    selected.pop('checksum_url', None)
    sources[runtime_wheel.name] = runtime_wheel
    data['native_candidate'] = {'version': 1, 'origin': 'local_exact_source',
        'runtimeSourceCommit': source_commit, 'runtimeWheelSha256': expected_sha,
        'releaseQualified': False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, sort_keys=True, indent=2)
        handle.write('\n')
    cache = cache_directory(output, output.parent / 'wheels')
    cache.mkdir(parents=True)
    for item in data['artifacts']:
        shutil.copyfile(sources[item['filename']], cache / item['filename'])
    verified_wheel_paths(output, cache)
    return {'manifest': str(output.resolve()), 'wheelDirectory': str(cache.resolve()),
            'runtimeSourceCommit': source_commit, 'runtimeWheelSha256': expected_sha}
