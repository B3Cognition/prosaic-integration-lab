"""Build and prepare a reviewable workflow using public SDKs; no execution.

Run with: python -I -B examples/first_workflow.py
Requires the released SDK train from dependencies/releases.json.
"""
import json

from prosaic import parse_artifact
from prosaic_harness import WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import EndpointConfig, ProsaicArtifact, RuntimeConfig


def main():
    # This approved Markdown material is host-owned. A larger application can
    # register artifacts inspected by Core instead of constructing one here.
    markdown = '''---
name: finder
description: Find an approved entity
tools: []
---
ALWAYS return one JSON object with entity_id. NEVER invent an entity.
'''
    finder = ProsaicArtifact.from_inspection({
        'id': 'approved/finder.md', 'type': 'subagent', **parse_artifact(markdown),
    })
    schema = {'type': 'object', 'properties': {'entity_id': {'type': 'string', 'maxLength': 64}},
        'required': ['entity_id'], 'additionalProperties': False}
    # Deliberately unusable illustrative endpoint: construction does not contact
    # it. Replace the binding and authorize execution in your own application.
    config = RuntimeConfig({'service': EndpointConfig('https://models.example.invalid/v1',
        'host-model', features={'streaming': False})}, {}, 'service', allowed_tools=frozenset())
    factory = WorkflowFactory(
        catalog=WorkflowCatalog(agents={'finder': finder}, schemas={'result': schema}),
        bindings=WorkflowBindings(config=config),
        policy=WorkflowPolicy(
            allowed_agents=frozenset({'finder'}), allowed_schemas=frozenset({'result'}),
            max_calls=1, max_attempts=1, timeout_s=30, max_tokens=256, max_run_s=60,
            max_provider_requests_per_invocation=1, max_tool_calls_per_invocation=0,
        ),
    )
    proposal = {'definition': {'version': 1, 'start': 'find', 'steps': {
        'find': {'kind': 'agent', 'agent': 'finder', 'schema': 'result', 'next': 'review'},
        'review': {'kind': 'pause', 'question': 'Accept the selected entity?',
            'choices': {'accept': 'done', 'reject': 'rejected'}, 'requires': ['find'],
            'response_schema': 'result'},
        'done': {'kind': 'finish', 'requires': ['find']},
        'rejected': {'kind': 'finish', 'outcome': 'rejected'},
    }}}
    workflow = factory.build_json(json.dumps(proposal))
    query = 'Find the approved entity for the demo'
    workflow.prepare_inputs({'query': query})
    print(json.dumps({'status': 'prepared', 'fingerprint': workflow.fingerprint,
        'steps': list(proposal['definition']['steps']),
        'reviewChoices': list(proposal['definition']['steps']['review']['choices']),
        'query': query}, indent=2))


if __name__ == '__main__':
    main()
