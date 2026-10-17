import importlib.util
import json
from pathlib import Path


def test_scoped_installed_smoke_has_complete_public_build_inputs(tmp_path):
    root=Path(__file__).resolve().parents[2]
    inventory=json.loads((root/'dependencies/public-build-inputs.json').read_text())['files']
    required={'lab_runner/memory_policy/'+name for name in
        ('__init__.py','scoped.py','assembly.py','budget.py','native.py','trace.py')}
    assert required|{'scripts/scoped_memory_smoke.py'}<=set(inventory)
    spec=importlib.util.spec_from_file_location('scoped_smoke',root/'scripts/scoped_memory_smoke.py')
    smoke=importlib.util.module_from_spec(spec);spec.loader.exec_module(smoke)
    result=smoke.run(tmp_path)
    assert result['scenarios']==9 and result['providerRequests']==15 and result['toolCalls']==7
    assert result['replayAdditionalRequests']==0 and result['traceBytesPreserved'] is True
