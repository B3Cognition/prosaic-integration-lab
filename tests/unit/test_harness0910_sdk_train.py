"""Exact cap-visibility release family, with historical trains retained."""
import hashlib
import json
from pathlib import Path
import pytest
from lab_runner.gates import COUNTS, required_modes, supports_conversation, supports_context_assembly, supports_consumer_blueprints

ROOT = Path(__file__).resolve().parents[2]
VERSIONS = {'b3-prosaic': '0.5.0', 'b3-prosaic-runtime': '0.9.14',
    'b3-prosaic-harness': '0.9.10', 'b3-prosaic-runtime-postgres': '0.3.0',
    'b3-prosaic-harness-postgres': '0.4.1'}

def manifest(changes=None):
    return {'artifacts': [{'distribution': k, 'version': v} for k, v in (VERSIONS | (changes or {})).items()]}

@pytest.mark.parametrize('gate', [supports_conversation, supports_context_assembly, supports_consumer_blueprints])
def test_exact_harness0910_family_retains_every_required_lane(gate):
    assert gate(manifest())
    assert required_modes(candidate=False, manifest=manifest()) == tuple(COUNTS)

@pytest.mark.parametrize('changes', [{'b3-prosaic-runtime': '0.9.13'}, {'b3-prosaic-harness': '0.9.11'},
    {'b3-prosaic': '0.5.1'}, {'b3-prosaic-harness-postgres': '0.4.0'}])
def test_unqualified_partial_or_future_families_are_refused(changes):
    with pytest.raises(ValueError, match='unsupported or incoherent'):
        supports_conversation(manifest(changes))

def test_prior_guarded_profile_remains_bound_to_its_original_manifest():
    from lab_runner.quality.sdk_provenance import qualified_sdk
    prior = qualified_sdk({'b3-prosaic': '0.5.0', 'b3-prosaic-runtime': '0.9.14', 'b3-prosaic-harness': '0.9.9'})
    archive = ROOT / 'dependencies/releases-pre-harness0910-2026-11-06.json'
    assert prior['manifestDigest'] == hashlib.sha256(archive.read_bytes()).hexdigest()
    assert prior == json.loads((ROOT / 'lab_runner/quality/data/sdk-provenance-pre-harness0910.json').read_bytes())
    current = json.loads((ROOT / 'dependencies/releases-pre-cerebro-2026-11-07.json').read_bytes())
    old = json.loads(archive.read_bytes())
    assert [a for a in old['artifacts'] if a['distribution'] != 'b3-prosaic-harness'] == [a for a in current['artifacts'] if a['distribution'] != 'b3-prosaic-harness']
