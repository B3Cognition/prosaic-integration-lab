"""Required installed Lab model-job cells: owned PostgreSQL and loopback only."""

from copy import deepcopy
import importlib.metadata
import json
import os
from pathlib import Path
import uuid

import pytest


@pytest.fixture(params=['file', 'postgres'])
def model_job_case(request, tmp_path):
    import psycopg
    from prosaic_harness import FileRunStore
    from prosaic_harness_postgres import PostgresRunStore
    from prosaic_runtime import RateCard
    from prosaic_runtime_postgres import PostgresRecorder
    import prosaic_integration_lab
    import prosaic_integration_lab.castle_jobs

    installed = importlib.metadata.distribution('prosaic-integration-lab')
    for module, name in (
        (prosaic_integration_lab, 'prosaic_integration_lab/__init__.py'),
        (prosaic_integration_lab.castle_jobs, 'prosaic_integration_lab/castle_jobs/__init__.py'),
    ):
        assert Path(module.__file__).resolve() == installed.locate_file(name).resolve(), (
            'required Castle job qualification must execute the installed Lab wheel')
    configuration = os.environ.get('LAB_MEMORY_FIXTURE')
    assert configuration, 'required Castle jobs need explicit owned PostgreSQL infrastructure'
    fixture = json.loads(Path(configuration).read_text())
    # OwnedPostgres provisions this restricted role separately from its migrator.
    # Never initialize either SDK schema from an application connection.
    with psycopg.connect(fixture['dsn']) as connection:
        role, can_create = connection.execute(
            "SELECT current_user, has_schema_privilege(current_user,'public','CREATE')"
        ).fetchone()
        assert role == 'memory_runtime' and can_create is False
    namespace = 'castle-jobs-' + uuid.uuid4().hex
    store = (FileRunStore(tmp_path/'runs', namespace=namespace) if request.param == 'file'
             else PostgresRunStore(fixture['dsn'], namespace=namespace))
    recorder = PostgresRecorder(fixture['dsn'], namespace=namespace, environment='sandbox',
        rate_card=RateCard('castle-jobs-fixture-v1', 'requirements-fixture-v1', '2', '8', '0.5'))
    try:
        yield fixture, namespace, store, recorder, request.param
    finally:
        store.close()


def _sources():
    return [dict(sourceId=f's{n}', text=f'Atlas is the named project. Evidence {n}. 🙂\r\n',
                 revision='r1', reference=f'fixture://castle-jobs/{n}',
                 provenance={'origin':'synthetic_fixture','record_id':f'fixture-{n}'})
            for n in range(4)]


