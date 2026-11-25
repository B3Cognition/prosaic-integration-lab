"""Explicit bounded invocations; successful responses do not verify live controls."""
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from lab_runner.live_allowance import SharedLiveAllowance
from . import EFFORTS, load_artifact, require_sdk
from .execution import execute_batch


def run(*, kind, config_path, profile, efforts, live=False, maximum=None,
        allowance_path=None, timeout_s=120, provenance=None):
    if live is not True:
        raise ValueError('live execution requires explicit opt-in')
    if (kind not in ('api', 'native') or not isinstance(efforts, (list, tuple))
            or not efforts or any(type(e) is not str or e not in EFFORTS for e in efforts)
            or len(set(efforts)) != len(efforts)):
        raise ValueError('select unique neutral efforts and an explicit adapter kind')
    if type(maximum) is not int or not len(efforts) <= maximum <= 12:
        raise ValueError('explicit allowance must cover selected efforts within 1..12')
    if (isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float))
            or not math.isfinite(timeout_s) or not 1 <= timeout_s <= 300):
        raise ValueError('timeout must be finite and within 1..300 seconds')
    if not isinstance(profile, str) or not profile:
        raise ValueError('explicit profile required')
    if allowance_path is None or not Path(allowance_path).is_absolute():
        raise ValueError('explicit absolute shared allowance path required')
    sdk = require_sdk()
    artifacts = [load_artifact(effort) for effort in efforts]
    if kind == 'api':
        supplied = sdk.RuntimeConfig.load(config_path)
        endpoint = supplied.profiles[profile]
        if (supplied.allowed_tools or supplied.tool_directories
                or endpoint.provider != 'openai-compatible'
                or endpoint.features.get('streaming') is not False
                or type(endpoint.max_tokens) is not int or not 1 <= endpoint.max_tokens <= 4096):
            raise ValueError('API reasoning config requires no tools, no streaming and at most 4096 output tokens')
        config = sdk.RuntimeConfig({profile: endpoint}, {}, profile, allowed_tools=frozenset())
        for artifact in artifacts:
            sdk.validate_execution_artifact(artifact, config)
        runtime = sdk.ProsaicRuntime(config)
        policy = sdk.RunPolicy(timeout_s=timeout_s, allowed_tools=frozenset(),
            max_provider_requests=1, max_tool_rounds=1, max_tool_calls=1)
    else:
        supplied = sdk.NativeRuntimeConfig.load(config_path)
        selected = supplied.profiles[profile]
        if selected.permission_mode != 'read-only':
            raise ValueError('native reasoning config requires a read-only profile')
        runtime = sdk.NativeRuntime(sdk.NativeRuntimeConfig({profile: selected}, default_profile=profile,
            capacity_file=supplied.capacity_file))
        policy = sdk.NativePolicy(permission_mode='read-only', timeout_s=timeout_s,
                                  max_input_bytes=8192, max_output_bytes=65536)
    allowance = SharedLiveAllowance(Path(allowance_path), max_calls=maximum)
    with TemporaryDirectory(prefix='lab-reasoning-live-') as temporary:
        report = execute_batch(runtime=runtime, artifacts=artifacts, kind=kind, profile=profile,
            policy=policy, allowance=allowance, cwd=temporary)
    report['provenance'] = provenance or {}
    return report
