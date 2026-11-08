"""Trusted diagnostic labels reach prepare(intent) before provider dispatch.

ALWAYS derive tenant/payer/run context from host authorization. NEVER bind labels
from model/client input as identity, retry permission or financial authority.
"""
from dataclasses import replace
from pathlib import Path

from prosaic import inspect_artifact
from prosaic_harness import WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import ExecutionContext, ProsaicArtifact, ProsaicRuntime, RunPolicy, RuntimeConfig

PROJECT = Path(__file__).resolve().parent


class LabelingRecorder:
    """Application recorder decorator; delegate storage and accounting semantics.

    on_prepare receives a copy of diagnostic labels, not prompts or raw requests.
    A callback/storage failure stops dispatch; it never authorizes a model retry.
    The backing recorder owns namespace, defaults, rates and durability.
    """
    def __init__(self, backend, on_prepare=None):
        self.backend, self.on_prepare = backend, on_prepare

    def __getattr__(self, name):
        return getattr(self.backend, name)

    def prepare(self, intent):
        labels = dict(intent['context'].get('request_metadata', {}).get('labels', {}))
        if self.on_prepare is not None:
            self.on_prepare(labels)
        return self.backend.prepare(intent)

    def observe(self, call_id, observation):
        return self.backend.observe(call_id, observation)


def trusted_context(*, tenant_id, billing_account_id, benchmark_run, variant, run_id=None):
    """Call only with identities/labels selected by the authenticated host."""
    return ExecutionContext(application_id='accounting-metadata-example', tenant_id=tenant_id,
        billing_account_id=billing_account_id, run_id=run_id,
        request_metadata={'run': benchmark_run, 'variant': variant})


def load_agent(project=PROJECT):
    result = inspect_artifact(Path(project), 'subagents/benchmark.md')
    if not result.get('ok'):
        raise ValueError('cannot inspect benchmark agent')
    return ProsaicArtifact.from_inspection(result['data'])


def build_runtime(*, project=PROJECT, base_url=None, provider=None, accounting=None,
                  custom_tools=None, guards=None):
    project = Path(project)
    config = RuntimeConfig.load(project/'runtime.yml')
    name = config.default_profile
    endpoint = config.profiles[name]
    changes = {}
    if base_url is not None: changes['base_url'] = base_url
    if provider is not None: changes['provider'] = provider
    tools = custom_tools or {}
    config = replace(config, profiles={**config.profiles, name: replace(endpoint, **changes)},
                     allowed_tools=frozenset(tools))
    runtime = ProsaicRuntime(config, source=project/'.prosaic', accounting=accounting,
                            custom_tools=tools, guards=guards)
    if 'accounting_request_metadata_v1' not in runtime.capabilities:
        raise ValueError('Runtime accounting_request_metadata_v1 is required')
    return runtime


def run_benchmark(runtime, agent, arguments='', *, context):
    return runtime.run(agent, arguments, context=context,
                       policy=RunPolicy(max_provider_requests=1, max_tool_calls=0))


def workflow(runtime, *, project=PROJECT):
    """Two finite calls separated by approval, with saved-context resume."""
    return WorkflowFactory(catalog=WorkflowCatalog(agents={'author': load_agent(project)},
        schemas={'result': {'type': 'object', 'properties': {'approved': {'type': 'boolean'}},
                            'required': ['approved'], 'additionalProperties': False}}),
        bindings=WorkflowBindings(config=runtime.config),
        policy=WorkflowPolicy(allowed_agents={'author'}, allowed_schemas={'result'},
            allowed_model_tiers={'fast'}, allow_agent_composition=True, max_calls=2,
            max_attempts=1, max_provider_requests_per_invocation=1, max_tool_calls_per_invocation=0)).build({
        'version': 1, 'name': 'accounting-metadata', 'start': 'first', 'steps': {
            'first': {'kind': 'agent', 'agent': 'author', 'schema': 'result', 'next': 'approval'},
            'approval': {'kind': 'pause', 'question': 'Continue?', 'choices': {'approve': 'second'}},
            'second': {'kind': 'agent', 'agent': 'author', 'schema': 'result', 'next': 'done'},
            'done': {'kind': 'finish'}}})


def public_view(state):
    """Example allowlisted view; never return raw Harness/operator state."""
    return {key: state[key] for key in ('status', 'calls') if key in state}


def main():
    import argparse
    from prosaic_runtime.accounting import MemoryRecorder
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='explicitly authorize one endpoint call')
    args = parser.parse_args()
    if not args.live:
        parser.error('--live is required to contact the configured endpoint')
    # Demonstration only. MemoryRecorder is non-durable and never a production ledger.
    backend = MemoryRecorder()
    recorder = LabelingRecorder(backend, lambda labels: print('Prepared variant:', labels.get('variant')))
    runtime = build_runtime(accounting=recorder)
    result = run_benchmark(runtime, load_agent(), context=trusted_context(
        tenant_id='operator-demo', billing_account_id='operator-demo', benchmark_run='demo-run', variant='baseline'))
    if result.exit_code: raise SystemExit(result.exit_code)
    print(result.stdout)


if __name__ == '__main__': main()