def _exercise(case, kind, *, malformed_judge=False):
    from prosaic_harness import RevisionConflict
    from prosaic_runtime import EndpointConfig, RuntimeConfig
    from lab_runner.requirements_review_v1.fixtures import provider
    from prosaic_integration_lab.castle_jobs import CastleJobError, CastleJobSession
    from prosaic_integration_lab.identity import Principal

    fixture, namespace, store, recorder, store_kind = case
    owner = Principal('tenant-a', 'alice', 'payer-a')
    sources = _sources()
    retained = deepcopy(sources)
    options = dict(kind=kind, candidates=sources)
    if kind == 'judge':
        options.update(query='Atlas project evidence', top_n=2)
        answer = {'ranked_indices':[True,False]} if malformed_judge else {'ranked_indices':[1,0]}
    elif kind == 'entity_refinement':
        options['entities'] = [{'name':'Atlas','currentType':'uncertain', 'contexts':[
            {'sourceId':'s0','line':1,'quote':'Atlas is the named project.'}]}]
        answer = {'classifications':[{'name':'Atlas','label':'PROJECT','reason':'Explicitly named project.'}]}
    else:
        answer = {'is_ai_dialogue_corpus':False,'confidence':0.8,'primary_platform':None,
                  'user_name':'Alice','agent_persona_names':['Alice','Echo'],
                  'evidence':['Project notes without conversational turns.']}
    expected = deepcopy(answer)
    if kind == 'corpus_origin':
        expected['agent_persona_names'] = ['Echo']
    run_id = uuid.uuid4().hex
    with provider([answer]) as (url, calls):
        config = RuntimeConfig({'fixture':EndpointConfig(url, 'requirements-fixture-v1',
            features={'streaming':False})}, {}, 'fixture', allowed_tools=frozenset())
        jobs = CastleJobSession({'enabled':True}, store, config, owner, namespace, accounting=recorder)
        waiting = jobs.start(run_id, **options)
        assert waiting['status'] == 'waiting' and waiting['attempts'] == 0
        assert calls == [] and recorder.calls(run_id=run_id) == []
        frozen = deepcopy(store.load_run(run_id).state['inputs']['candidates'])
        assert [s['text'].encode() for s in frozen] == [s['text'].encode() for s in retained]
        assert [s['provenance'] for s in frozen] == [s['provenance'] for s in retained]
        sources[0]['text'] = 'Changed caller-owned object after admission.'
        sources[0]['revision'] = 'changed'
        sources[0]['provenance']['record_id'] = 'changed'
        with pytest.raises(CastleJobError, match='job_request_conflict'):
            jobs.start(run_id, **options)
        wrong = CastleJobSession({'enabled':True}, store, config,
            Principal('tenant-a', 'bob', 'payer-a'), namespace, accounting=recorder)
        with pytest.raises(PermissionError):
            wrong.report(run_id)
        with pytest.raises(RevisionConflict):
            jobs.resume(run_id, expected_revision='0'*64, choice='continue')
        assert calls == [] and recorder.calls(run_id=run_id) == []

        completed = jobs.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        assert completed['status'] == 'completed' and completed['attempts'] == 1 and len(calls) == 1
        assert store.load_run(run_id).state['inputs']['candidates'] == frozen
        assert 'Changed caller-owned' not in json.dumps(calls)
        assert all(not row['request'].get('tools') for row in calls)
        report = jobs.report(run_id)
        assert report['advisory'] is True and report['usageComplete'] is True and report['reportedTokens'] == 15
        assert report['audit']['receiptSha256'] and report['audit']['responseSha256']
        assert report['audit']['fallback'] is malformed_judge
        if malformed_judge:
            assert report['result'] is None and report['audit']['reason'] == 'invalid_ranking_permutation'
        else:
            assert report['result'] == expected and report['audit']['reason'] is None
        if kind == 'judge':
            assert report['rankedSourceIds'] == (['s0','s1','s2','s3'] if malformed_judge else ['s1','s0','s2','s3'])

        jobs.resume(run_id, expected_revision=completed['revision'])
        with pytest.raises(RevisionConflict):
            jobs.resume(run_id, expected_revision=waiting['revision'], choice='continue')
        disabled = CastleJobSession(None, store, config, owner, namespace, accounting=recorder)
        assert disabled.report(run_id) == report
        with pytest.raises(CastleJobError, match='castle_jobs_disabled'):
            disabled.resume(run_id, expected_revision=completed['revision'])
        with pytest.raises(CastleJobError, match='castle_jobs_disabled'):
            disabled.start(uuid.uuid4().hex, **options)
        assert len(calls) == 1
        rows = recorder.calls(run_id=run_id)
        assert len(rows) == 1
        context = rows[0]['intent']['context']
        assert {key:context[key] for key in ('application_id','project_id','tenant_id','actor_id','billing_account_id')} == {
            'application_id':'integration-lab-castle-jobs','project_id':namespace,
            'tenant_id':'tenant-a','actor_id':'alice','billing_account_id':'payer-a'}

    # Export only the already filtered public report and explicit synthetic checks.
    # No fixture DSN, raw responses, prompts or Harness/operator state is retained.
    evidence = dict(origin='scripted_castle_jobs_fixture', synthetic_only=True, store=store_kind,
        jobKind=kind, invalidJudge=malformed_judge, providerRequests=1, replayAdditionalRequests=0,
        wrongOwnerRefused=True, staleRevisionRefused=True, exactSourcesFrozen=True,
        billingPinned=True, disabledDispatches=0, report=report)
    serialized = json.dumps(evidence, sort_keys=True, indent=2)+'\n'
    assert fixture['dsn'] not in serialized and 'rawResponse' not in serialized and 'accounting_context' not in serialized
    directory = Path(fixture['evidence_directory'])/'jobs'
    directory.mkdir(parents=True, exist_ok=True)
    name = kind + ('--invalid' if malformed_judge else '--valid') + '--' + store_kind + '.json'
    (directory/name).write_text(serialized)


@pytest.mark.parametrize('kind', ['judge', 'entity_refinement', 'corpus_origin'])
def test_installed_optional_job_owner_freeze_usage_and_replay(model_job_case, kind):
    _exercise(model_job_case, kind)


def test_installed_invalid_judge_preserves_original_order_without_retry(model_job_case):
    _exercise(model_job_case, 'judge', malformed_judge=True)
