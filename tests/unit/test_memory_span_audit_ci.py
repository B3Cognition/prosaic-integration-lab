"""CI must execute every profile and reject substituted SDK candidate bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_profiles_cover_default_files_and_keep_candidate_assertions(tmp_path):
    paths = ['tests/unit/test_ordinary.py', 'tests/functional/test_service.py',
        'tests/unit/test_memory_span_audit_contracts.py', 'tests/unit/test_mb_answer_contract.py',
        'tests/memory_benchmark_candidate/test_span_audit.py', 'tests/requirements_review_v5/test_canonical.py']
    for path in paths:
        p = tmp_path/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('def test_ok(): pass\n')
    groups = script('regression_profiles').groups(tmp_path)
    assert set(groups['released']) == set(paths[:2])
    assert set(groups['candidate']) == set(paths[2:])
    assert set(groups['all']) <= set(groups['released']) | set(groups['candidate'])


def test_profile_coverage_rejects_a_missing_or_unexecuted_test():
    m = script('regression_profiles')
    released = dict(profile='released', nodeIds=['tests/unit/test_a.py::test_a'], exitCode=0, skipped=0, collectedOnly=False)
    candidate = dict(profile='candidate', nodeIds=['tests/unit/test_b.py::test_b'], exitCode=0, skipped=0, collectedOnly=False)
    all_tests = dict(profile='all', nodeIds=released['nodeIds']+candidate['nodeIds'], exitCode=0, skipped=0, collectedOnly=True)
    assert m.coverage(all_tests, released, candidate)['covered'] is True
    for key, value in [('nodeIds', []), ('skipped', 1), ('exitCode', 1), ('collectedOnly', True)]:
        bad = dict(candidate, **{key:value})
        with pytest.raises(ValueError): m.coverage(all_tests, released, bad)


def test_required_profile_rejects_skips_and_retains_summary(tmp_path):
    p = tmp_path/'tests/unit/test_required.py'; p.parent.mkdir(parents=True)
    p.write_text('import pytest\ndef test_required(): pytest.skip("missing required prerequisite")\n')
    output = tmp_path/'summary.json'
    result = subprocess.run([sys.executable, '-I', str(ROOT/'scripts/regression_profiles.py'),
        '--root', str(tmp_path), '--profile', 'released', '--output', str(output)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 1, result.stdout+result.stderr
    summary = json.loads(output.read_text())
    assert summary['skipped'] == 1 and summary['exitCode'] == 1


@pytest.mark.parametrize('options', [['--collect-only'], ['--setup-only'], ['-k','test_first']])
def test_execution_proof_counts_actual_test_calls_not_collection(tmp_path, options):
    p = tmp_path/'tests/unit/test_execution.py'; p.parent.mkdir(parents=True)
    p.write_text('def test_first(): pass\ndef test_second(): pass\n')
    output = tmp_path/'summary.json'
    result = subprocess.run([sys.executable, '-I', str(ROOT/'scripts/regression_profiles.py'),
        '--root',str(tmp_path),'--profile','released','--output',str(output),'--',*options],
        capture_output=True,text=True,timeout=30)
    summary = json.loads(output.read_text())
    if options[0] in ('--collect-only','--setup-only'):
        assert result.returncode == 1 and summary['nodeIds'] == []
    else:
        assert result.returncode == 0
        assert summary['nodeIds'] == ['tests/unit/test_execution.py::test_first']


def wheel_fixture(tmp_path):
    name = 'b3_prosaic_runtime-0.9.8+jsonschema.3-py3-none-any.whl'
    members = {'prosaic_runtime/__init__.py':b'VALUE = 1\n',
        'b3_prosaic_runtime-0.9.8+jsonschema.3.dist-info/METADATA':
        b'Metadata-Version: 2.1\nName: b3-prosaic-runtime\nVersion: 0.9.8+jsonschema.3\n'}
    spec = dict(version=1, repository='B3Cognition/prosaic-runtime',
        sourceCommit='1'*40, sourceTree='2'*40, distribution='b3-prosaic-runtime',
        packageVersion='0.9.8+jsonschema.3', originalWheelSha256='3'*64,
        members={n:hashlib.sha256(value).hexdigest() for n,value in members.items()}, publicationAuthorized=False)
    path = tmp_path/name
    with zipfile.ZipFile(path, 'w') as z:
        for n,value in members.items(): z.writestr(n,value)
    return path, spec, members


@pytest.mark.parametrize('mutation', ['changed', 'added', 'missing', 'duplicate', 'symlink'])
def test_candidate_wheel_rejects_changed_or_uninventoried_members(tmp_path, mutation):
    path, spec, members = wheel_fixture(tmp_path)
    verifier = script('verify_answer_span_runtime')
    assert verifier.verify_wheel(path, spec)['qualified'] is True
    with zipfile.ZipFile(path, 'w') as z:
        for n,value in members.items():
            if mutation == 'missing' and n.endswith('__init__.py'): continue
            z.writestr(n, value+b'# replaced\n' if mutation == 'changed' and n.endswith('__init__.py') else value)
        if mutation == 'added': z.writestr('prosaic_runtime/injected.py', b'pass\n')
        if mutation == 'duplicate': z.writestr('prosaic_runtime/__init__.py', b'VALUE = 1\n')
        if mutation == 'symlink':
            item = zipfile.ZipInfo('link'); item.external_attr = (0o120777 << 16)
            z.writestr(item, 'prosaic_runtime/__init__.py')
    with pytest.raises(ValueError): verifier.verify_wheel(path, spec)


def test_candidate_spec_must_remain_unpublished_and_exact(tmp_path):
    path, spec, _ = wheel_fixture(tmp_path)
    verifier = script('verify_answer_span_runtime')
    for change in [dict(publicationAuthorized=True), dict(sourceCommit='main'), dict(packageVersion='0.9.8')]:
        with pytest.raises(ValueError): verifier.verify_wheel(path, dict(spec, **change))


def test_audit_ci_executes_both_profiles_and_checks_coverage_and_installed_fixtures():
    import yaml
    path = ROOT/'.github/workflows/answer-span-audit.yml'
    assert path.is_file(), 'audit candidate has no reproducible CI lane'
    workflow = yaml.safe_load(path.read_text())
    assert workflow['permissions'] == {'contents':'read'}
    job = workflow['jobs']['audit']
    assert job['strategy']['matrix'] == {'runner':['ubuntu-24.04','ubuntu-24.04-arm']}
    commands = '\n'.join(step.get('run','') for step in job['steps'])
    for term in ['--profile all --collect-only', '--profile released', '--profile candidate',
                 '--coverage', 'verify_answer_span_runtime.py', 'audit-fixture',
                 '--force-reinstall', '--no-deps']:
        assert term in commands
    assert 'secrets.' not in path.read_text()
    assert all('@' in step['uses'] and len(step['uses'].split('@')[1].split()[0])==40
               for step in job['steps'] if 'uses' in step)


def test_existing_ci_assigns_candidate_only_tests_without_dropping_other_assertions():
    import yaml
    for name in ['required-acceptance.yml', 'sue-review.yml']:
        workflow = yaml.safe_load((ROOT/'.github/workflows'/name).read_text())
        commands = '\n'.join(step.get('run','') for job in workflow['jobs'].values() for step in job['steps'])
        assert 'regression_profiles.py --profile released' in commands
    commands = (ROOT/'.github/workflows/sue-review.yml').read_text()
    for directory in ['tests/sue_review','tests/requirements_review','tests/requirements_review_v2']:
        assert directory in commands


def test_sue_ci_preserves_legacy_engine_and_qualifies_opt_in_context_separately():
    import yaml
    workflow = yaml.safe_load((ROOT/'.github/workflows/sue-review.yml').read_text())
    steps = workflow['jobs']['synthetic']['steps']
    checkout = next(step for step in steps if 'checkout@' in step.get('uses',''))
    assert checkout['with']['fetch-depth'] == 0
    context = next(step for step in steps if step.get('name')=='Qualify opt-in context with its exact engine and restore legacy bytes')
    assert 'tests/sue_review/test_review_context.py' in context['run']
    assert 'bundle/sue-cycle/*.whl' in context['run']
    assert '--force-reinstall bundle/sue/*.whl' in context['run']
    assert 'dependencies/sue-cycle-ci-source.json' in '\n'.join(step.get('run','') for step in steps)
    legacy = next(step for step in steps if step.get('name')=='Require ordinary and explicitly enabled source regressions without skips')
    assert '--ignore=tests/sue_review/test_review_context.py' in legacy['run']
    assert 'dependencies/sue-review-source.json' in (ROOT/'.github/workflows/sue-review.yml').read_text()
