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
    released = json.loads((ROOT / 'dependencies/releases-pre-ontology-2026-11-13.json').read_bytes())['artifacts']
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
    floor = dict(repository='B3Cognition/prosaic', source_commit='67b3807281ed0cdfd345fff84c56b236ec82cfb1')
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


@pytest.fixture
def released_ontology(manifest, tmp_path, monkeypatch):
    from lab_runner import catalogue_ontology

    for item in manifest['artifacts']:
        name = item['filename']
        if 'url' not in item:
            repository = 'prosaic' if item['distribution'] == 'b3-prosaic' else 'prosaic-harness'
            item.update(
                url=f'https://files.pythonhosted.org/packages/fixture/{name}',
                checksum_url=f'https://github.com/B3Cognition/{repository}/releases/download/v{item["version"]}/SHA256SUMS',
            )
    released = {'artifacts': manifest['artifacts']}
    path = tmp_path / 'catalogue-ontology-public-0.5.1-0.9.18.json'
    path.write_text(json.dumps(released))
    monkeypatch.setattr(catalogue_ontology, 'PUBLIC_PROFILE', path, raising=False)
    return released


def test_public_ontology_requires_the_full_inherited_stack(released_ontology):
    modes = required_modes(candidate=False, manifest=released_ontology)
    assert modes == tuple(ALL_COUNTS)
    assert len(modes) == 14
    assert sum(expected_test_count(mode, True) for mode in modes) == 450


@pytest.mark.parametrize('alteration', ['changed-digest', 'changed-source', 'qualified-run', 'lineage'])
def test_released_ontology_rejects_changed_public_provenance(released_ontology, alteration):
    from lab_runner import catalogue_ontology

    changed = deepcopy(released_ontology)
    core = next(item for item in changed['artifacts'] if item['distribution'] == 'b3-prosaic')
    if alteration == 'changed-digest':
        core['sha256'] = 'f' * 64
    elif alteration == 'changed-source':
        core['source_commit'] = 'e' * 40
    elif alteration == 'qualified-run':
        core['qualified_run_id'] = '12345'
    else:
        changed['candidate_lineage'] = {'kind': 'catalogue-ontology'}
    with pytest.raises(ValueError):
        catalogue_ontology.validate_released_manifest(changed)


def test_qualified_candidate_cannot_supply_released_ontology_proof(manifest, released_ontology):
    from lab_runner import catalogue_ontology

    with pytest.raises(ValueError):
        catalogue_ontology.validate_released_manifest(manifest)


def test_released_stack_rejects_candidate_lineage(manifest):
    with pytest.raises(ValueError):
        required_modes(candidate=False, manifest=manifest)


@pytest.mark.parametrize('complete', [True, False])
def test_public_distribution_requires_the_installed_ontology_cases(
        released_ontology, tmp_path, monkeypatch, complete):
    from types import SimpleNamespace
    from xml.etree import ElementTree
    from scripts import conversation_distribution_smoke as smoke

    calls = []
    monkeypatch.setattr(smoke, 'verified_wheel_paths', lambda *args: ())
    monkeypatch.setattr(smoke, 'wheel_identity', lambda path: {'name': 'lab', 'version': '0.9.16', 'files': {}})
    monkeypatch.setattr(smoke, 'verify_cli_versions', lambda *args: None)
    monkeypatch.setattr(smoke, '_helper', lambda name: SimpleNamespace(
        INDEX='https://pypi.org/simple', AUDIT_LAUNCH='', PUBLIC_EXAMPLE=''))

    def run(argv, *, directory, environment, **kwargs):
        if 'lab_runner.native_eval' in argv:
            counts = {'test': 9, 'unified-test': 11, 'unified-cli-test': 13, 'unified-fallback-test': 18}
            command = argv[argv.index('lab_runner.native_eval') + 1]
            calls.append(command)
            return json.dumps({'passed': True, 'caseCount': counts[command],
                'cleanup': 'verified', 'liveInvocations': 0}).encode()
        if any(str(arg).endswith('/tests/catalogue_ontology_acceptance') for arg in argv):
            assert '-I' in argv and '-B' in argv
            assert environment['PROSAIC_LAB_ONTOLOGY_PROFILE'] == 'released'
            calls.append('ontology')
            names = (
                'test_discovery_and_execution_are_offline',
                'test_projection_is_opt_in_scoped_and_detached',
                'test_discovery_bounds_combined_response',
                'test_core_rejects_invalid_attachments[malformed-json]',
                'test_core_rejects_invalid_attachments[duplicate-key]',
                'test_core_rejects_invalid_attachments[unknown-concept]',
                'test_unregistered_aliases_are_rejected[agents]',
                'test_unregistered_aliases_are_rejected[tools]',
                'test_workflow_admission_ignores_ontology_authority',
                'test_exact_installed_sdk_payloads',
                'test_copied_catalogue_and_workflow',
            )
            suite = ElementTree.Element('testsuite', tests='11', failures='0', errors='0', skipped='0')
            for name in names if complete else names[1:]:
                ElementTree.SubElement(suite, 'testcase', name=name)
            flag = next(str(arg) for arg in argv if str(arg).startswith('--junitxml='))
            ElementTree.ElementTree(suite).write(flag.split('=', 1)[1])
        if any(str(arg).endswith('/tests/blueprint_acceptance/test_sub_agents.py') for arg in argv):
            calls.append('delegation')
        return b'{}'

    monkeypatch.setattr(smoke, 'run', run)
    manifest_path = tmp_path / 'manifest.json'
    manifest_path.write_text(json.dumps(released_ontology))
    arguments = dict(directory=tmp_path, manifest=manifest_path, wheels=tmp_path,
                     lock=tmp_path / 'requirements.lock', environment={})
    if complete:
        smoke.consume(tmp_path / 'lab.whl', **arguments)
        assert calls == ['test', 'unified-test', 'unified-cli-test', 'unified-fallback-test',
                         'delegation', 'ontology']
    else:
        with pytest.raises(ValueError, match='incomplete catalogue ontology acceptance'):
            smoke.consume(tmp_path / 'lab.whl', **arguments)
        assert 'ontology' in calls
