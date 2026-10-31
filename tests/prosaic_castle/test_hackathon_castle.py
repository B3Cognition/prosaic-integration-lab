"""Required installed fork lane; actual Castle sources across all 24 fixture cells."""

from copy import deepcopy
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import uuid

import pytest


@pytest.fixture(params=['file','postgres'])
def castle_case(request,tmp_path):
    from prosaic_harness import FileRunStore
    from prosaic_harness_postgres import PostgresRunStore
    from prosaic_runtime import RateCard
    from prosaic_runtime_postgres import PostgresRecorder
    import prosaic_integration_lab

    installed = importlib.metadata.distribution('prosaic-integration-lab')
    assert Path(prosaic_integration_lab.__file__).resolve() == installed.locate_file('prosaic_integration_lab/__init__.py').resolve()
    configuration = os.environ.get('LAB_MEMORY_FIXTURE')
    assert configuration, 'required fork qualification needs owned fixture infrastructure'
    fixture = json.loads(Path(configuration).read_text())
    namespace = 'castle-review-'+uuid.uuid4().hex
    store = (FileRunStore(tmp_path/'runs',namespace=namespace) if request.param == 'file'
             else PostgresRunStore(fixture['dsn'],namespace=namespace))
    recorder = PostgresRecorder(fixture['dsn'],namespace=namespace,environment='sandbox',
        rate_card=RateCard('castle-requirements-v1','requirements-fixture-v1','2','8','0.5'))
    try:
        yield fixture,namespace,store,recorder,tmp_path,request.param
    finally:
        store.close()


@pytest.mark.parametrize('case_id',[f'requirements-{n:02}' for n in range(1,9)])
@pytest.mark.parametrize('strategy',['direct','critic_author','sue'])
def test_actual_frozen_castle_hackathon_case_survives_source_removal(castle_case,case_id,strategy):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    from lab_runner.castle_requirements_v1 import capture_case,execute_frozen_case,project_case
    from lab_runner.requirements_review_v1.cases import load_cases
    from lab_runner.requirements_review_v1.fixtures import _dialogue,provider
    from prosaic_integration_lab.identity import Principal

    fixture,namespace,store,recorder,root,kind = castle_case
    owner = Principal('tenant-a','alice','payer-a')
    frozen = capture_case(case_id,worker_python=fixture['worker_python'],root=root/'castle',principal=owner,namespace=namespace)
    assert frozen['sources'][0]['provenance']['record_id'] == 'spec'
    assert frozen['sources'][0]['provenance']['wing'] == 'approved'
    assert frozen['capture']['namespace'] == namespace
    assert frozen['sources'][0]['text'].encode() == load_cases()[case_id]['sources'][0]['text'].encode()
    retained = deepcopy(frozen)
    # The worker was closed by capture. The selected corpus is now unavailable.
    shutil.rmtree(root/'castle')
    case,answer,_ = project_case(case_id,frozen)
    values = ([{'feedback':'Assess the frozen source against the supplied issue definitions.'}]
              if strategy == 'critic_author' else _dialogue(case) if strategy == 'sue' else []) + [answer]
    with provider(values) as (url,calls):
        config = RuntimeConfig({'fixture':EndpointConfig(url,'requirements-fixture-v1',features={'streaming':False})},
                               {},'fixture',allowed_tools=frozenset())
        report = execute_frozen_case(case_id,strategy,frozen=frozen,config=config,store=store,
                                    principal=owner,namespace=namespace,accounting=recorder)
    expected = {'direct':1,'critic_author':2,'sue':8}[strategy]
    assert report['score']['passed'] and all(report['score']['checks'].values())
    assert report['providerRequests'] == len(calls) == expected
    assert report['reportedTokens'] == expected*15 and report['usageComplete']
    assert report['replayAdditionalRequests'] == 0 and frozen == retained
    assert not (root/'castle').exists()
    for run_id in report['runIds']:
        observed = recorder.calls(run_id=run_id)
        assert observed
        assert all(row['intent']['context']['billing_account_id'] == 'payer-a' for row in observed)
    assert all(not row['request'].get('tools') for row in calls)
    directory = Path(fixture['evidence_directory'])/kind
    directory.mkdir(parents=True,exist_ok=True)
    (directory/(case_id+'--'+strategy+'.json')).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
