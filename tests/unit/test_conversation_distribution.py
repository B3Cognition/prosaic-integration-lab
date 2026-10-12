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


def test_unit_and_functional_modules_collect_without_basename_collisions():
    import tomllib
    root=Path(__file__).resolve().parents[2]
    settings=tomllib.loads((root/'pyproject.toml').read_text())['tool']['pytest']['ini_options']
    assert '--import-mode=importlib' in settings.get('addopts','')


def test_ci_qualifies_distribution_and_an_actual_sdist_conversation_stack():
    root=Path(__file__).resolve().parents[2]
    workflow=(root/'.github/workflows/required-acceptance.yml').read_text()
    assert 'scripts/conversation_distribution_smoke.py' in workflow
    assert '--run-stack' in workflow and 'conversation-distribution-pg' in workflow
    assert '--mode conversation' in workflow
