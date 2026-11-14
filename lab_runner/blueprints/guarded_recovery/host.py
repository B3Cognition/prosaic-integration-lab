"""Trusted host setup for one guarded workflow step and one authorized lookup."""
import json
from pathlib import Path

from prosaic import inspect_artifact
from prosaic_harness import WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import CustomTool, EndpointConfig, Guard, ProsaicArtifact, RuntimeConfig, Verdict


def build_workflow(base_url, *, provider, lookup, authorize_lookup, rule_retries=2,
                   correct_malformed_tool_calls=True):
    root = Path(__file__).resolve().parent
    inspected = inspect_artifact(root, 'subagents/reviewer.md')
    if not inspected['ok']:
        raise ValueError('reviewer artifact could not be inspected')
    agent = ProsaicArtifact.from_inspection(inspected['data'])
    schema = {'type': 'object', 'properties': {'value': {'type': 'integer'}},
              'required': ['value'], 'additionalProperties': False}

    def verify_record(stage, context):
        try:
            output = json.loads(context.draft)
        except ValueError:
            return Verdict(False)
        return Verdict(len(context.tool_results) == 1 and output == context.tool_results[0])

    guard = Guard('verified_record', 'review-v1', ('final',), verify_record, fixes=True)
    tool = CustomTool('lookup', 'Read the one synthetic record', {'type': 'object', 'additionalProperties': False},
                      lookup, 'lookup-v1', authorize=authorize_lookup)
    config = RuntimeConfig({'fixture': EndpointConfig(base_url, 'synthetic', provider=provider,
        max_tokens=128, features={'streaming': False})}, {}, 'fixture', frozenset({'lookup'}))
    factory = WorkflowFactory(
        catalog=WorkflowCatalog(agents={'reviewer': agent}, schemas={'result': schema}),
        bindings=WorkflowBindings(config=config, guards=[guard], custom_tools={'lookup': tool},
            rule_retries=rule_retries, correct_malformed_tool_calls=correct_malformed_tool_calls),
        policy=WorkflowPolicy(allowed_agents={'reviewer'}, allowed_schemas={'result'},
            allowed_guards={'verified_record'}, allowed_tools={'lookup'}, max_calls=1,
            timeout_s=10, max_provider_requests_per_invocation=5, max_tool_calls_per_invocation=1),
    )
    return factory.build({'version': 1, 'name': 'guarded-recovery', 'start': 'review', 'steps': {
        'review': {'kind': 'agent', 'agent': 'reviewer', 'schema': 'result',
                   'tools': ['lookup'], 'initial_tool': 'lookup', 'next': 'done'},
        'done': {'kind': 'finish', 'requires': ['review']},
    }})
