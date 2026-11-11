import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


def test_public_build_snapshot_can_capture_and_serve_generation_without_checkout_imports(tmp_path):
    root=Path(__file__).resolve().parents[2]
    snapshot=tmp_path/'public-build';snapshot.mkdir()
    inventory=json.loads((root/'dependencies/public-build-inputs.json').read_bytes())['files']
    for name in inventory:
        target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,target)
    script='''
import asyncio,sys
from pathlib import Path
root=Path(sys.argv[1]);sys.path[:0]=[str(root),str(root/'src')]
from prosaic_integration_lab.run_observations import RunObservations
assert RunObservations().snapshot('missing')['generation']['calls']==[]
from lab_runner import model
model.scenario='conversation'
response=model.completions({'model':'test-model-balanced','stream':True,'messages':[]})
async def consume():
    frames=[part async for part in response.body_iterator]
    assert frames[-1]=='data: [DONE]\\n\\n'
    assert len(frames)>4
asyncio.run(consume())
'''
    result=subprocess.run([sys.executable,'-I','-c',script,str(snapshot)],cwd=tmp_path,
        capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr


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
