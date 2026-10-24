"""Explicit installed candidate lane: frozen constrained SUE on both stores."""
import importlib.metadata
import json
import os
from pathlib import Path
import uuid

import pytest
from prosaic_harness import FileRunStore
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime import EndpointConfig, RateCard, RuntimeConfig
from prosaic_runtime_postgres import PostgresRecorder

from lab_runner.sue_review_fixture import CLAIM, SOURCE_LINE, model_fixture
from lab_runner.requirements_review_v1.fixtures import provider
from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.sue_review.contracts import ReviewError, digest
from prosaic_integration_lab.sue_review.session import SueReviewSession


@pytest.fixture(params=['file', 'postgres'])
def installed_case(request, tmp_path):
    import prosaic_integration_lab, prosaic_runtime
    for module, name in [(prosaic_integration_lab, 'prosaic-integration-lab'), (prosaic_runtime, 'b3-prosaic-runtime')]:
        owner = importlib.metadata.distribution(name)
        assert Path(module.__file__).resolve() == owner.locate_file(module.__name__+'/__init__.py').resolve()
    assert importlib.metadata.version('b3-prosaic-runtime') == '0.9.8+jsonschema.2'
    config_path = os.environ.get('LAB_SUE_FIXTURE')
    assert config_path, 'explicit owned PostgreSQL fixture required'
    fixture = json.loads(Path(config_path).read_text())
    namespace = 'sue-json-'+uuid.uuid4().hex
    store = FileRunStore(tmp_path/'runs', namespace=namespace) if request.param == 'file' else PostgresRunStore(fixture['dsn'], namespace=namespace)
    recorder = PostgresRecorder(fixture['dsn'], namespace=namespace, environment='sandbox',
        rate_card=RateCard('sue-fixture-v1', 'sue-fixture', '2', '8', '0.5'))
    try: yield store, recorder, namespace
    finally: store.close()


@pytest.mark.parametrize('scenario', ['complete', 'false_quote', 'missing_field'])
def test_installed_constrained_sue_freeze_resume_and_strict_acceptance(installed_case, scenario):
    store, recorder, namespace = installed_case
    source = SOURCE_LINE+'\r\nConsent must be current.\r\n'
    owner = Principal('tenant', 'alice', 'payer')
    invalid = dict(answer='An attributed interpretation requiring review.', verdict='SUPPORTED',
        answer_type='definition', evidence_lines=[1], claim=CLAIM, test_result='ESTABLISHED',
        evidence=[{'line': 1, 'quote': SOURCE_LINE}], premises=[{'statement': SOURCE_LINE,
        'kind': 'stated', 'evidence_lines': [1]}], witness=None, open_questions=[], addresses=[], revision_reason=None)
    if scenario == 'false_quote': invalid['evidence'][0]['quote'] = 'Fabricated quotation.'
    if scenario == 'missing_field': invalid.pop('addresses')
    responder = model_fixture() if scenario == 'complete' else provider([invalid])
    with responder as (url, calls):
        config = RuntimeConfig({'fixture': EndpointConfig(url, 'sue-fixture', features={'streaming': False})}, {}, 'fixture')
        def session(*, enabled=True, constrained=False, principal=owner):
            return SueReviewSession({'enabled': enabled}, store, config, principal, namespace,
                accounting=recorder, constrained_json=constrained)
        flow = session(constrained=True); run_id = uuid.uuid4().hex
        sources = [{'sourceId': 'spec', 'text': source, 'revision': 'r1'}]
        waiting = flow.start(run_id, seed=CLAIM, sources=sources)
        assert waiting['status'] == 'waiting' and calls == []
        frozen = store.load_run(run_id).state['inputs']['evidence']
        sources[0]['text'] = 'Changed after admission.'
        with pytest.raises(PermissionError): session(principal=Principal('tenant', 'bob', 'payer')).status(run_id)
        with pytest.raises(ReviewError, match='review_disabled'):
            session(enabled=False).resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert calls == [] and recorder.calls(run_id=run_id) == []
        done = session().resume(run_id, expected_revision=waiting['revision'], choice='continue')
        requests = calls if scenario == 'complete' else [row['request'] for row in calls]
        if scenario != 'complete':
            assert done['status'] == 'blocked' and done['acceptedTurns'] == 0
            assert len(requests) == 2
        else:
            assert done['status'] == 'completed' and done['acceptedTurns'] == 7
            assert store.load_run(run_id).state['inputs']['evidence'] == frozen
            assert len(requests) == 7
            count = len(requests)
            assert session().resume(run_id, expected_revision=done['revision']) == done
            assert len(requests) == count
        rows = recorder.calls(run_id=run_id)
        assert len(rows) == len(requests)
        assert sum(row['observation']['usage']['total_tokens'] for row in rows) == len(rows)*15
        saved = store.load_run(run_id).state
        for invocation, wire in zip(saved['invocations'], requests, strict=True):
            receipt = store.load_receipt(run_id, invocation['id'])
            prompt = wire['messages'][0]['content']
            projected = json.loads(prompt.split('\n\n## Arguments\n', 1)[1])
            schema = projected['responseSchema']
            assert wire['response_format'] == {'type': 'json_schema', 'json_schema': {'name': 'response', 'schema': schema, 'strict': True}}
            assert receipt['result']['metadata']['response_schema_v1']['schema_sha256'] == digest(schema)
            assert not wire.get('tools')
