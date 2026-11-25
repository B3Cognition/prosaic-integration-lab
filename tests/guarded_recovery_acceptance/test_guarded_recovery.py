"""Run the copied recovery host on both installed provider wires."""
import os
from pathlib import Path
import runpy
import sys

import pytest


@pytest.mark.parametrize('provider', ['openai-compatible', 'anthropic'])
def test_copied_guarded_recovery(tmp_path, provider):
    from lab_runner.parallel_tools import endpoint
    from prosaic_harness import Harness

    import lab_runner
    from lab_runner.blueprints import copy_blueprint
    if os.environ.get('PROSAIC_BLUEPRINT_INSTALLED') == '1':
        assert Path(lab_runner.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    project = copy_blueprint('guarded-recovery', tmp_path / 'guarded-recovery')
    build = runpy.run_path(str(project / 'host.py'))['build_workflow']
    authorized, reads = [], []
    def authorize(arguments):
        authorized.append(arguments)
        return True

    def lookup(arguments):
        reads.append(arguments)
        return {'value': 7}

    with endpoint(provider) as (url, requests, replies):
        def workflow(retries):
            return build(url, provider=provider, lookup=lookup, authorize_lookup=authorize,
                         rule_retries=retries)

        replies.extend([
            {'calls': [{'id': 'invalid', 'name': 'lookup', 'input': {'fixture': 'invalid'}}]},
            {'calls': [{'id': 'valid', 'name': 'lookup', 'input': {}}]},
            '{"value": 0}', '{"value": 1}', '{"value": 7}',
        ])
        path = tmp_path / 'owned-run'
        harness = Harness(workflow(2), path)
        state = harness.run({})
        assert state['status'] == 'completed' and state['calls'] == 1
        assert state['outputs']['review'] == {'value': 7}
        assert authorized == reads == [{}]
        assert len(requests) == 5 and requests[0]['tool_choice'] == requests[1]['tool_choice']

        receipt = harness.store.load_receipt('legacy', state['invocations'][0]['id'])
        metadata = receipt['result']['metadata']
        ids = metadata['workflow_rules_v1']['rules']['violated']
        assert ids
        assert metadata['guarded_recovery_v1'] == {
            'version': 1, 'ruleRetriesUsed': 2, 'rulesDeclined': ids, 'rulesRetried': ids,
            'toolRequestCorrections': ['argumentsSchema'],
        }
        assert Harness(workflow(2), path).resume()['status'] == 'completed'
        with pytest.raises(ValueError):
            Harness(workflow(1), path).resume()
        assert len(requests) == 5 and reads == [{}]


@pytest.mark.parametrize('provider', ['openai-compatible', 'anthropic'])
def test_guarded_bounded_tool_recovery(tmp_path, provider):
    import lab_runner
    from lab_runner.blueprints import copy_blueprint
    from lab_runner.parallel_tools import endpoint
    from prosaic_harness import Harness

    if os.environ.get('PROSAIC_BLUEPRINT_INSTALLED') == '1':
        assert Path(lab_runner.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    project = copy_blueprint('guarded-recovery', tmp_path / 'guarded-recovery')
    build = runpy.run_path(str(project / 'host.py'))['build_workflow']
    reads = []

    def lookup(arguments):
        reads.append(arguments)
        return {'value': 7}

    with endpoint(provider) as (url, requests, replies):
        def workflow():
            return build(url, provider=provider, lookup=lookup, authorize_lookup=lambda _: True,
                         bounded_tool_recovery=True)

        replies.extend([
            {'calls': [{'id': 'lookup-1', 'name': 'lookup', 'input': {}}]},
            '{"value": 7}',
        ])
        path = tmp_path / 'owned-run'
        harness = Harness(workflow(), path)
        state = harness.run({})
        assert (state['status'], state['reason']) == ('completed', None)
        assert state['calls'] == 1 and state['outputs']['review'] == {'value': 7}

        receipt = harness.store.load_receipt('legacy', state['invocations'][0]['id'])
        tool_events = [(event['event'], event['tool_version']) for event in receipt['events']
                       if event['event'] in {'tool_started', 'tool_completed'}]
        assert tool_events == [('tool_started', 'lookup-v1'), ('tool_completed', 'lookup-v1')]
        assert Harness(workflow(), path).resume()['status'] == 'completed'
        assert len(requests) == 2 and reads == [{}]
