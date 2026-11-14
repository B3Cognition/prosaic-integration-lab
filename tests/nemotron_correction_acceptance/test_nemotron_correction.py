"""Verify the installed blueprint and native recovery wire without live inference."""
from importlib.metadata import version
import os
from pathlib import Path
import runpy
import sys

import pytest

from lab_runner.blueprints import copy_blueprint
from lab_runner.parallel_tools import endpoint
from prosaic_harness import Harness


@pytest.mark.parametrize('mode', ['optional', 'required', 'ignored', 'ungrounded'])
def test_copied_nemotron_correction(tmp_path, mode):
    import lab_runner
    if os.environ.get('PROSAIC_BLUEPRINT_INSTALLED') == '1':
        assert Path(lab_runner.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
        assert version('b3-prosaic-runtime') == '0.9.26'
        assert version('b3-prosaic-harness') == '0.9.19'
    project = copy_blueprint('nemotron-correction', tmp_path / 'copy')
    build = runpy.run_path(str(project / 'host.py'))['build_workflow']
    authorized, reads = [], []

    def authorize(args):
        authorized.append(args)
        return True

    def lookup(args):
        reads.append(args)
        return {'value': 7}

    with endpoint('openai-compatible') as (url, requests, replies):
        workflow = build(url, lookup=lookup, authorize_lookup=authorize,
                         require_lookup=mode == 'required')
        replies.append({'calls': [{'id': 'invalid', 'name': 'lookup', 'input': {'extra': True}}]})
        if mode == 'ignored':
            replies.append('{"value": 7}')
        else:
            replies.append({'calls': [{'id': 'valid', 'name': 'lookup', 'input': {}}]})
            replies.append('{"value": 0}' if mode == 'ungrounded' else '{"value": 7}')
        path = tmp_path / 'owned-run'
        harness = Harness(workflow, path)
        state = harness.run({})
        assert state['calls'] == 1 and not replies
        completed = mode in ('optional', 'required')
        assert state['status'] == ('completed' if completed else 'blocked')
        assert state['outputs'].get('review') == ({'value': 7} if completed else None)
        assert authorized == reads == ([] if mode == 'ignored' else [{}])
        assert len(requests) == (2 if mode == 'ignored' else 3)
        assert 'structured_outputs' not in requests[0]
        assert requests[1]['structured_outputs'] == {
            'choice': ['<tool_call>\n<function=lookup>\n</function>\n</tool_call>'],
        }
        assert requests[0]['tool_choice'] == requests[1]['tool_choice'] == (
            {'type': 'function', 'function': {'name': 'lookup'}} if mode == 'required' else 'auto')
        if mode != 'ignored':
            assert 'structured_outputs' not in requests[2]
            assert any(m['role'] == 'tool' for m in requests[2]['messages'])
        if mode == 'ungrounded':
            assert state['reason'] == 'rule_violation'
        receipt = harness.store.load_receipt('legacy', state['invocations'][0]['id'])
        recovery = receipt['result']['metadata']['guarded_recovery_v1']
        assert recovery['toolRequestCorrections'] == ['argumentsSchema']
        assert recovery['ruleRetriesUsed'] == 0
        if completed:
            assert Harness(workflow, path).resume()['outputs'] == state['outputs']
            assert len(requests) == 3 and reads == [{}]
