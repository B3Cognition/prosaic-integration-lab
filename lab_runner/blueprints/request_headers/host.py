"""Host-owned benchmark headers; no run tag enters the model input."""
from dataclasses import replace
from pathlib import Path

from prosaic import inspect_artifact
from prosaic_runtime import ProsaicArtifact, ProsaicRuntime, RunPolicy, RuntimeConfig

PROJECT = Path(__file__).parent


def load_agent(project=PROJECT):
    result = inspect_artifact(Path(project), 'subagents/benchmark.md')
    if not result.get('ok'):
        raise ValueError('cannot inspect benchmark agent')
    return ProsaicArtifact.from_inspection(result['data'])


def build_runtime(*, project=PROJECT, base_url=None, custom_tools=None):
    project = Path(project)
    config = RuntimeConfig.load(project / 'runtime.yml')
    if base_url is not None:
        name = config.default_profile
        config = replace(config, profiles={**config.profiles, name: replace(config.profiles[name], base_url=base_url)})
    return ProsaicRuntime(config, source=project / '.prosaic', custom_tools=custom_tools or {})


def run_benchmark(runtime, artifact, arguments='', *, policy=None):
    return runtime.run(artifact, arguments, policy=policy or RunPolicy(max_provider_requests=1, max_tool_calls=0),
        request_headers={'x-tokenproxy-no-cache': '1'})


def turn_benchmark(runtime, artifact_or_prepared, **turn_options):
    # Every invocation gets a fresh host-owned mapping; never accept it from model input.
    return runtime.turn(artifact_or_prepared, request_headers={'x-tokenproxy-no-cache': '1'}, **turn_options)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='explicitly authorize a provider call')
    args = parser.parse_args()
    if not args.live:
        parser.error('--live is required to contact the configured endpoint')
    result = run_benchmark(build_runtime(), load_agent())
    if result.exit_code:
        raise SystemExit(result.exit_code)
    print(result.stdout)


if __name__ == '__main__':
    main()
