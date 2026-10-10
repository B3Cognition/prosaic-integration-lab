"""Credential-free native admission fixtures using only public SDK APIs."""
import json
import pytest


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
