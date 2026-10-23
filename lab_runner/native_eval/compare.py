"""Same Markdown and workspace inputs across installed native and API runtimes."""
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time

from lab_runner.live_allowance import SharedLiveAllowance
from .cases import CASE_IDS, SOURCE, prepare_case, grade
from .live import preflight
from .provenance import require_native
from .report import summarize
from .runner import sample


def planned_reservations(repetitions):
    # Two native attempts plus four API requests per case. This pilot deliberately
    # permits one repetition: multiple repeats need a separately planned allowance.
    if type(repetitions) is not int or repetitions != 1:
        raise ValueError('three-runtime pilot requires one repetition within 12 dispatch units')
    return 12


def resolve_local_timeout(value, *, default):
    value = default if value is None else value
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not 1 <= value <= 300):
        raise ValueError('local timeout must be finite and within 1..300 seconds')
    return value


def validate_local_config(local):
    from urllib.parse import urlsplit
    import ipaddress
    endpoint = local.profiles[local.default_profile]
    url = urlsplit(endpoint.base_url)
    if (url.scheme != 'http' or not ipaddress.ip_address(url.hostname).is_loopback
            or url.username or url.password or url.query or url.fragment
            or endpoint.api_key_env or not endpoint.api_key_file
            or endpoint.provider != 'openai-compatible'
            or type(endpoint.max_tokens) is not int or not 1 <= endpoint.max_tokens <= 2048
            or endpoint.features.get('streaming') is not False or local.tool_directories):
        raise ValueError('bounded secret-managed loopback local endpoint required')
    if ('read_file' not in local.allowed_tools
            or not {'write_file', 'edit_file'}.intersection(local.allowed_tools)):
        raise ValueError('local configuration must grant read and write tools')


def local_sample(runtime, case_id, workspace, *, timeout_s):
    timeout_s = resolve_local_timeout(None, default=timeout_s)
    sdk = require_native()
    artifact = prepare_case(case_id, workspace)
    inputs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in workspace.iterdir()}
    digest = hashlib.sha256(json.dumps({'body': artifact.body, 'inputs': inputs}, sort_keys=True).encode()).hexdigest()
    allowed = frozenset({'read_file', 'write_file', 'edit_file'})
    policy = sdk.RunPolicy(allowed_tools=allowed, read_roots=(str(workspace),),
        write_paths=(str(workspace / 'calculator.py'),) if case_id == 'repair' else (),
        timeout_s=timeout_s, max_tool_rounds=4, max_provider_requests=4, max_tool_calls=3,
        max_reported_tokens=16384)
    started = time.monotonic()
    timings = []
    def observe(event):
        # Public observer records contain no prompts, tool arguments or output.
        row = {key: event[key] for key in ('event', 'name', 'status', 'outcome',
            'reason', 'http_status', 'duration_ms') if key in event}
        row['elapsedMs'] = (time.monotonic() - started) * 1000
        timings.append(row)
    result = runtime.run(artifact, cwd=workspace, policy=policy, observer=observe)
    budget = result.metadata.get('invocation_budgets_v1', {})
    profile = runtime.config.profiles[runtime.config.default_profile]
    return {'selector': 'local', 'case': case_id, 'inputSha256': digest,
        'artifactSha256': hashlib.sha256((SOURCE / artifact.id).read_bytes()).hexdigest(),
        'selectedProfile': runtime.config.default_profile, 'backend': 'openai-compatible',
        'model': profile.model, 'passed': result.exit_code == 0 and grade(case_id, workspace, result.stdout),
        'completed': result.exit_code == 0, 'durationMs': (time.monotonic() - started) * 1000,
        'nativeAttempts': 0, 'providerRequests': budget.get('provider_requests'),
        'toolCalls': budget.get('tool_calls'), 'reportedTokens': result.token_usage,
        'failureReason': result.metadata.get('failure_reason'), 'recoveryRequired': False,
        'timedOut': result.timed_out, 'timeoutSeconds': timeout_s, 'timings': timings}


def run_comparison(*, native_config, local_config, selectors, output, provenance,
                   live=False, repetitions=1, timeout_s=60, local_timeout_s=None):
    if live is not True:
        raise ValueError('explicit live opt-in required')
    maximum = planned_reservations(repetitions)
    local_timeout_s = resolve_local_timeout(local_timeout_s, default=timeout_s)
    if len(selectors) != 2:
        raise ValueError('select exactly one Claude and one Codex profile')
    if 'local' in selectors:
        raise ValueError('local is reserved for the API comparison slot')
    readiness = preflight(config_path=native_config, selectors=selectors,
        repetitions=1, maximum=4, timeout_s=timeout_s)
    if not readiness['passed']:
        raise ValueError('native CLI preflight failed')
    sdk = require_native()
    config = sdk.NativeRuntimeConfig.load(native_config)
    if ({config.profiles[s].backend for s in selectors} != {'claude-code', 'codex-cli'}):
        raise ValueError('comparison requires Claude and Codex profiles')
    local = sdk.RuntimeConfig.load(local_config)
    validate_local_config(local)
    output = Path(output).resolve()
    output.mkdir(mode=0o700)
    allowance = SharedLiveAllowance(output / 'allowance.json', max_calls=maximum)
    native_runtime, local_runtime = sdk.NativeRuntime(config), sdk.ProsaicRuntime(local)
    rows = []
    with tempfile.TemporaryDirectory(prefix='workspaces-', dir=output) as temporary:
        for case_id in CASE_IDS:
            for selector in (*selectors, 'local'):
                token = allowance.reserve(maximum_requests=4 if selector == 'local' else 1)
                workspace = Path(temporary) / f'{case_id}-{selector}'
                workspace.mkdir()
                started = time.monotonic()
                try:
                    row = (local_sample(local_runtime, case_id, workspace, timeout_s=local_timeout_s)
                           if selector == 'local' else sample(native_runtime, selector, case_id, workspace, timeout_s=timeout_s))
                    observed = row.get('providerRequests') if selector == 'local' else row['nativeAttempts']
                    allowance.finish(token, actual_requests=observed)
                except Exception:
                    allowance.finish(token, actual_requests=None)
                    row = {'selector': selector, 'case': case_id, 'passed': False, 'completed': False,
                        'durationMs': (time.monotonic() - started) * 1000, 'nativeAttempts': 0,
                        'nativeAttemptsStatus': 'unknown' if selector != 'local' else 'not_applicable',
                        'providerRequests': None, 'reportedTokens': None, 'failureReason': 'execution_uncertain',
                        'recoveryRequired': True}
                rows.append(row)
                # Each row is synthetic filtered metrics; never output raw CLI logs or credentials.
                print(json.dumps({'event': 'comparison_sample', **row}), flush=True)
    report = summarize(rows, origin='live_three_runtime', provenance=provenance)
    report.update(allowance={'unit': 'native_attempt_or_local_provider_request', **allowance.status()},
        preflight=readiness, cleanup='verified', localMaxProviderRequestsPerAssignment=4,
        timeoutSecondsPerAssignment=timeout_s, localTimeoutSecondsPerAssignment=local_timeout_s,
        comparisonLimits=['Two tiny tasks, one trial each; no general model ranking.',
            'Same Markdown and inputs; vendor system prompts and tools differ.',
            'Native internal provider requests and exact tool authority are opaque.',
            'Local latency includes any model load; token counts are not directly comparable.'])
    with os.fdopen(os.open(output / 'report.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as target:
        json.dump(report, target, sort_keys=True, indent=2, allow_nan=False)
    return report
