from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from lab_runner.catalogue_ontology import validate_manifest
from lab_runner.gates import (ALL_COUNTS, expected_test_count, required_modes,
                              supports_consumer_blueprints, supports_context_assembly)


ROOT = Path(__file__).resolve().parents[2]


def _sha(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, indent=2) + '\n').encode()).hexdigest()


@pytest.fixture
def manifest():
    released = json.loads((ROOT / 'dependencies/releases.json').read_bytes())['artifacts']
    retained = [item for item in released if item['distribution'] not in {'b3-prosaic', 'b3-prosaic-harness'}]
    from lab_runner.catalogue_ontology import CASES

    artifacts = retained.copy()
    receipts = {}
    packages = {}
    for sdk, name, version, digit in (('core', 'b3-prosaic', '0.5.1', 'a'),
                                       ('harness', 'b3-prosaic-harness', '0.9.18', 'b')):
        prefix = f'{name.replace("-", "_")}-{version}'
        package_files = [{'filename': prefix + suffix, 'sha256': digit * 64}
                         for suffix in ('-py3-none-any.whl', '.tar.gz')]
        packages[sdk] = dict(source_commit=digit * 40, artifacts=package_files)
        distributions = [{'name': name, 'version': version}]
        if sdk == 'harness':
            distributions.append({'name': 'b3-prosaic-harness-postgres', 'version': '0.4.5'})
        receipts[sdk] = dict(version=1, source_commit=digit * 40, artifacts=package_files.copy(),
                             distributions=distributions)
        if sdk == 'harness':
            receipts[sdk]['artifacts'] += [{'filename': 'b3_prosaic_harness_postgres-0.4.5' + suffix,
                                           'sha256': 'c' * 64}
                                          for suffix in ('-py3-none-any.whl', '.tar.gz')]
        packages[sdk]['receipt_sha256'] = _sha(receipts[sdk])
        artifacts.append(dict(distribution=name, version=version, source_commit=digit * 40,
                              **package_files[0]))
    runtime = retained[0]
    floor = dict(repository='B3Cognition/prosaic', source_commit=released[0]['source_commit'])
    runtime_upstream = dict(version=1, candidates=[floor])
    upstream = dict(version=1, candidates=[floor, dict(repository='B3Cognition/prosaic-runtime',
        run_id='43210113804', source_commit=runtime['source_commit'], receipt_sha256='c' * 64,
        upstream_receipt=runtime_upstream, upstream_sha256=_sha(runtime_upstream),
        wheels=[{'filename': runtime['filename'], 'sha256': runtime['sha256']}])])
    result = dict(cases=CASES, junit_sha256='d' * 64, core_wheel_sha256='a' * 64,
                  harness_wheel_sha256='b' * 64)
    proof = dict(version=1, kind='catalogue-ontology', core={**packages['core'], 'run_id': None},
                 harness=packages['harness'], runtime={**upstream['candidates'][1],
                 'filename': runtime['filename'], 'sha256': runtime['sha256'],
                 'harness_upstream_sha256': _sha(upstream)}, python='3.12.15', platform='linux',
                 machine='aarch64', results={'wheel': result, 'sdist': result.copy()})
    for key in ('repository', 'wheels', 'upstream_receipt'):
        proof['runtime'].pop(key)
    return dict(artifacts=artifacts, candidate_lineage=dict(version=1, kind='catalogue-ontology',
        core_receipt=receipts['core'], harness_receipt=receipts['harness'], harness_upstream=upstream,
        compatibility=proof, compatibility_sha256=_sha(proof), harness_run_id=None,
        retained_artifacts=retained))


def test_candidate_inherits_the_entire_released_stack(manifest):
    assert validate_manifest(manifest) == manifest
    assert supports_consumer_blueprints(manifest)
    assert supports_context_assembly(manifest)
    modes = required_modes(candidate=True, manifest=manifest)
    assert modes == tuple(ALL_COUNTS)
    assert len(modes) == 14
    assert sum(expected_test_count(mode, True) for mode in modes) == 450


def test_ontology_candidate_cannot_build_in_released_mode(manifest, tmp_path):
    from scripts.build_consumer import build

    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='ontology handoff requires candidate mode'):
        build(path, tmp_path / 'wheels', 'fixture', 'released')


@pytest.mark.parametrize('change', [
    lambda value: value['artifacts'][0].update(sha256='0' * 64),
    lambda value: value['artifacts'].append(value['artifacts'][0]),
    lambda value: value['candidate_lineage'].pop('compatibility'),
    lambda value: value['candidate_lineage']['compatibility']['results']['wheel']['cases'].clear(),
    lambda value: value['candidate_lineage']['harness_upstream']['candidates'].reverse(),
    lambda value: value['candidate_lineage']['harness_receipt']['artifacts'][0].update(sha256='0' * 64),
])
def test_candidate_rejects_mismatched_lineage_and_artifacts(manifest, change):
    altered = deepcopy(manifest)
    change(altered)
    with pytest.raises(ValueError):
        validate_manifest(altered)
