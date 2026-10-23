"""Owned synthetic CLI stand-in. No network, credentials or model execution."""
import json
from pathlib import Path
import sys


def main(backend, scenario):
    if '--version' in sys.argv:
        print('2.1.248' if backend == 'claude-code' else '0.154.0')
        return 0
    prompt = sys.stdin.read()
    def emit(value):
        print(json.dumps(value), flush=True)
    if scenario == 'malformed':
        print('{bad output}')
        return 1
    if scenario in {'quota', 'effect-quota'}:
        if scenario == 'effect-quota':
            Path('partial.txt').write_text('partial synthetic effect')
            if backend == 'claude-code':
                emit({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit'}]}})
            else:
                emit({'type': 'item.started', 'item': {'type': 'command_execution'}})
        if backend == 'claude-code':
            emit({'type': 'rate_limit_event', 'rate_limit_info': {'status': 'rejected'}})
            emit({'type': 'result', 'is_error': True, 'num_turns': 0 if scenario == 'quota' else 1})
        else:
            emit({'type': 'turn.failed', 'error': {'message': "You've hit your usage limit. Try later."}})
        return 1
    if 'inventory.json' in prompt:
        inventory = json.loads(Path('inventory.json').read_text())
        answer = json.dumps({'total': sum(inventory['counts']),
                             'decision': 'BLOCK' if inventory['blockingIssue'] else 'APPROVE'})
    elif 'calculator.py' in prompt:
        Path('calculator.py').write_text('def add(a, b):\n    return a + b\n')
        answer = 'fixed'
    else:
        answer = 'done'
    if backend == 'claude-code':
        emit({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': answer,
              'usage': {'input_tokens': 5, 'output_tokens': 2}})
    else:
        emit({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': answer}})
        emit({'type': 'turn.completed', 'usage': {'input_tokens': 5, 'output_tokens': 2}})
    return 0
