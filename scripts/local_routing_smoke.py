"""Explicit three-call loopback routing smoke through public WorkflowFactory/Harness."""
import argparse
from contextlib import contextmanager
import ipaddress
import json
import os
from pathlib import Path
import tempfile
import uuid
from urllib.parse import urlsplit

from prosaic_harness import (FileRunStore, Harness, WorkflowBindings, WorkflowCatalog,
    WorkflowFactory, WorkflowPolicy)
from prosaic_runtime import ProsaicArtifact, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]
TIERS = ('default', 'balanced', 'strong')
SCHEMA = {'type': 'object', 'properties': {'result': {'type': 'string', 'enum': ['routing ok']}},
    'required': ['result'], 'additionalProperties': False}


@contextmanager
def loopback_environment():
    """Standalone-script scope prevents urllib environment and system proxies."""
    saved = {name: value for name, value in os.environ.items() if name.lower().endswith('_proxy')}
    try:
        for name in saved:
            os.environ.pop(name, None)
        # A nonempty bypass environment suppresses macOS system proxy discovery.
        os.environ.update(no_proxy='*', NO_PROXY='*')
        yield
    finally:
        for name in list(os.environ):
            if name.lower().endswith('_proxy'):
                os.environ.pop(name, None)
        os.environ.update(saved)


def preflight(path, *, live_local, max_calls):
    """Validate all host configuration without opening a credential or endpoint."""
    if live_local is not True:
        raise ValueError('explicit --live-local opt-in is required')
    if type(max_calls) is not int or max_calls != 3:
        raise ValueError('exactly three shared calls must be authorized')
    config = RuntimeConfig.load(path)
    if not {'balanced', 'strong'} <= config.routes.keys():
        raise ValueError('balanced and strong routes are required')
    if config.allowed_tools or config.tool_directories:
        raise ValueError('local routing does not permit tools')
    for profile in config.profiles.values():
        url = urlsplit(profile.base_url)
        try:
            loopback = ipaddress.ip_address(url.hostname).is_loopback
        except ValueError:
            loopback = False
        if (not loopback or url.username or url.password or url.query or url.fragment or
                profile.provider != 'openai-compatible'):
            raise ValueError('local routing requires literal loopback HTTP(S) profiles')
        if (profile.api_key_env is not None or not isinstance(profile.api_key_file, str) or
                not profile.api_key_file.strip()):
            raise ValueError('local routing requires a secret-managed api_key_file')
        if (type(profile.max_tokens) is not int or not 0 < profile.max_tokens <= 512 or
                profile.features.get('streaming') is not False):
            raise ValueError('local routing requires finite output tokens and non-streaming profiles')
    if config.profiles[config.routes['balanced']].model == config.profiles[config.routes['strong']].model:
        raise ValueError('balanced and strong routes must select distinct models')
    return config


def create_factory(config, *, tiers, composition=False):
    """Trusted host bindings and independent tier/composition grants."""
    agents = {tier: ProsaicArtifact.from_inspection({'id': f'routing/{tier}.md',
        'type': 'subagent', 'frontmatter': {'name': tier, 'description': 'Bounded routing smoke',
            'tools': [], **({} if tier == 'default' else {'model_tier': tier})},
        'body': 'Return only the JSON object {"result":"routing ok"}. /no_think'}) for tier in TIERS}
    return WorkflowFactory(catalog=WorkflowCatalog(agents=agents, schemas={'result': SCHEMA}),
        bindings=WorkflowBindings(config=config), policy=WorkflowPolicy(
            allowed_agents=frozenset(agents), allowed_schemas=frozenset({'result'}),
            allowed_model_tiers=frozenset(tiers), allow_agent_composition=composition,
            max_calls=2 if composition else 1, max_attempts=1, max_visits=1,
            max_tokens=8192, max_run_s=120, timeout_s=60,
            max_provider_requests_per_invocation=1, max_tool_calls_per_invocation=0,
            max_output_bytes=8192, max_run_input_bytes=1024))


def proposal(tier):
    return {'definition': {'version': 1, 'start': 'ask', 'steps': {
        'ask': {'kind': 'agent', 'agent': tier, 'schema': 'result', 'next': 'done'},
        'done': {'kind': 'finish', 'requires': ['ask']}}}}


