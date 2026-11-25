"""Explicit native invocation admission; internal provider requests remain opaque."""
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

from lab_runner.live_allowance import SharedLiveAllowance
from .cases import CASE_IDS
from .provenance import require_native
from .runner import sample, validate_repetitions
from .report import summarize


class NativeAttemptAllowance:
    """Reuse the Lab's durable allowance, explicitly counting CLI attempts."""
    def __init__(self, path, *, maximum):
        self._allowance = SharedLiveAllowance(path, max_calls=maximum)

    def reserve(self, maximum):
        return self._allowance.reserve(maximum_requests=maximum)

    def finish(self, token, observed):
        self._allowance.finish(token, actual_requests=observed)

    def status(self):
        return {'unit': 'native_cli_attempts', **self._allowance.status()}


def validate_live_inputs(config_path, selectors, repetitions, maximum, timeout_s):
    validate_repetitions(repetitions)
    if config_path is None:
        raise ValueError('private native configuration required')
    path = Path(config_path)
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o077 or info.st_size > 65536):
        raise ValueError('owned private native configuration required')
    if type(maximum) is not int or not 1 <= maximum <= 12:
        raise ValueError('native attempt allowance must be 1..12')
    if (isinstance(timeout_s, bool) or not isinstance(timeout_s, (float, int))
            or not math.isfinite(timeout_s) or not 1 <= timeout_s <= 60):
        raise ValueError('native assignment timeout must be 1..60 seconds')
    if (not selectors or len(selectors) > 4 or len(set(selectors)) != len(selectors)
            or any(not isinstance(s, str) or not re.fullmatch('[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', s) for s in selectors)):
        raise ValueError('select 1..4 distinct native profiles/pools')


def preflight(*, config_path, selectors, repetitions, maximum, timeout_s):
    validate_live_inputs(config_path, selectors, repetitions, maximum, timeout_s)
    sdk = require_native()
    config = sdk.NativeRuntimeConfig.load(config_path)
    requirements = {}
    selected_names = set()
    for selector in selectors:
        if selector in config.profiles:
            names = (selector,)
        elif selector in config.pools:
            names = config.pools[selector].profiles
        else:
            raise ValueError('unknown native selector')
        # Every sample includes a write task; never weaken profile restrictions.
        if any(config.profiles[name].permission_mode != 'workspace-write' for name in names):
            raise ValueError('selected native profiles must explicitly permit the synthetic repair task')
        requirements[selector] = len(names)
        selected_names.update(names)
    worst_case = len(CASE_IDS) * repetitions * sum(requirements.values())
    if worst_case > maximum:
        raise ValueError('requested native benchmark exceeds its worst-case attempt allowance')
    versions = []
    for name in sorted(selected_names):
        profile = config.profiles[name]
        ready, parsed = False, None
        try:
            result = subprocess.run([profile.executable, '--version'], capture_output=True, text=True, timeout=5)
            match = re.search(r'\b(\d+)\.(\d+)\.(\d+)\b', result.stdout[:1024])
            if match:
                components = tuple(int(v) for v in match.groups())
                parsed = '.'.join(match.groups())
                minimum = (2, 1, 248) if profile.backend == 'claude-code' else (0, 154, 0)
                ready = result.returncode == 0 and components >= minimum
        except (OSError, subprocess.TimeoutExpired):
            pass
        versions.append({'profile': name, 'backend': profile.backend, 'version': parsed, 'ready': ready})
    fingerprint = hashlib.sha256(json.dumps(asdict(config), sort_keys=True).encode()).hexdigest()
    return {'passed': all(v['ready'] for v in versions), 'status': 'preflight',
        'liveInvocations': 0, 'providerRequests': None, 'authChecked': False,
        'configSha256': fingerprint, 'cliVersions': versions,
        'worstCaseNativeAttempts': worst_case, 'maximumNativeAttempts': maximum,
        'timeoutSecondsPerAssignment': timeout_s, 'attemptReservations': requirements}


def run_live(*, config_path, selectors, repetitions, maximum, timeout_s, output, provenance):
    readiness = preflight(config_path=config_path, selectors=selectors, repetitions=repetitions,
                          maximum=maximum, timeout_s=timeout_s)
    if not readiness['passed']:
        return {**readiness, 'status': 'blocked_cli_version', 'provenance': provenance}
    if output is None:
        raise ValueError('exclusive private live output directory required')
    output = Path(output).resolve()
    output.mkdir(mode=0o700)  # Existing directories cannot reset an allowance.
    sdk = require_native()
    config = sdk.NativeRuntimeConfig.load(config_path)
    fingerprint = hashlib.sha256(json.dumps(asdict(config), sort_keys=True).encode()).hexdigest()
    if fingerprint != readiness['configSha256']:
        raise ValueError('native configuration changed after preflight')
    runtime = sdk.NativeRuntime(config)
    allowance = NativeAttemptAllowance(output / 'allowance.json', maximum=maximum)
    rows = []
    stopped = False
    with tempfile.TemporaryDirectory(prefix='workspaces-', dir=output) as temporary:
        root = Path(temporary)
        for repeat in range(repetitions):
            for case_id in CASE_IDS:
                for selector in selectors:
                    token = allowance.reserve(readiness['attemptReservations'][selector])
                    workspace = root / f'{repeat}-{case_id}-{selector}'
                    workspace.mkdir()
                    try:
                        row = sample(runtime, selector, case_id, workspace, timeout_s=timeout_s)
                        allowance.finish(token, row['nativeAttempts'])
                    except Exception:
                        # An exception is not proof that no CLI was dispatched.
                        allowance.finish(token, None)
                        row = {'selector': selector, 'case': case_id, 'passed': False, 'completed': False,
                            'durationMs': 0, 'nativeAttempts': 0, 'nativeAttemptsStatus': 'unknown',
                            'reportedTokens': None, 'failureReason': 'execution_uncertain', 'recoveryRequired': True}
                    rows.append(row)
                    if not row['completed']:
                        stopped = True
                        break
                if stopped:
                    break
            if stopped:
                break
    report = summarize(rows, origin='live_native', provenance=provenance)
    report.update(status='stopped' if stopped else 'completed', allowance=allowance.status(),
                  preflight=readiness, cleanup='verified')
    with os.fdopen(os.open(output / 'report.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as target:
        json.dump(report, target, sort_keys=True, indent=2, allow_nan=False)
    return report
