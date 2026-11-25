import json
from pathlib import Path
import stat
import pytest


def test_agent_profile_disables_thinking_without_mutating_shared_settings(tmp_path):
    from lab_runner.native_eval.local_server import prepare_agent_server_profile
    source=tmp_path/'source';source.mkdir()
    settings=b'{"auth":{"api_key":"synthetic-secret"},"cache":{"enabled":true}}'
    models={'version':1,'models':{'selected':{'temperature':0,'enable_thinking':True},'other':{'enable_thinking':True}}}
    (source/'settings.json').write_bytes(settings)
    (source/'model_settings.json').write_text(json.dumps(models))
    (source/'model_profiles.json').write_text('{"version":1,"profiles":{}}')
    destination=tmp_path/'owned'
    report=prepare_agent_server_profile(source,destination,'selected')
    assert (destination/'settings.json').read_bytes()==settings
    assert json.loads((destination/'model_settings.json').read_text())=={
        'version':1,'models':{'selected':{'temperature':0,'enable_thinking':False},'other':{'enable_thinking':True}}}
    assert json.loads((source/'model_settings.json').read_text())==models
    assert (destination/'model_profiles.json').read_bytes()==(source/'model_profiles.json').read_bytes()
    assert stat.S_IMODE(destination.stat().st_mode)==0o700
    assert all(stat.S_IMODE(p.stat().st_mode)==0o600 for p in destination.iterdir())
    assert report['enableThinking'] is False and report['model']=='selected'
    assert 'synthetic-secret' not in json.dumps(report)
    assert len(report['modelSettingsSha256'])==64
    with pytest.raises(FileExistsError):prepare_agent_server_profile(source,destination,'selected')


@pytest.mark.parametrize('problem',['unknown-model','invalid-settings','symlink'])
def test_agent_profile_rejects_invalid_sources_before_creating_destination(tmp_path,problem):
    from lab_runner.native_eval.local_server import prepare_agent_server_profile
    source=tmp_path/'source';source.mkdir()
    (source/'settings.json').write_text('{}')
    (source/'model_settings.json').write_text('{"version":1,"models":{"selected":{}}}')
    model='absent' if problem=='unknown-model' else 'selected'
    if problem=='invalid-settings':(source/'settings.json').write_text('[]')
    if problem=='symlink':
        (source/'model_settings.json').rename(source/'original.json')
        (source/'model_settings.json').symlink_to(source/'original.json')
    with pytest.raises(ValueError):prepare_agent_server_profile(source,tmp_path/'owned',model)
    assert not (tmp_path/'owned').exists()
