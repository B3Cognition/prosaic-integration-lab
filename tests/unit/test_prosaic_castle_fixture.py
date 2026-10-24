import builtins
import json
import hashlib
from pathlib import Path

import pytest


def test_fork_qualification_is_disabled_without_importing_optional_packages(monkeypatch, capsys):
    from lab_runner import prosaic_castle_fixture

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split('.')[0] not in {'cognitive_castle', 'prosaic_castle', 'castle_sue', 'prosaic_memory_castle'}
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', guarded)
    assert prosaic_castle_fixture.main([]) == 0
    assert json.loads(capsys.readouterr().out) == {'enabled': False, 'qualified': False, 'reason': 'disabled'}


def test_case_projection_preserves_frozen_hackathon_scorer_and_source_identity():
    from lab_runner.castle_requirements_v1 import project_case
    from lab_runner.requirements_review_v1.cases import load_cases
    from lab_runner.requirements_review_v1.host_keys import fixture_answer, load_keys
    from lab_runner.requirements_review_v1.scoring import grade
    from prosaic_integration_lab.sue_review.sources import freeze_documents

    for case_id, case in load_cases().items():
        frozen = freeze_documents([dict(case['sources'][0], sourceId='castle:0123456789abcdef')])
        projected, answer, restore = project_case(case_id, frozen)
        assert projected['sources'][0]['text'] == case['sources'][0]['text']
        assert projected['sources'][0]['sourceId'] == 'castle:0123456789abcdef'
        assert answer['citations'][0]['sourceId'] == projected['sources'][0]['sourceId']
        normalized = restore(answer)
        assert normalized == fixture_answer(case, load_keys()[case_id])
        assert grade(case, load_keys()[case_id], normalized)['passed']


def test_fork_runner_refuses_existing_evidence_before_any_fixture(tmp_path):
    from lab_runner.prosaic_castle_fixture import main

    retained = tmp_path/'evidence'
    retained.mkdir()
    receipt = retained/'qualification.json'
    receipt.write_text('historic bytes')
    with pytest.raises(SystemExit):
        main(['--enable','--lab-wheel','absent','--engine-wheel','absent',
              '--adapter-wheel','absent','--worker-wheel','absent','--worker-python','absent',
              '--tests-root','absent','--output',str(retained)])
    assert receipt.read_text() == 'historic bytes'


def test_frozen_execution_refuses_corrupted_sources_before_dispatch():
    from lab_runner.castle_requirements_v1 import execute_frozen_case
    from lab_runner.requirements_review_v1.cases import load_cases
    from prosaic_integration_lab.identity import Principal
    from prosaic_integration_lab.sue_review.contracts import ReviewError
    from prosaic_integration_lab.sue_review.sources import freeze_documents
    from prosaic_runtime import RuntimeConfig,EndpointConfig

    frozen = freeze_documents(load_cases()['requirements-01']['sources'])
    frozen['sourcesSha256'] = '0'*64
    config = RuntimeConfig({'fixture':EndpointConfig('http://127.0.0.1:9/v1',
        'requirements-fixture-v1',features={'streaming':False})},{},'fixture')
    with pytest.raises(ReviewError,match='source_identity_mismatch'):
        execute_frozen_case('requirements-01','direct',frozen=frozen,config=config,
            store=None,principal=Principal('t','a','p'),namespace='owned')


def test_new_fork_profile_keeps_disabled_default_and_frozen_sue_identity():
    root = Path(__file__).resolve().parents[2]
    profile = json.loads((root/'dependencies/prosaic-castle-source-2026-10-24.json').read_text())
    assert profile['default_enabled'] is False and profile['publication_authorized'] is False
    assert profile['worker']['distribution'] == 'prosaic-castle'
    assert profile['worker']['profile'] == 'memory-fts-v1'
    assert profile['worker']['recency_boost'] is False
    assert profile['sue']['engine_identity'] == 'bbde4669d1eb069dcb8c72e121cd08be4ca953b349f9243b9e650e0d1b596f0b'
    assert profile['sue']['default_enabled'] is False
    for filename, sha in profile['preserved_profiles'].items():
        assert hashlib.sha256((root/'dependencies'/filename).read_bytes()).hexdigest() == sha
    from lab_runner.prosaic_castle_fixture import ENGINE_SHA256
    assert profile['sue']['wheel_sha256'] == ENGINE_SHA256
    from lab_runner.prosaic_castle_fixture import WORKER_SHA256, ADAPTER_SHA256
    assert profile['worker']['wheel_sha256'] == WORKER_SHA256
    assert profile['adapter']['wheel_sha256'] == ADAPTER_SHA256


def test_fixture_failure_export_redacts_full_and_truncated_dsn_passwords():
    from lab_runner.prosaic_castle_fixture import sanitize_fixture_log

    dsn = 'host=127.0.0.1 port=5432 dbname=fixture user=runtime password=abcdef123456'
    text = dsn + "\nfixture={'dsn': 'host=127.0.0.1 password=abcdef...'}\nFAILED test_real_assertion"
    result = sanitize_fixture_log(text,dsn)
    assert 'abcdef' not in result and dsn not in result
    assert 'FAILED test_real_assertion' in result


def test_required_lane_inventory_cannot_qualify_without_model_jobs():
    from lab_runner.prosaic_castle_fixture import required_test_names, complete_test_inventory
    from xml.etree.ElementTree import Element,SubElement

    names = required_test_names()
    assert len(names) == 76
    assert 'test_installed_optional_job_owner_freeze_usage_and_replay[postgres-corpus_origin]' in names
    assert 'test_actual_frozen_castle_hackathon_case_survives_source_removal[file-sue-requirements-08]' in names
    suite = Element('testsuite')
    for name in sorted(names):
        SubElement(suite,'testcase',name=name)
    assert complete_test_inventory(suite)
    missing = next(case for case in suite if case.get('name').startswith('test_installed_optional_job'))
    suite.remove(missing)
    assert not complete_test_inventory(suite)
    SubElement(suite,'testcase',name='unrelated_case_that_keeps_count_76')
    assert not complete_test_inventory(suite)
