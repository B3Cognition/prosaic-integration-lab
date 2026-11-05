"""Rebuild the rule-admission candidate wheels from exact upstream commits.

The candidate manifest records unreleased Runtime and Harness wheels built from
``git archive`` of an exact 40-character commit. This script fetches only that
commit, builds it with the hashed backend in ``rule-admission-build.lock``
(no build isolation, ``SOURCE_DATE_EPOCH`` set to the commit time) and refuses
any wheel whose SHA256 differs from the manifest. Verified wheels are copied
into the manifest's wheel cache, where ``prepare_dependencies.py`` expects
explicit candidate wheels. Released manifests are never read or edited.

``--report`` builds and prints digests without verifying or caching; use it
only when deliberately re-pinning the manifest to new commits.
"""

import argparse
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from prosaic_integration_lab.dependencies import cache_directory, file_digest, sdk_manifest  # noqa: E402

MANIFEST = ROOT / 'dependencies/rule-admission-candidate.json'
QUALIFICATION = 'local-offline-candidate; not a published release'
BACKEND = ('setuptools', '80.9.0')
REPOSITORIES = {'b3-prosaic-runtime': 'B3Cognition/prosaic-runtime',
    'b3-prosaic-harness': 'B3Cognition/prosaic-harness'}
RELEASED = {ROOT / 'dependencies/releases.json', ROOT / 'dependencies/releases-reasoning.json'}


def candidates(manifest):
    """Return Runtime and Harness candidates; Core is the released 0.5.0 wheel."""
    if Path(manifest).resolve() in {path.resolve() for path in RELEASED}:
        raise ValueError('candidate builds never use a release manifest')
    data = sdk_manifest(manifest)
    selected = [item for item in data['artifacts'] if item.get('qualification') == QUALIFICATION]
    if len(selected) != 2 or {item['distribution'] for item in selected} != set(REPOSITORIES):
        raise ValueError('candidate manifest must build exactly Runtime and Harness')
    for item in selected:
        if (
            item.get('source_repository') != REPOSITORIES[item['distribution']]
            or not re.fullmatch('[0-9a-f]{40}', item.get('source_commit', ''))
            or 'url' in item
        ):
            raise ValueError('candidate entry requires its repository, an exact commit and no download URL')
    return selected


def run(*command, cwd=None, env=None):
    return subprocess.run(command, cwd=cwd, env=env, check=True, capture_output=True, text=True, timeout=600).stdout


def build(item, work, *, local_repository=None):
    """Fetch one exact commit, archive it and build its wheel; returns the wheel path."""
    try:
        installed = version(BACKEND[0])
    except PackageNotFoundError:
        installed = None
    if installed != BACKEND[1]:
        raise ValueError('install dependencies/rule-admission-build.lock before building candidates')
    commit = item['source_commit']
    repository = work / 'repository.git'
    run('git', 'init', '--quiet', '--bare', str(repository))
    if local_repository is None:
        url = f'https://github.com/{item["source_repository"]}'
    else:
        checkout = Path(local_repository)
        if not checkout.is_absolute() or not checkout.is_dir():
            raise ValueError('local repository must be an absolute Git checkout')
        url = str(checkout)
    run('git', '-C', str(repository), 'fetch', '--quiet', '--depth', '1', url, commit)
    if run('git', '-C', str(repository), 'rev-parse', 'FETCH_HEAD').strip() != commit:
        raise ValueError('fetched commit differs from the manifest')
    epoch = run('git', '-C', str(repository), 'show', '-s', '--format=%ct', commit).strip()
    archive, source, output = work / 'source.tar', work / 'source', work / 'dist'
    run('git', '-C', str(repository), 'archive', '--format=tar', '--output', str(archive), commit)
    with tarfile.open(archive) as bundle:
        bundle.extractall(source, filter='data')
    env = {**os.environ, 'SOURCE_DATE_EPOCH': epoch, 'PYTHONHASHSEED': '0'}
    run(sys.executable, '-m', 'build', '--wheel', '--no-isolation', '--outdir', str(output), str(source), env=env)
    wheels = list(output.glob('*.whl'))
    if [wheel.name for wheel in wheels] != [item['filename']]:
        raise ValueError('candidate build produced an unexpected wheel')
    return wheels[0]


def place(wheel, cache, item):
    """Copy a verified wheel into the cache; never through a symlink, never over different bytes."""
    digest = file_digest(wheel)
    if digest != item['sha256']:
        raise ValueError(f'candidate wheel bytes differ from the manifest: {item["filename"]}')
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / item['filename']
    # is_symlink() first: a dangling link reports exists() False and copyfile would write through it.
    if target.is_symlink():
        raise ValueError(f'refusing a symlink in the candidate cache: {item["filename"]}')
    if target.exists():
        if not target.is_file() or file_digest(target) != digest:
            raise ValueError(f'cached candidate differs from the manifest: {item["filename"]}')
        return target
    with tempfile.NamedTemporaryFile(dir=cache, prefix='.candidate-', suffix='.partial', delete=False) as handle:
        partial = Path(handle.name)
        with Path(wheel).open('rb') as source:
            shutil.copyfileobj(source, handle)
    try:
        os.replace(partial, target)  # Renames over the path itself; never follows a link created meanwhile.
    finally:
        partial.unlink(missing_ok=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--cache-root', type=Path, default=ROOT / '.cache/wheels')
    parser.add_argument('--report', action='store_true', help='print digests; do not verify or cache')
    parser.add_argument('--local-repository', action='append', default=[], metavar='REPOSITORY=PATH',
        help='explicit local Git source for an unpublished exact commit; hashes are still mandatory')
    args = parser.parse_args()
    selected = candidates(args.manifest)
    local = {}
    for value in args.local_repository:
        name, separator, path = value.partition('=')
        if not separator or name not in REPOSITORIES.values() or name in local:
            raise ValueError('local repository must name one distinct candidate repository')
        local[name] = path
    cache = cache_directory(args.manifest, args.cache_root)
    report = []
    for item in selected:
        with tempfile.TemporaryDirectory(prefix='rule-candidate-') as temporary:
            wheel = build(item, Path(temporary), local_repository=local.get(item['source_repository']))
            digest = file_digest(wheel)
            report.append({'distribution': item['distribution'], 'filename': wheel.name, 'sha256': digest})
            if not args.report:
                place(wheel, cache, item)
    print(json.dumps({'verified': not args.report, 'cache': str(cache), 'wheels': report}, indent=2))


if __name__ == '__main__':
    main()
