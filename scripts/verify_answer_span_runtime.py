"""Require exact qualified candidate wheel members and immutable source identity."""
import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify_wheel(path, spec):
    required = {'version','repository','sourceCommit','sourceTree','distribution',
                'packageVersion','originalWheelSha256','members','publicationAuthorized'}
    if (set(spec) != required or type(spec['version']) is not int or spec['version'] != 1
            or spec['repository'] != 'B3Cognition/prosaic-runtime'
            or spec['distribution'] != 'b3-prosaic-runtime'
            or spec['packageVersion'] != '0.9.8+jsonschema.3'
            or spec['publicationAuthorized'] is not False
            or any(not re.fullmatch('[a-f0-9]{40}',spec[k]) for k in ('sourceCommit','sourceTree'))
            or not re.fullmatch('[a-f0-9]{64}',spec['originalWheelSha256'])):
        raise ValueError('invalid exact unpublished Runtime candidate specification')
    with zipfile.ZipFile(path) as z:
        entries = [item for item in z.infolist() if not item.is_dir()]
        names = [item.filename for item in entries]
        if (len(names) != len(set(names)) or set(names) != set(spec['members']) or any(
                PurePosixPath(item.filename).is_absolute() or '..' in PurePosixPath(item.filename).parts
                or '\\' in item.filename or stat.S_ISLNK(item.external_attr >> 16) for item in entries)):
            raise ValueError('candidate wheel inventory differs')
        for name in names:
            if hashlib.sha256(z.read(name)).hexdigest() != spec['members'][name]:
                raise ValueError('candidate wheel member checksum differs')
        metadata = [name for name in names if name.endswith('.dist-info/METADATA')]
        if len(metadata) != 1:
            raise ValueError('candidate distribution identity missing')
        identity = BytesParser().parsebytes(z.read(metadata[0]))
        if identity['Name'] != spec['distribution'] or identity['Version'] != spec['packageVersion']:
            raise ValueError('candidate distribution identity differs')
    return dict(qualified=True,sourceCommit=spec['sourceCommit'],sourceTree=spec['sourceTree'],
        packageVersion=spec['packageVersion'],verifiedMembers=len(names),
        wheelSha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        originalWheelSha256=spec['originalWheelSha256'],publicationAuthorized=False)


def verify_source(source, spec):
    for reference, expected in [('HEAD',spec['sourceCommit']),('HEAD^{tree}',spec['sourceTree'])]:
        actual = subprocess.check_output(['git','-C',str(source),'rev-parse',reference],text=True).strip()
        if actual != expected:
            raise ValueError('candidate source identity differs')
    for name, expected in spec['members'].items():
        if name.startswith('prosaic_runtime/'):
            path = Path(source)/'src'/name
            if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('candidate source payload differs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, default=ROOT/'dependencies/answer-span-runtime.json')
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--export', type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    result = verify_wheel(args.wheel, spec)
    if args.source: verify_source(args.source, spec)
    args.export.parent.mkdir(parents=True, exist_ok=True)
    with args.export.open('x') as f: json.dump(result, f, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
