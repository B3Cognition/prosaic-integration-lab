import json
from pathlib import Path

import pytest


def test_public_build_accepts_complete_conversation_inventory():
    from scripts.build_consumer import public_file_allowed
    root=Path(__file__).resolve().parents[2]
    inventory=json.loads((root/'dependencies/public-build-inputs.json').read_text())['files']
    assert 'configs/conversation-conformance.example.json' in inventory
    assert all(public_file_allowed(name) for name in inventory)
    assert all((root/name).is_file() for name in inventory)


@pytest.mark.parametrize('filename',['configs/private.json','/private/workspace.json',
    'configs/../private.json','configs/runtime-local.private.yml','.lab/host.json'])
def test_conversation_recipe_does_not_broaden_secret_build_inputs(filename):
    from scripts.build_consumer import public_file_allowed
    assert public_file_allowed(filename) is False


def test_sdist_explicitly_includes_conformance_recipe_and_preview_docs():
    root=Path(__file__).resolve().parents[2]
    manifest=(root/'MANIFEST.in').read_text()
    assert 'include configs/conversation-conformance.example.json' in manifest
    assert (root/'docs/conversations.md').is_file()
