"""One explicitly selected local model smoke invocation; no cloud fallback."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from prosaic_runtime import ProsaicRuntime, RunPolicy
from prosaic_runtime.config import RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = RuntimeConfig.load(ROOT / 'configs/runtime-local.example.yml')
    if any(urlsplit(profile.base_url).hostname not in {'127.0.0.1', 'localhost', '::1'} for profile in config.profiles.values()):
        raise ValueError('local smoke requires loopback profiles; cloud fallback forbidden')
    runtime = ProsaicRuntime(config, source=str(ROOT / 'assets'))
    result = runtime.run('subagents/author.md', 'Return a JSON object with result set to local smoke ok.',
                         policy=RunPolicy(timeout_s=60, max_tool_rounds=1))
    try:
        matched = json.loads(result.stdout) == {'result': 'local smoke ok'}
    except (ValueError, TypeError):
        matched = False
    print(json.dumps({'exit_code': result.exit_code, 'timed_out': result.timed_out,
                      'token_usage': result.token_usage, 'expected_output': matched}))
    return 0 if result.exit_code == 0 and matched else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit('Local smoke failed; secret-bearing diagnostics suppressed')
