"""Repeated realistic tasks through the installed unified CLI, never a copied engine."""
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from lab_runner.live_allowance import SharedLiveAllowance
from .cases import SOURCE
from .compare import resolve_local_timeout, validate_local_config
from .live import preflight
from .realistic import summary, _private_json, check_local_readiness
from .realistic_cases import CASE_IDS, OUTPUTS, prepare, grade
from .unified import require_unified

STATES = ('all-eligible', 'claude-cooling', 'native-cooling')
EXCLUDED = {'all-eligible': (), 'claude-cooling': ('claude',),
            'native-cooling': ('claude', 'codex')}


def plan(repetitions, *, local_timeout_s=180):
    if type(repetitions) is not int or not 1 <= repetitions <= 3:
        raise ValueError('repetitions must be 1..3')
    local_timeout_s = resolve_local_timeout(local_timeout_s, default=180)
    return {'assignments': 9 * repetitions, 'maximumDispatchUnits': 81 * repetitions,
            'repetitions': repetitions, 'nativeTimeoutSeconds': 60,
            'localTimeoutSeconds': local_timeout_s, 'poolTimeoutSeconds': 300}


def schedule(repetitions):
    plan(repetitions)
    return [(i + 1, case, state) for i in range(repetitions)
            for case in CASE_IDS[i:] + CASE_IDS[:i] for state in STATES[i:] + STATES[:i]]


@contextmanager
def controlled_capacity(store, quotas, excluded):
    """Restore only marks owned by this experiment; never reset a provider mark."""
    owned = {}
    before = {name: store.status(key) for name, key in quotas.items()}
    try:
        for name in excluded:
            if before[name]['state'] == 'cooling_down':
                continue
            store.mark_unavailable(quotas[name], reason='unavailable', until=time.time() + 3600)
            owned[name] = store.status(quotas[name])
        yield {'excludedProfiles': list(excluded), 'capacityBefore': before,
               'controlledProfiles': list(owned)}
    finally:
        for name, mark in owned.items():
            if store.status(quotas[name]) == mark:
                store.mark_available(quotas[name])


def evaluate(case, workspace, result):
    completed = result['exit_code'] == 0
    outcome = grade(case, workspace)
    passed = completed and outcome['passed']
    return {'completed': completed, 'passed': passed, 'grade': outcome['checks'],
        'timedOut': result.get('timed_out', False),
        'recoveryRequired': bool(result['metadata'].get('recovery_required')),
        'failureReason': None if passed else 'contract_failed' if completed else
            result['metadata'].get('failure_reason', 'execution_failure')}


@contextmanager
def assignment_latency(row):
    started = time.monotonic()
    try:
        yield
    finally:
        row['durationMs'] = (time.monotonic() - started) * 1000


def summarize(rows):
    r = summary(rows)
    groups = r.pop('byBackend')
    for group in groups:
        selected = [row for row in rows if row['selector'] == group['selector']]
        group.update(fallbackAssignments=sum(any(e['event'] == 'profile_fallback' for e in row['events'])
                                            for row in selected),
            fallbackEvents=sum(e['event'] == 'profile_fallback' for row in selected for e in row['events']),
            profileSkips=sum(e['event'] == 'profile_skipped' for row in selected for e in row['events']),
            selectedProfiles=dict(Counter(row.get('selectedProfile') or 'none' for row in selected)),
            attemptProfiles=dict(Counter(a['profile'] for row in selected for a in row['attempts'])))
    r['byAvailability'] = groups
    actual = [dict(row, selector=row.get('selectedProfile') or 'none') for row in rows]
    r['bySelectedProfile'] = summary(actual)['byBackend']
    return r


def cli_command(config, case, workspace, *, local_timeout_s=180):
    local_timeout_s = resolve_local_timeout(local_timeout_s, default=180)
    return [sys.executable, '-I', '-m', 'prosaic_runtime.cli', f'subagents/{case}.md',
        '--source', str(SOURCE), '--config', str(config), '--cwd', str(workspace), '--events', '--quiet',
        '--timeout', '300', '--max-attempts', '3', '--max-native-attempts', '2',
        '--native-permissions', 'workspace-write', '--native-timeout', '60',
        '--enable-api', '--api-timeout', str(local_timeout_s), '--max-api-requests', '8',
        '--max-api-tool-calls', '7', '--max-tool-rounds', '8', '--max-api-reported-tokens', '65536',
        '--allow-tool', 'read_file', '--allow-tool', 'write_file', '--allow-tool', 'edit_file',
        '--read-root', str(workspace), '--write-path', str(workspace / OUTPUTS[case])]


