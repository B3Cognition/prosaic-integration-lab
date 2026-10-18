"""Public build includes the provider-neutral installed qualification driver."""
import json
from pathlib import Path
import runpy


def test_continuation_smoke_uses_public_build_inputs_and_both_provider_wires():
    root=Path(__file__).resolve().parents[2]
    inventory=json.loads((root/'dependencies/public-build-inputs.json').read_text())['files']
    assert 'scripts/continuation_budget_smoke.py' in inventory
    report=runpy.run_path(str(root/'scripts/continuation_budget_smoke.py'))['run']()
    assert report['scenarios']==14 and report['liveDispatches']==0
    assert {r['provider'] for r in report['results']}=={'openai-compatible','anthropic'}
    assert sum(r['providerRequests'] for r in report['results'])==24
    assert sum(r['toolCalls'] for r in report['results'])==6
    assert sum(not r['usageComplete'] for r in report['results'])==2
