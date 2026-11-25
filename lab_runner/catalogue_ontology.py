"""Validate the exact candidate and released ontology SDK families."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from prosaic_integration_lab.catalogue_ontology import TRAIN


KIND = 'catalogue-ontology'
PUBLIC_PROFILE = Path(__file__).with_name('data') / 'catalogue-ontology-public-0.5.1-0.9.18.json'
RETAINED = {
    'b3-prosaic-runtime': ('48c10ac9aeb18bd06f53015df0624b35d5254646',
        '5caab59f6d0ffd14299ee0840dd5f9b58b4e4f4a1b724ff6e3e2fa1699f08fd8'),
    'b3-prosaic-runtime-postgres': ('a59621c5f30d766d1217b37df777d3876075dc34',
        '5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'),
    'b3-prosaic-harness-postgres': ('5cf6b08e3f181bfb368b24afbe1eadf9911b4504',
        '6a64d3276850582fbf24d6a6698d83bd0adb861bd9189f096733a3f1d28b03cc'),
}
PACKAGES = {'core': 'b3-prosaic', 'harness': 'b3-prosaic-harness'}
CASES = sorted((
    'test_exact_installed_ontology_sdk',
    'test_projection_uses_existing_visibility_and_owns_the_result',
    'test_attachment_rejects_unknown_aliases[agents]',
    'test_attachment_rejects_unknown_aliases[tools]',
    'test_delegate_aliases_keep_the_existing_admission_boundary',
    'test_ontology_cannot_be_authored_and_does_not_change_saved_identity',
))


def _hash(document):
    return hashlib.sha256((json.dumps(document, sort_keys=True, indent=2, allow_nan=False)
                           + '\n').encode()).hexdigest()


def _check(condition):
    if not condition:
        raise ValueError('invalid catalogue ontology candidate evidence')


def _hex(value, size=64):
    return type(value) is str and re.fullmatch(rf'[0-9a-f]{{{size}}}', value) is not None


def _run(value):
    return type(value) is str and re.fullmatch(r'[1-9][0-9]*', value) is not None


def package_binding(receipt, sdk):
    name = PACKAGES[sdk]
    expected = {name: TRAIN[name]}
    if sdk == 'harness':
        expected['b3-prosaic-harness-postgres'] = TRAIN['b3-prosaic-harness-postgres']
    prefix = name.replace('-', '_') + '-' + TRAIN[name]
    names = {distribution.replace('-', '_') + '-' + version + suffix
             for distribution, version in expected.items() for suffix in ('-py3-none-any.whl', '.tar.gz')}
    files = receipt['artifacts']
    _check(type(receipt['version']) is int and receipt['version'] == 1
           and _hex(receipt['source_commit'], 40)
           and len(receipt['distributions']) == len(expected)
           and {item['name']: item['version'] for item in receipt['distributions']} == expected
           and len(files) == len(names) and {item['filename'] for item in files} == names
           and all(set(item) == {'filename', 'sha256'} and _hex(item['sha256']) for item in files))
    return {'source_commit': receipt['source_commit'], 'receipt_sha256': _hash(receipt),
            'artifacts': [item for item in files if item['filename'].startswith(prefix)]}


def validate_manifest(data, *, hosted=False):
    try:
        by_name = {item['distribution']: item for item in data['artifacts']}
        _check(len(data['artifacts']) == len(TRAIN)
               and {name: item['version'] for name, item in by_name.items()} == TRAIN)
        lineage = data['candidate_lineage']
        proof = lineage['compatibility']
        _check(type(lineage['version']) is int and lineage['version'] == 1 and lineage['kind'] == KIND
               and type(proof['version']) is int and proof['version'] == 1 and proof['kind'] == KIND
               and lineage['compatibility_sha256'] == _hash(proof))
        core_run, harness_run = proof['core']['run_id'], lineage['harness_run_id']
        if hosted or core_run is not None or harness_run is not None:
            _check(_run(core_run) and _run(harness_run)
                   and proof['platform'] == 'linux' and proof['machine'] == 'x86_64')
        _check(type(proof['python']) is str and re.fullmatch(r'3\.1[123]\.\d+', proof['python']))

        for sdk, name in PACKAGES.items():
            binding = package_binding(lineage[sdk + '_receipt'], sdk)
            expected = {**binding, 'run_id': core_run} if sdk == 'core' else binding
            item = by_name[name]
            _check(proof[sdk] == expected and item['source_commit'] == binding['source_commit']
                   and {'filename': item['filename'], 'sha256': item['sha256']} in binding['artifacts']
                   and item['filename'] == name.replace('-', '_') + '-' + TRAIN[name] + '-py3-none-any.whl')

        retained = lineage['retained_artifacts']
        _check(len(retained) == len(RETAINED))
        for name, expected in RETAINED.items():
            item = by_name[name]
            _check(item in retained and (item['source_commit'], item['sha256']) == expected
                   and item['filename'] == name.replace('-', '_') + '-' + TRAIN[name] + '-py3-none-any.whl')
        runtime = by_name['b3-prosaic-runtime']
        upstream = lineage['harness_upstream']
        floor, original = upstream['candidates']
        _check(upstream['version'] == 1 and floor['repository'] == 'B3Cognition/prosaic'
               and floor['source_commit'] == '67b3807281ed0cdfd345fff84c56b236ec82cfb1'
               and original['repository'] == 'B3Cognition/prosaic-runtime'
               and original['run_id'] == '43210113804' and original['source_commit'] == runtime['source_commit']
               and _hex(original['receipt_sha256'])
               and original['upstream_receipt'] == {'version': 1, 'candidates': [floor]}
               and original['upstream_sha256'] == _hash(original['upstream_receipt'])
               and {'filename': runtime['filename'], 'sha256': runtime['sha256']} in original['wheels'])
        _check(proof['runtime'] == {key: original[key] for key in
               ('source_commit', 'run_id', 'receipt_sha256', 'upstream_sha256')}
               | {'filename': runtime['filename'], 'sha256': runtime['sha256'],
                  'harness_upstream_sha256': _hash(upstream)})

        results = proof['results']
        _check(set(results) == {'wheel', 'sdist'})
        for result in results.values():
            _check(result['cases'] == CASES and all(_hex(result[key]) for key in
                   ('junit_sha256', 'core_wheel_sha256', 'harness_wheel_sha256')))
        for sdk, name in PACKAGES.items():
            _check(results['wheel'][sdk + '_wheel_sha256'] == by_name[name]['sha256'])
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('invalid catalogue ontology candidate evidence') from error
    return data


def validate_released_manifest(data):
    """Match an independently committed public release, including exact wheel provenance."""
    from prosaic_integration_lab.dependencies import sdk_manifest

    message = 'invalid released catalogue ontology SDK family'
    try:
        profile = sdk_manifest(PUBLIC_PROFILE)
        if set(profile) != {'artifacts'} or data != profile:
            raise ValueError(message)

        by_name = {item['distribution']: item for item in profile['artifacts']}
        if {name: item['version'] for name, item in by_name.items()} != TRAIN:
            raise ValueError(message)
        for name, item in by_name.items():
            filename = name.replace('-', '_') + '-' + TRAIN[name] + '-py3-none-any.whl'
            url = urlsplit(item['url'])
            if (set(item) != {'distribution', 'version', 'filename', 'sha256',
                              'source_commit', 'url', 'checksum_url'}
                    or item['filename'] != filename or not _hex(item['source_commit'], 40)
                    or url.scheme != 'https' or url.netloc != 'files.pythonhosted.org'
                    or url.query or url.fragment or not url.path.endswith('/' + filename)):
                raise ValueError(message)
        for name, expected in RETAINED.items():
            item = by_name[name]
            if (item['source_commit'], item['sha256']) != expected:
                raise ValueError(message)
        for repository, name in (('prosaic', PACKAGES['core']), ('prosaic-harness', PACKAGES['harness'])):
            expected = f'https://github.com/B3Cognition/{repository}/releases/download/v{TRAIN[name]}/SHA256SUMS'
            if by_name[name]['checksum_url'] != expected:
                raise ValueError(message)
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise ValueError(message) from error
    return data
