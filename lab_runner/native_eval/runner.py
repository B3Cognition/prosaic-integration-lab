"""Host-only consumer of the installed native Runtime, not a second agent loop."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import yaml

from .cases import CASE_IDS, SOURCE, prepare_case, grade
from .provenance import require_native
from .report import summarize


def validate_repetitions(value):
    if type(value) is not int or not 1 <= value <= 100:
        raise ValueError('repetitions must be 1..100')


def fixture_config(root, *, scenario='pass', same_quota=False):
    sdk = require_native()
    from . import fixture_cli
    source = Path(fixture_cli.__file__).read_text()
    profiles = {}
    for name, backend in [('claude', 'claude-code'), ('codex', 'codex-cli')]:
        selected = scenario if name == 'claude' else 'pass'
        script = root / (name + '-fixture')
        script.write_text(f'#!{sys.executable}\n' + source + f'\nraise SystemExit(main({backend!r}, {selected!r}))\n')
        script.chmod(0o700)
        profiles[name] = sdk.NativeProfile(backend, 'synthetic',
            'shared' if same_quota else name, str(script), permission_mode='workspace-write')
    return sdk.NativeRuntimeConfig(profiles, {'coding': sdk.ProfilePool(('claude', 'codex'))},
        default_pool='coding', capacity_file=str(root / 'capacity.json'))


def sample(runtime, selector, case_id, workspace, *, timeout_s=10):
    sdk = require_native()
    artifact = prepare_case(case_id, workspace)
    inputs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in workspace.iterdir() if p.is_file()}
    input_sha = hashlib.sha256(json.dumps({'body': artifact.body, 'inputs': inputs}, sort_keys=True).encode()).hexdigest()
    policy = sdk.NativePolicy(permission_mode='workspace-write' if case_id == 'repair' else 'read-only',
                              timeout_s=timeout_s)
    selection = {'profile': selector} if selector in runtime.config.profiles else {'pool': selector}
    started = time.monotonic()
    result = runtime.run(artifact, cwd=workspace, policy=policy, **selection)
    elapsed = (time.monotonic() - started) * 1000
    complete = result.exit_code == 0
    # Grade only the synthetic assignment; never execute generated Python.
    passed = complete and grade(case_id, workspace, result.stdout)
    return {'selector': selector, 'case': case_id, 'inputSha256': input_sha,
        'artifactSha256': hashlib.sha256((SOURCE / artifact.id).read_bytes()).hexdigest(),
        'selectedProfile': result.metadata.get('profile'), 'backend': result.metadata.get('backend'),
        'model': result.metadata.get('model'),
        'passed': passed, 'completed': complete, 'durationMs': elapsed,
        'nativeAttempts': len(result.metadata.get('native_execution_v1', {}).get('attempts', [])),
        'reportedTokens': result.token_usage,
        'knownReportedTokens': result.metadata.get('native_execution_v1', {}).get('known_tokens', 0),
        'failureReason': result.metadata.get('failure_reason'),
        'recoveryRequired': bool(result.metadata.get('recovery_required', False))}


def fixture_benchmark(*, repetitions=3, provenance=None):
    validate_repetitions(repetitions)
    sdk = require_native()
    rows = []
    with tempfile.TemporaryDirectory(prefix='lab-native-benchmark-') as temporary:
        root = Path(temporary)
        runtime = sdk.NativeRuntime(fixture_config(root))
        for repeat in range(repetitions):
            for case_id in CASE_IDS:
                for selector in ('claude', 'codex', 'coding'):
                    workspace = root / f'{repeat}-{case_id}-{selector}'
                    workspace.mkdir()
                    rows.append(sample(runtime, selector, case_id, workspace))
    report = summarize(rows, origin='scripted_fixture', provenance=provenance or {})
    report.update(liveInvocations=0, cleanup='verified')
    return report


def run_acceptance(*, provenance=None):
    sdk = require_native()
    checks = {}
    with tempfile.TemporaryDirectory(prefix='lab-native-acceptance-') as temporary:
        root = Path(temporary)
        for scenario, same_quota, expected in [
            ('quota', False, 'fallback'), ('quota', True, 'exhausted'),
            ('effect-quota', False, 'recovery'), ('malformed', False, 'failure')]:
            owned = root / scenario / str(same_quota)
            owned.mkdir(parents=True)
            config = fixture_config(owned, scenario=scenario, same_quota=same_quota)
            runtime = sdk.NativeRuntime(config)
            workspace = owned / 'workspace'
            workspace.mkdir()
            row = sample(runtime, 'coding', 'facts', workspace)
            if expected == 'fallback':
                checks['quota_fallback'] = row['passed'] and row['nativeAttempts'] == 2
                checks['unknown_usage_retained'] = row['reportedTokens'] is None
                document = owned / 'runtime.yml'
                document.write_text(yaml.safe_dump({'kind': 'native',
                    'profiles': {k: asdict(v) for k, v in config.profiles.items()},
                    'pools': {k: {'profiles': list(v.profiles)} for k, v in config.pools.items()},
                    'default_pool': 'coding', 'capacity_file': config.capacity_file}))
                code = ('import json,sys; from prosaic_runtime import NativeRuntime,NativeRuntimeConfig,NativePolicy,ProsaicArtifact;'
                    'r=NativeRuntime(NativeRuntimeConfig.load(sys.argv[1])).run('
                    'ProsaicArtifact("fixture","subagent",{},"done"),cwd=sys.argv[2],policy=NativePolicy());'
                    'print(json.dumps({"exit":r.exit_code,"profile":r.metadata.get("profile"),'
                    '"attempts":len(r.metadata["native_execution_v1"]["attempts"])}))')
                completed = subprocess.run([sys.executable, '-I', '-c', code, str(document), str(workspace)],
                    capture_output=True, text=True, timeout=15)
                observed = json.loads(completed.stdout) if completed.returncode == 0 else {}
                checks['cross_process_cooldown'] = observed == {'exit': 0, 'profile': 'codex', 'attempts': 1}
            elif expected == 'exhausted':
                checks['shared_quota_no_bypass'] = row['failureReason'] == 'capacity_unavailable' and row['nativeAttempts'] == 1
                next_row = sample(runtime, 'coding', 'facts', workspace)
                checks['all_exhausted_no_dispatch'] = next_row['failureReason'] == 'capacity_unavailable' and next_row['nativeAttempts'] == 0
            elif expected == 'recovery':
                checks['uncertain_effect_no_replay'] = row['recoveryRequired'] and row['nativeAttempts'] == 1 and (workspace / 'partial.txt').exists()
            else:
                checks['malformed_output_no_replay'] = not row['completed'] and row['nativeAttempts'] == 1
        checks['temporary_workspace_owned'] = root.exists()
    checks['temporary_workspace_cleanup'] = not root.exists()
    return {'suiteVersion': 'native-runtime-v1', 'origin': 'scripted_fixture',
        'passed': all(checks.values()), 'caseCount': len(checks), 'checks': checks,
        'cleanup': 'verified' if checks['temporary_workspace_cleanup'] else 'failed',
        'liveInvocations': 0, 'provenance': provenance or {}}
