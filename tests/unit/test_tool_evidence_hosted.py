import json
from pathlib import Path
import pytest


def test_tool_evidence_is_a_separate_24_case_lane():
    from lab_runner.gates import ALL_COUNTS,FAILURE_CASES
    from prosaic_integration_lab.tool_evidence import CASES
    assert ALL_COUNTS['tool-evidence']==24 and len(CASES)==12
    assert set(FAILURE_CASES['tool-evidence'])=={'test_tool_evidence['+case+'-'+provider+']' for case in CASES for provider in ('openai-compatible','anthropic')}


def test_feature_run_validation_does_not_relax_publish_sdk():
    from scripts.prepare_sdk_candidates import validate_run
    run=dict(head_sha='a'*40,conclusion='success',name='Tool contract candidate',path='.github/workflows/tool-contract-candidate.yml',event='workflow_dispatch')
    validate_run(run,'a'*40,tool_contracts=True)
    with pytest.raises(ValueError):validate_run(run,'a'*40)
    with pytest.raises(ValueError):validate_run(run,'b'*40,tool_contracts=True)


def test_mismatched_or_missing_manifest_refuses_before_stack_allocation(tmp_path,monkeypatch):
    import lab_runner.__main__ as cli
    monkeypatch.setattr(cli,'OwnedStack',lambda *a,**k:pytest.fail('allocated before preflight'))
    with pytest.raises(SystemExit):monkeypatch.setattr("sys.argv",["lab_runner",'test','--mode','tool-evidence','--candidate']);cli.main()
    path=tmp_path/'candidate.json';path.write_text('{}')
    with pytest.raises(SystemExit):monkeypatch.setattr("sys.argv",["lab_runner",'test','--mode','tool-evidence','--candidate','--candidate-manifest',str(path)]);cli.main()


def test_tool_contract_storage_is_enabled_only_by_owned_provisioner():
    root=Path(__file__).resolve().parents[2]
    stack=(root/'lab_runner/stack.py').read_text();provision=(root/'scripts/provision.py').read_text()
    assert "'tool_contracts':self.tool_contracts_fixture" in stack
    assert "config.get('tool_contracts') is True" in provision
    assert 'migrate_tool_contract_storage()' in provision
    worker=(root/'src/prosaic_integration_lab/conversation_execution.py').read_text()
    assert 'migrate_tool_contract_storage' not in worker


def test_failure_export_never_copies_payloads():
    from lab_runner.gates import export
    result=export(dict(mode='tool-evidence',failed_tests=['PRIVATE-ARG locator/password'],cleanup='verified',qualification='not_qualified'))
    assert 'PRIVATE' not in json.dumps(result) and result['failed_cases']==['unknown']


def paired_manifest():
    from prosaic_integration_lab.tool_evidence import TRAIN
    from lab_runner.tool_evidence import validate_tool_manifest
    pins={'b3-prosaic':'e858a853595746c6930fbe062e84bd8ece1a366aa3b126f2fe11bfb7cb2ceb81','b3-prosaic-runtime-postgres':'5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'}
    artifacts=[dict(distribution=name,version=version,filename=name.replace('-','_')+'-'+version+'-py3-none-any.whl',source_commit='a'*40,sha256=pins.get(name,'b'*64)) for name,version in TRAIN.items()]
    candidates=[]
    for sdk,names in [('runtime',{'b3-prosaic-runtime'}),('harness',{'b3-prosaic-harness','b3-prosaic-harness-postgres'})]:
        chosen=[item for item in artifacts if item['distribution'] in names]
        receipt=dict(source_commit='a'*40,distributions=[dict(name=item['distribution'],version=item['version']) for item in chosen],artifacts=[dict(filename=item['filename'],sha256=item['sha256']) for item in chosen])
        qualification=dict(source_commit='a'*40,exit_code=0,label='tool-contract-consumer',artifacts=receipt['artifacts'])
        candidates.append(dict(sdk=sdk,receipt=receipt,qualification=qualification))
    return dict(artifacts=artifacts,candidate_lineage=dict(version=1,kind='local-tool-contract-handoff',candidates=candidates,retained_artifacts=[item for item in artifacts if item['distribution'] in pins]))


@pytest.mark.parametrize('damage',['pair-source','wheel','qualification','recorder','kind'])
def test_paired_provenance_requires_matching_sources_and_original_bytes(damage):
    from lab_runner.tool_evidence import validate_tool_manifest
    data=paired_manifest();validate_tool_manifest(data)
    if damage=='pair-source':data['candidate_lineage']['candidates'][1]['receipt']['source_commit']='c'*40
    elif damage=='wheel':next(item for item in data['artifacts'] if item['distribution']=='b3-prosaic-runtime')['sha256']='c'*64
    elif damage=='qualification':data['candidate_lineage']['candidates'][0]['qualification']['exit_code']=1
    elif damage=='recorder':next(item for item in data['artifacts'] if item['distribution']=='b3-prosaic-runtime-postgres')['sha256']='c'*64
    else:data['candidate_lineage']['kind']='published'
    with pytest.raises(ValueError):validate_tool_manifest(data)


def test_required_lane_failure_and_cleanup_are_checked_without_releasing():
    root=Path(__file__).resolve().parents[2]
    runner=(root/'lab_runner/__main__.py').read_text()
    assert "result['skipped'] == 0" in runner and 'stack.stop()' in runner and "result['cleanup'] = 'verified'" in runner
    workflow=(root/'.github/workflows/tool-evidence.yml').read_text()
    assert 'ubuntu-24.04-arm' in workflow and "['16', '18']" in workflow
    assert 'tool-contracts' in workflow and 'Publish SDK' not in workflow


def test_cli_bootstraps_application_source_without_pytest_pythonpath(tmp_path):
    import os,subprocess,sys
    root=Path(__file__).resolve().parents[2];manifest=tmp_path/'invalid.json';manifest.write_text('{}')
    env={key:value for key,value in os.environ.items() if key!='PYTHONPATH'}
    result=subprocess.run([sys.executable,'-m','lab_runner','test','--mode','tool-evidence','--candidate','--candidate-manifest',str(manifest)],
        cwd=root,env=env,capture_output=True,text=True,timeout=15)
    assert result.returncode==2 and 'Traceback' not in result.stderr


def test_released_mode_requires_complete_stable_family_and_original_retained_bytes():
    from prosaic_integration_lab.tool_evidence import RELEASE_TRAIN
    from lab_runner.tool_evidence import validate_tool_manifest
    data=paired_manifest();data.pop('candidate_lineage')
    for item in data['artifacts']:item['version']=RELEASE_TRAIN[item['distribution']]
    validate_tool_manifest(data,candidate=False)
    data['artifacts'][0]['sha256']='0'*64
    with pytest.raises(ValueError):validate_tool_manifest(data,candidate=False)