def recorded_evidence(state, receipt, *, expected_profile, expected_model):
    """Project only mutually consistent public checkpoint/receipt evidence."""
    row = {'completed': False, 'profile': None, 'request_model': None,
        'provider_requests': None, 'tool_calls': None, 'token_usage': None}
    if type(state) is not dict or type(receipt) is not dict:
        return row
    invocations = state.get('invocations')
    if (type(state.get('calls')) is not int or state['calls'] != 1 or
            type(invocations) is not list or len(invocations) != 1 or
            type(invocations[0]) is not dict or state.get('pending') is not None):
        return row
    invocation = invocations[0]
    if (invocation.get('status') != 'complete' or not isinstance(invocation.get('id'), str) or
            not isinstance(state.get('run_id'), str) or receipt.get('run_id') != state['run_id'] or
            receipt.get('id') != invocation['id'] or receipt.get('step') != 'ask' or
            receipt.get('step') != invocation.get('step') or
            not isinstance(receipt.get('sha256'), str) or receipt['sha256'] != invocation.get('receipt_sha256') or
            not isinstance(receipt.get('arguments_sha256'), str) or
            receipt['arguments_sha256'] != invocation.get('arguments_sha256')):
        return row
    result = receipt.get('result')
    if type(result) is not dict or type(result.get('metadata')) is not dict:
        return row
    metadata = result['metadata']
    budget = metadata.get('invocation_budgets_v1')
    if type(budget) is not dict:
        return row
    if type(budget.get('provider_requests')) is int and budget['provider_requests'] == 1:
        row['provider_requests'] = budget['provider_requests']
    if type(budget.get('tool_calls')) is int and budget['tool_calls'] == 0:
        row['tool_calls'] = budget['tool_calls']
    if metadata.get('profile') == expected_profile:
        row['profile'] = metadata['profile']
    if metadata.get('request_model') == expected_model:
        row['request_model'] = metadata['request_model']
    usage = result.get('token_usage')
    if (type(usage) is int and usage >= 0 and usage.bit_length() <= 256 and
            type(invocation.get('token_usage')) is int and invocation['token_usage'] == usage):
        row['token_usage'] = usage
    row['completed'] = (state.get('status') == 'completed' and type(result.get('exit_code')) is int and
        result['exit_code'] == 0 and result.get('timed_out') is False and
        row['profile'] is not None and row['request_model'] is not None and
        row['provider_requests'] == 1 and row['tool_calls'] == 0 and row['token_usage'] is not None and
        budget.get('usage_complete') is True and type(budget.get('reported_tokens')) is int and
        budget['reported_tokens'] == row['token_usage'])
    return row


@loopback_environment()
def smoke(path, *, live_local=False, max_calls=None):
    config = preflight(path, live_local=live_local, max_calls=max_calls)
    # Admit every case before Harness creates state or Runtime reads api_key_file.
    workflows = [(tier, create_factory(config,
        tiers=frozenset() if tier == 'default' else frozenset({tier})).build_json(json.dumps(proposal(tier))))
        for tier in TIERS]
    rows = []
    with tempfile.TemporaryDirectory(prefix='lab-local-routing-') as temporary:
        directory = Path(temporary).resolve()
        remaining = max_calls
        for tier, workflow in workflows:
            if remaining <= 0:
                raise ValueError('shared local call allowance exhausted')
            remaining -= 1  # Reserve before execution, including failed/uncertain requests.
            profile = config.default_profile if tier == 'default' else config.routes[tier]
            run_id = uuid.uuid4().hex
            with FileRunStore(directory / tier) as store:
                try:
                    Harness(workflow, store=store, run_id=run_id).run({})
                    # Read durable evidence through the public store before cleanup.
                    state = store.load_run(run_id).state
                    invocations = state.get('invocations')
                    receipt = None
                    if (type(invocations) is list and len(invocations) == 1 and
                            type(invocations[0]) is dict and isinstance(invocations[0].get('id'), str)):
                        receipt = store.load_receipt(run_id, invocations[0]['id'])
                    row = recorded_evidence(state, receipt, expected_profile=profile,
                        expected_model=config.profiles[profile].model)
                except Exception:
                    row = recorded_evidence({}, None, expected_profile=profile,
                        expected_model=config.profiles[profile].model)
            rows.append({'tier': tier, **row})
            if not row['completed']:
                break
    def total(field):
        values = [row[field] for row in rows]
        return sum(values) if values and all(type(value) is int for value in values) else None
    return {'event': 'local_routing_smoke', 'passed': len(rows) == 3 and all(r['completed'] for r in rows),
        'invocations_reserved': max_calls - remaining, 'provider_requests': total('provider_requests'),
        'tool_calls': total('tool_calls'), 'max_calls': 3,
        'max_provider_requests_per_invocation': 1, 'max_output_tokens': 512,
        'timeout_s': 60, 'cases': rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/runtime-local.example.yml')
    parser.add_argument('--live-local', action='store_true')
    parser.add_argument('--max-calls', type=int)
    args = parser.parse_args(argv)
    try:
        receipt = smoke(args.config, live_local=args.live_local, max_calls=args.max_calls)
    except Exception:
        # Credentials, model output and secret-bearing exception text stay private.
        receipt = {'event': 'local_routing_smoke', 'passed': False, 'failure': 'local_routing_failed'}
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
