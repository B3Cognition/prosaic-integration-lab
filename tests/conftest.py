"""Credential-free native admission fixtures using only public SDK APIs."""
import json
import pytest


def _historical_sdk_environment():
    import os
    # Replicas receive neither the owner's DSN nor ambient provider credentials.
    allowed=('PATH','HOME','TMPDIR','TEMP','TMP','LANG','LC_ALL','SYSTEMROOT',
             'SSL_CERT_FILE','SSL_CERT_DIR')
    environment={k:os.environ[k] for k in allowed if k in os.environ}
    environment.update(NO_PROXY='*',no_proxy='*')
    return environment


@pytest.fixture(scope='session')
def legacy_sdk_python(tmp_path_factory):
    """Actual checksum-pinned pre-effort SDKs; never simulate or reseal receipts."""
    from pathlib import Path
    import os,subprocess,sys
    from prosaic_integration_lab.dependencies import cache_directory,verified_wheel_paths
    root=Path(__file__).resolve().parents[1]
    manifest=root/'dependencies/releases-pre-sent-effort-2026-11-08.json'
    environment=_historical_sdk_environment()
    environment.update(PIP_CONFIG_FILE=os.devnull,PIP_INDEX_URL='https://pypi.org/simple',PIP_DISABLE_PIP_VERSION_CHECK='1')
    def run(argv):
        result=subprocess.run([str(x) for x in argv],cwd=root,env=environment,
                              capture_output=True,text=True,timeout=240)
        assert result.returncode==0,result.stderr[-4000:]
    run([sys.executable,root/'scripts/prepare_dependencies.py','--manifest',manifest])
    wheels=verified_wheel_paths(manifest,cache_directory(manifest,root/'.cache/wheels'))
    directory=tmp_path_factory.mktemp('published-pre-sent-effort-sdk')
    run([sys.executable,'-m','venv',directory])
    python=directory/'bin/python'
    run([python,'-m','pip','install','--require-hashes','-r',root/'dependencies/requirements.lock'])
    run([python,'-m','pip','install','--no-deps',*wheels])
    run([python,'-m','pip','check'])
    run([python,'-I','-c',"from importlib.metadata import version; import sys, pathlib,prosaic_runtime; assert version('b3-prosaic-runtime')=='0.9.17'; assert pathlib.Path(prosaic_runtime.__file__).is_relative_to(pathlib.Path(sys.prefix))"])
    return python


@pytest.fixture
def create_legacy_receipts(legacy_sdk_python):
    from pathlib import Path
    import json,os,subprocess
    helper=Path(__file__).resolve().parent/'support/sent_effort_legacy.py'
    def create(**options):
        result=subprocess.run([str(legacy_sdk_python),'-I','-B',str(helper)],
            input=json.dumps({k:str(v) for k,v in options.items()}),capture_output=True,
            text=True,timeout=45,env=_historical_sdk_environment())
        assert result.returncode==0,result.stderr[-4000:]
        return json.loads(result.stdout)
    return create


@pytest.fixture
def proposal_text():
    return json.dumps({'definition': {'version': 1, 'start': 'ask', 'steps': {
        'ask': {'kind': 'pause', 'question': 'Accept žluť?', 'choices': {'yes': 'done'}},
        'done': {'kind': 'finish'}}}}, ensure_ascii=False)


@pytest.fixture
def bundle_factory():
    def make(version='v1', max_calls=12):
        from prosaic_harness import WorkflowBundle, WorkflowFactory, WorkflowCatalog, WorkflowBindings, WorkflowPolicy
        from prosaic_runtime import RuntimeConfig, EndpointConfig
        config = RuntimeConfig({'local': EndpointConfig('http://localhost:9/v1', 'synthetic')}, {}, 'local')
        return WorkflowBundle(version, WorkflowFactory(catalog=WorkflowCatalog(agents={}, schemas={}),
            bindings=WorkflowBindings(config=config), policy=WorkflowPolicy(max_calls=max_calls)))
    return make


@pytest.fixture
def prepared_v1(bundle_factory, proposal_text):
    return bundle_factory().prepare_json(proposal_text)


@pytest.fixture
def prepared_v2(bundle_factory, proposal_text):
    return bundle_factory('v2', max_calls=11).prepare_json(proposal_text)


@pytest.fixture
def prepared_finish(bundle_factory):
    return bundle_factory().prepare_json(
        '{"definition":{"version":1,"start":"done","steps":{"done":{"kind":"finish"}}}}')
