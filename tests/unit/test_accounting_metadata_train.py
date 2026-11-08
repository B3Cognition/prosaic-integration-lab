"""Request labels require the complete qualified train and a copyable host."""
import pytest
import hashlib
import json
from pathlib import Path
from lab_runner.gates import supports_conversation, supports_context_assembly, supports_consumer_blueprints
from lab_runner.blueprints import copy_blueprint

VERSIONS = {'b3-prosaic': '0.5.0', 'b3-prosaic-runtime': '0.9.17', 'b3-prosaic-harness': '0.9.12',
            'b3-prosaic-runtime-postgres': '0.3.0', 'b3-prosaic-harness-postgres': '0.4.1'}


def manifest(changes=None):
    return {'artifacts': [{'distribution': k, 'version': v} for k, v in (VERSIONS | (changes or {})).items()]}


@pytest.mark.parametrize('gate', [supports_conversation, supports_context_assembly, supports_consumer_blueprints])
def test_complete_metadata_train_is_admitted(gate):
    assert gate(manifest())


@pytest.mark.parametrize('changes', [{'b3-prosaic-runtime': '0.9.18'}, {'b3-prosaic-harness': '0.9.11'},
    {'b3-prosaic-harness': '0.9.13'}, {'b3-prosaic-runtime-postgres': '0.3.1'}, {'b3-prosaic': '0.5.1'}])
def test_partial_metadata_train_is_refused(changes):
    with pytest.raises(ValueError, match='unsupported or incoherent'):
        supports_conversation(manifest(changes))


def test_metadata_blueprint_copies_with_no_provider_configuration_or_calls(tmp_path):
    project = copy_blueprint('accounting-metadata', tmp_path/'metadata')
    assert (project/'host.py').is_file()
    assert '127.0.0.1:9' in (project/'runtime.yml').read_text()
    assert '--live' in (project/'README.md').read_text()
    with pytest.raises(FileExistsError):
        copy_blueprint('accounting-metadata', project)


@pytest.mark.parametrize('path,sha', [
    ('dependencies/releases-pre-accounting-metadata-2026-11-08.json', '3f93bf5a6d9b570d14ba7280710e0844b81c64a8ba3a9f07a389decfca6236e3'),
    ('dependencies/releases-reasoning-pre-accounting-metadata-2026-11-08.json', '3f93bf5a6d9b570d14ba7280710e0844b81c64a8ba3a9f07a389decfca6236e3'),
    ('lab_runner/quality/data/sdk-provenance-pre-accounting-metadata.json', '7b9c0cbc280ec1ed8c958cb0ac8172ec514dcd34ee5e563f9bc8c1f8c82141e2'),
    ('lab_runner/memory/data/development-freeze-pre-accounting-metadata.json', '9206e16f1381158f8e9426573c2122c9cc347f2adcbe0ddfa02af89c5f205e0f'),
    ('lab_runner/memory/data/evaluation-freeze-pre-accounting-metadata.json', '63fdbdec6d87072d45e8f2bc3f7266b75d1a2bbde72a9bee5496066b297550c3'),
])
def test_pre_metadata_profile_snapshots_are_immutable(path, sha):
    assert hashlib.sha256((Path(__file__).resolve().parents[2]/path).read_bytes()).hexdigest() == sha


def test_previous_workflow_enforcement_profile_stays_registered_and_selectable():
    from lab_runner.quality.suite import resource
    from lab_runner.quality.sdk_provenance import qualified_sdk
    saved = json.loads(resource('sdk-provenance-pre-accounting-metadata.json'))
    assert saved['manifestDigest'] == '3f93bf5a6d9b570d14ba7280710e0844b81c64a8ba3a9f07a389decfca6236e3'
    assert qualified_sdk({'b3-prosaic': '0.5.0', 'b3-prosaic-runtime': '0.9.16', 'b3-prosaic-harness': '0.9.12'}) == saved
