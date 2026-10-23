import json
from pathlib import Path

from lab_runner.gates import supports_conversation


def test_latest_timeout_patch_train_enables_required_conversation_gate():
    manifest = Path(__file__).resolve().parents[2] / 'dependencies/releases.json'
    assert supports_conversation(json.loads(manifest.read_text()))
