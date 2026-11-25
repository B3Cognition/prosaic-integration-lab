"""The beginner example must run from a neutral directory using installed SDKs."""
import json
from pathlib import Path
import subprocess
import sys


def test_first_workflow_example_prepares_a_reviewable_workflow(tmp_path):
    example = Path(__file__).resolve().parents[2] / 'examples/first_workflow.py'
    child = subprocess.run([sys.executable, '-I', '-B', str(example)], cwd=tmp_path,
        capture_output=True, text=True, timeout=30)
    assert child.returncode == 0, child.stderr
    result = json.loads(child.stdout)
    assert result['status'] == 'prepared'
    assert result['steps'] == ['find', 'review', 'done', 'rejected']
    assert result['reviewChoices'] == ['accept', 'reject']
    assert result['query'] == 'Find the approved entity for the demo'
    assert isinstance(result['fingerprint'], str) and len(result['fingerprint']) >= 32
    assert not list(tmp_path.iterdir())
