"""Inspect effective caps and construct new sessions with explicit host policy."""
from dataclasses import replace
from pathlib import Path

from prosaic import inspect_artifact
from prosaic_harness import ConversationBindings, ConversationPolicy
from prosaic_runtime import ProsaicArtifact, RunPolicy, RuntimeConfig

PROJECT = Path(__file__).parent


def agent(project, name):
    result = inspect_artifact(Path(project), 'subagents/' + name + '.md')
    if not result.get('ok'):
        raise ValueError('cannot inspect conversation agent')
    return ProsaicArtifact.from_inspection(result['data'])


def build_bindings(*, project=PROJECT, base_url=None, max_input_bytes=8192,
                   run_max_input_bytes=None, interpretation_max_input_bytes=None):
    project = Path(project)
    config = RuntimeConfig.load(project / 'runtime.yml')
    if base_url is not None:
        name = config.default_profile
        config = replace(config, profiles={**config.profiles, name: replace(config.profiles[name], base_url=base_url)})
    return ConversationBindings(agent(project, 'assistant'), version='conversation-caps-v1', config=config,
        policy=ConversationPolicy(max_input_bytes=max_input_bytes, max_provider_requests=4, max_tool_calls=0),
        run_policy=RunPolicy(timeout_s=30, max_input_bytes=max_input_bytes if run_max_input_bytes is None else run_max_input_bytes,
            max_provider_requests=1, max_tool_calls=0),
        interpreter=agent(project, 'interpreter'),
        interpretation_policy=RunPolicy(timeout_s=30, max_tool_rounds=1,
            max_input_bytes=max_input_bytes if interpretation_max_input_bytes is None else interpretation_max_input_bytes,
            max_provider_requests=1, max_tool_calls=0))


def limits(bindings):
    return {'ordinary': bindings.effective_max_input_bytes,
            'interpretation': bindings.effective_interpretation_max_input_bytes}


if __name__ == '__main__':
    import json
    print(json.dumps(limits(build_bindings()), sort_keys=True))