def _invoke(command):
    env = dict(os.environ)
    for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', 'ANTHROPIC_BASE_URL'):
        env.pop(key, None)
    with subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=env, start_new_session=True) as process:
        try:
            stdout, _ = process.communicate(timeout=330)
        except BaseException as exc:
            # Interrupt our CLI first so Runtime can clean up its own vendor process.
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.communicate(timeout=10)
                except (subprocess.TimeoutExpired, KeyboardInterrupt):
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
            if isinstance(exc, subprocess.TimeoutExpired):
                raise RuntimeError('CLI outer guard expired; dispatch uncertain') from None
            raise
        events = [json.loads(line) for line in stdout.splitlines()]
        if not events or events[-1].get('event') != 'result':
            raise RuntimeError('CLI terminal result absent; dispatch uncertain')
        result = events[-1]
        if process.returncode != (0 if result['exit_code'] == 0 else 1):
            raise RuntimeError('CLI and result exit codes disagree')
        return result, [{k: event[k] for k in ('event', 'profile', 'reason') if k in event}
                        for event in events[:-1]]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_unified_benchmark(*, native_config, local_config, output, provenance,
                          live=False, repetitions=3, local_timeout_s=180):
    if live is not True:
        raise ValueError('explicit live opt-in required')
    experiment = plan(repetitions, local_timeout_s=local_timeout_s)
    local_timeout_s = experiment['localTimeoutSeconds']
    if output is None or native_config is None or local_config is None:
        raise ValueError('explicit output, native and local configuration paths required')
    sdk = require_unified()
    native = sdk.NativeRuntimeConfig.load(native_config)
    api = sdk.RuntimeConfig.load(local_config)
    validate_local_config(api)
    aliases = {kind: [name for name, profile in native.profiles.items() if profile.backend == backend]
               for kind, backend in [('claude', 'claude-code'), ('codex', 'codex-cli')]}
    if any(len(names) != 1 for names in aliases.values()) or len(native.profiles) != 2:
        raise ValueError('benchmark needs one direct Claude and one direct Codex profile')
    names = {name: values[0] for name, values in aliases.items()}
    names['local'] = api.default_profile
    readiness = preflight(config_path=native_config, selectors=[names['claude'], names['codex']],
                          repetitions=1, maximum=4, timeout_s=60)
    if not readiness['passed']:
        raise ValueError('native version preflight failed')
    check_local_readiness(api.profiles[names['local']])
    root = Path(output).resolve()
    root.mkdir(mode=0o700)
    for directory in ('samples', 'private-outputs', 'admissions'):
        (root / directory).mkdir(mode=0o700)
    config_path = root / 'unified.json'
    _private_json(config_path, {'kind': 'unified', 'native_config': str(Path(native_config).resolve()),
        'api_config': str(Path(local_config).resolve()), 'api_quota_keys': {names['local']: 'local-service'},
        'pools': {'agents': {'profiles': [names[k] for k in ('claude', 'codex', 'local')], 'cooldown_s': 300}},
        'default_pool': 'agents', 'capacity_file': str(root / 'capacity.json')})
    config = sdk.UnifiedRuntimeConfig.load(config_path)
    quotas = {kind: native.profiles[names[kind]].quota_key for kind in ('claude', 'codex')}
    quotas['local'] = config.api_quota_keys[names['local']]
    if len(set(quotas.values())) != 3:
        raise ValueError('comparison requires three distinct quota identities')
    capacity = sdk.CapacityStore(config.capacity_file)
    allowance = SharedLiveAllowance(root / 'allowance.json', max_calls=experiment['maximumDispatchUnits'], ceiling=243)
    frozen = {str(path): _sha(path) for path in [Path(native_config), Path(local_config),
        Path(__file__), Path(__file__).with_name('realistic_cases.py'),
        Path(__file__).with_name('__main__.py'), *[SOURCE / f'subagents/{c}.md' for c in CASE_IDS]]}
    with os.fdopen(os.open(root / 'driver.py', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as handle:
        handle.write(Path(__file__).read_bytes())
    _private_json(root / 'plan.json', {'suiteVersion': 'unified-cli-realistic-v1', **experiment,
        'provenance': provenance, 'preflight': readiness, 'sourceDigests': frozen,
        'modelProfiles': {**{k: {'model': p.model, 'effort': p.effort} for k, p in native.profiles.items()},
                          names['local']: {'model': api.profiles[names['local']].model}},
        'schedule': schedule(repetitions), 'profileAliases': names,
        'conditions': 'Controlled capacity exclusions, shared real cooldown state; no induced provider quota exhaustion.',
        'apiLimits': {'requests': 8, 'tools': 7, 'rounds': 8, 'reportedTokens': 65536},
        'nativePermission': 'workspace-write', 'apiWriteScope': 'exact task output',
        'nativeInternalProviderCalls': None})
    rows = []
    interrupted = False
    try:
        for trial, case, state in schedule(repetitions):
            if any(_sha(path) != digest for path, digest in frozen.items()):
                raise ValueError('frozen benchmark sources/configuration changed')
            reservation = allowance.reserve(maximum_requests=10 - len(EXCLUDED[state]))
            _private_json(root / 'admissions' / f'{len(rows)+1:02}.json',
                {'trial': trial, 'case': case, 'state': state,
                 'maximumDispatchUnits': 10 - len(EXCLUDED[state]), 'reservation': reservation})
            observed = None
            row = {'trial': trial, 'case': case, 'selector': state, 'sequence': len(rows) + 1,
                'passed': False, 'completed': False, 'attempts': [], 'events': [],
                'durationMs': 0,
                'artifactSha256': _sha(SOURCE / f'subagents/{case}.md'), 'selectedProfile': None,
                'localTimeoutSeconds': local_timeout_s, 'nativeTimeoutSeconds': 60, 'poolTimeoutSeconds': 300}
            try:
                with controlled_capacity(capacity, quotas, EXCLUDED[state]) as control:
                    row['capacityControl'] = control
                    with tempfile.TemporaryDirectory(prefix='workspace-', dir=root) as temporary:
                        workspace = Path(temporary)
                        artifact = prepare(case, workspace)
                        inputs = {p.name: _sha(p) for p in workspace.iterdir()}
                        row['inputSha256'] = hashlib.sha256(json.dumps({'body': artifact.body, 'inputs': inputs}, sort_keys=True).encode()).hexdigest()
                        with assignment_latency(row):
                            result, events = _invoke(cli_command(config_path, case, workspace,
                                local_timeout_s=local_timeout_s))
                        info = result['metadata']['unified_execution_v1']
                        native_count, api_count = info['native_attempts'], info['api_provider_requests']
                        if native_count is not None and api_count is not None:
                            observed = native_count + api_count
                        row.update(evaluate(case, workspace, result), events=events, attempts=info['attempts'],
                            selectedProfile=result['metadata'].get('profile'), unifiedExecution=info,
                            reportedTokens=result.get('token_usage'))
                        target = workspace / OUTPUTS[case]
                        if target.is_file() and not target.is_symlink() and target.stat().st_size <= 32768:
                            saved = root / 'private-outputs' / f'{row["sequence"]:02}-{OUTPUTS[case]}'
                            with os.fdopen(os.open(saved, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as handle:
                                handle.write(target.read_bytes())
                            row['outputSha256'] = _sha(saved)
            except KeyboardInterrupt:
                interrupted = True
                row.update(passed=False, failureReason='interrupted', exceptionType='KeyboardInterrupt', recoveryRequired=True)
                rows.append(row)
                _private_json(root / 'samples' / f'{row["sequence"]:02}.json', row)
                raise
            except Exception as exc:
                row.update(passed=False, failureReason='execution_uncertain', exceptionType=type(exc).__name__, recoveryRequired=True)
                interrupted = True
            finally:
                allowance.finish(reservation, actual_requests=observed)
            row.setdefault('durationMs', 0)
            rows.append(row)
            _private_json(root / 'samples' / f'{row["sequence"]:02}.json', row)
            print(json.dumps({'event': 'unified_benchmark_sample', **{k: row.get(k) for k in
                ('sequence', 'trial', 'case', 'selector', 'selectedProfile', 'passed', 'durationMs', 'failureReason')},
                'fallbackEvents': sum(e['event'] == 'profile_fallback' for e in row['events'])}), flush=True)
            if observed is None or interrupted:
                interrupted = True
                break
    finally:
        timeout_label = int(local_timeout_s) if local_timeout_s == int(local_timeout_s) else local_timeout_s
        same = all(len({(r['artifactSha256'], r.get('inputSha256')) for r in rows if r['case'] == case}) <= 1 for case in CASE_IDS)
        stable = all(_sha(path) == digest for path, digest in frozen.items())
        report = {'suiteVersion': 'unified-cli-realistic-v1', 'origin': 'live_repeated_unified_cli',
            'passed': len(rows) == experiment['assignments'] and not interrupted and same and stable and all(r['passed'] for r in rows),
            'sampleCount': len(rows), 'scheduledAssignments': experiment['assignments'],
            'interrupted': interrupted, 'sameInputsAcrossBackendsAndTrials': same,
            'frozenSourcesUnchanged': stable, 'samples': rows, **summarize(rows),
            'allowance': allowance.status(), 'allowanceUnit': 'native_cli_attempt_or_api_request',
            'providerQuotaExhaustionInduced': False, 'cleanup': 'verified' if not list(root.glob('workspace-*')) else 'failed',
            'provenance': provenance, 'limitations': ['Three trials per task and availability state.',
                f'Native 60s, local {timeout_label}s, pool total 300s.', 'Controlled skips differ from provider-triggered fallback.',
                'No concurrent test load or deliberate warmup; cache and host state uncontrolled.',
                'Native provider loops opaque; factual contracts graded, prose quality ungraded.']}
        _private_json(root / 'report.json', report)
    return report
