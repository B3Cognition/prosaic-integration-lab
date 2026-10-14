"""Candidate curation binds exact source, artifact bytes and upstream lineage."""
import hashlib
import json
from pathlib import Path

import pytest


def serialized(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def test_retained_dependency_helper_bootstraps_from_source_outside_pytest(tmp_path):
    import subprocess,sys
    script=Path(__file__).resolve().parents[2]/'scripts/prepare_sdk_candidates.py'
    source="""
import importlib.util,sys
spec=importlib.util.spec_from_file_location('candidate_probe',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from scripts.prepare_dependencies import prepare
assert callable(prepare)
"""
    result=subprocess.run([sys.executable,'-I','-B','-c',source,str(script)],cwd=tmp_path,
        capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr


@pytest.fixture
def candidate_set(tmp_path,request):
    # Structural fixture for the planned conversation train; these are never qualification receipts.
    expected_versions={
        'B3Cognition/prosaic':{'b3-prosaic':'0.4.1'},
        'B3Cognition/prosaic-runtime':{'b3-prosaic-runtime':'0.9.0','b3-prosaic-runtime-postgres':'0.3.0'},
        'B3Cognition/prosaic-harness':{'b3-prosaic-harness':'0.8.0','b3-prosaic-harness-postgres':'0.3.0'}}
    if getattr(request,'param',None)=='context':
        expected_versions['B3Cognition/prosaic-runtime']['b3-prosaic-runtime']='0.9.4'
        expected_versions['B3Cognition/prosaic-harness']={'b3-prosaic-harness':'0.9.0','b3-prosaic-harness-postgres':'0.4.0'}
    candidates=[]
    for index,(repository,expected) in enumerate(expected_versions.items()):
        directory=tmp_path/str(index);directory.mkdir()
        artifacts=[]
        for name,version in expected.items():
            for suffix in ('-py3-none-any.whl','.tar.gz'):
                filename=name.replace('-','_')+'-'+version+suffix
                payload=(filename+' immutable bytes').encode();(directory/filename).write_bytes(payload)
                artifacts.append({'filename':filename,'sha256':hashlib.sha256(payload).hexdigest()})
        receipt={'version':1,'source_commit':str(index+1)*40,
            'distributions':[{'name':name,'version':version,'requires_python':'>=3.11','dependencies':[]}
                             for name,version in expected.items()], 'artifacts':artifacts}
        (directory/'release-receipt.json').write_bytes(serialized(receipt))
        candidate={'repository':repository,'run_id':str(index+1),'source_commit':receipt['source_commit'],
            'receipt_sha256':hashlib.sha256(serialized(receipt)).hexdigest(),'receipt':receipt,
            'wheels':[item for item in artifacts if item['filename'].endswith('.whl')]}
        if index:
            upstream={'version':1,'candidates':candidates.copy()}
            (directory/'upstream-receipt.json').write_bytes(serialized(upstream))
            candidate.update(upstream_receipt=upstream,upstream_sha256=hashlib.sha256(serialized(upstream)).hexdigest())
        candidates.append(candidate)
    return [tmp_path/str(index) for index in range(3)],candidates


@pytest.mark.parametrize('candidate_set',['context'],indirect=True)
@pytest.mark.parametrize('corrupt',[False,True])
def test_context_train_keeps_original_adapter_bytes(candidate_set,tmp_path,monkeypatch,corrupt):
    import scripts.prepare_sdk_candidates as cli
    directories,candidates=candidate_set
    original=tmp_path/'original.whl';original.write_bytes(b'original published adapter')
    retained={'distribution':'b3-prosaic-runtime-postgres','version':'0.3.0',
        'filename':'b3_prosaic_runtime_postgres-0.3.0-py3-none-any.whl',
        'sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'source_commit':'a'*40}
    monkeypatch.setattr(cli,'retained_runtime_postgres',lambda cache:(retained,original))
    if corrupt:original.write_bytes(b'changed original')
    arguments=[(c['repository'],c['run_id'],c['source_commit'],d) for c,d in zip(candidates,directories)]
    manifest=tmp_path/'context.json'
    if corrupt:
        with pytest.raises(ValueError,match='bytes differ'):cli.curate(arguments,manifest,tmp_path/'cache',context_assembly=True)
        assert not manifest.exists()
    else:
        data=cli.curate(arguments,manifest,tmp_path/'cache',context_assembly=True)
        assert next(a for a in data['artifacts'] if a['distribution']==retained['distribution'])==retained
        assert data['candidate_lineage']['retained_artifacts']==[retained]
        from prosaic_integration_lab.dependencies import cache_directory
        assert (cache_directory(manifest,tmp_path/'cache')/retained['filename']).read_bytes()==original.read_bytes()


def test_candidates_curate_only_exact_five_verified_wheels(candidate_set,tmp_path):
    from scripts.prepare_sdk_candidates import curate
    directories,candidates=candidate_set
    manifest=tmp_path/'manifest.json';cache=tmp_path/'cache'
    data=curate([(candidate['repository'],candidate['run_id'],candidate['source_commit'],directory)
                 for candidate,directory in zip(candidates,directories)],manifest,cache)
    assert len(data['artifacts'])==5
    from prosaic_integration_lab.dependencies import cache_directory,verified_wheel_paths
    assert len(verified_wheel_paths(manifest,cache_directory(manifest,cache)))==5
    assert all(item['distribution'].startswith('b3-') for item in data['artifacts'])
    assert {item['distribution']:item['version'] for item in data['artifacts']}=={
        'b3-prosaic':'0.4.1','b3-prosaic-runtime':'0.9.0','b3-prosaic-runtime-postgres':'0.3.0',
        'b3-prosaic-harness':'0.8.0','b3-prosaic-harness-postgres':'0.3.0'}


@pytest.mark.parametrize('version',['0.8.1','0.10.0'])
def test_old_or_unapproved_runtime_train_rejected(candidate_set,tmp_path,version):
    from scripts.prepare_sdk_candidates import curate
    directories,candidates=candidate_set
    receipt_path=directories[1]/'release-receipt.json'
    receipt=json.loads(receipt_path.read_text())
    receipt['distributions'][0]['version']=version
    receipt_path.write_bytes(serialized(receipt))
    with pytest.raises(ValueError,match='distribution'):
        curate([(candidate['repository'],candidate['run_id'],candidate['source_commit'],directory)
            for candidate,directory in zip(candidates,directories)],tmp_path/'manifest.json',tmp_path/'cache')
    assert not (tmp_path/'manifest.json').exists()


def test_candidate_wrong_source_or_wheel_hash_never_creates_selected_manifest(candidate_set,tmp_path):
    from scripts.prepare_sdk_candidates import curate
    directories,candidates=candidate_set
    arguments=[(candidate['repository'],candidate['run_id'],candidate['source_commit'],directory)
               for candidate,directory in zip(candidates,directories)]
    manifest=tmp_path/'manifest.json';cache=tmp_path/'cache'
    path=directories[1]/candidates[1]['wheels'][0]['filename'];path.write_bytes(b'changed')
    with pytest.raises(ValueError):curate(arguments,manifest,cache)
    assert not manifest.exists()


def test_candidate_runtime_and_harness_must_bind_chosen_upstream_candidates(candidate_set,tmp_path):
    from scripts.prepare_sdk_candidates import curate
    directories,candidates=candidate_set
    upstream=json.loads((directories[2]/'upstream-receipt.json').read_text())
    upstream['candidates'][1]['run_id']='999'
    (directories[2]/'upstream-receipt.json').write_bytes(serialized(upstream))
    with pytest.raises(ValueError,match='lineage'):
        curate([(candidate['repository'],candidate['run_id'],candidate['source_commit'],directory)
                for candidate,directory in zip(candidates,directories)],tmp_path/'manifest.json',tmp_path/'cache')


@pytest.mark.parametrize('changes',[{'conclusion':'failure'},{'head_sha':'a'*40},
    {'event':'pull_request'},{'name':'other'},{'path':'other.yml'}])
def test_unqualified_run_metadata_cannot_supply_candidate_bytes(changes):
    from scripts.prepare_sdk_candidates import validate_run
    run={'conclusion':'success','head_sha':'1'*40,'event':'workflow_dispatch',
         'name':'Publish SDK','path':'.github/workflows/publish.yml'}
    validate_run(run,'1'*40)
    run.update(changes)
    with pytest.raises(ValueError):validate_run(run,'1'*40)


def test_profile_selects_pinned_sources_without_replacing_run_or_byte_verification(tmp_path):
    from scripts.prepare_sdk_candidates import load_profile
    path=tmp_path/'profile.json'
    path.write_text(json.dumps({'version':1,'core':{'run_id':'101','source_commit':'1'*40},
        'runtime':{'run_id':'102','source_commit':'2'*40},
        'harness':{'run_id':'103','source_commit':'3'*40}}))
    assert load_profile(path)==[
        ('B3Cognition/prosaic','101','1'*40),
        ('B3Cognition/prosaic-runtime','102','2'*40),
        ('B3Cognition/prosaic-harness','103','3'*40)]


@pytest.mark.parametrize('change',['mutable_source','missing_sdk','external_repository','extra_binding'])
def test_invalid_profile_fails_before_any_github_access(tmp_path,monkeypatch,change,capsys):
    import scripts.prepare_sdk_candidates as cli
    value={'version':1,**{prefix:{'run_id':'101','source_commit':'1'*40}
                       for prefix in ('core','runtime','harness')}}
    if change=='mutable_source':value['core']['source_commit']='main'
    elif change=='missing_sdk':del value['runtime']
    elif change=='external_repository':value['core']['repository']='other/project'
    else:value['endpoint']='https://other.invalid'
    profile=tmp_path/'profile.json';profile.write_text(json.dumps(value))
    def forbidden(*args,**kwargs):raise AssertionError('network before input validation')
    monkeypatch.setattr(cli.subprocess,'run',forbidden)
    manifest=tmp_path/'candidate.json'
    assert cli.main(['--profile',str(profile),'--manifest',str(manifest)])==1
    assert json.loads(capsys.readouterr().out)['category']=='ValueError'
    assert not manifest.exists()


def test_profile_cannot_be_partially_overridden_with_manual_sources(tmp_path,monkeypatch):
    import scripts.prepare_sdk_candidates as cli
    def forbidden(*args,**kwargs):raise AssertionError('network before input validation')
    monkeypatch.setattr(cli.subprocess,'run',forbidden)
    with pytest.raises(SystemExit) as error:
        cli.main(['--profile',str(tmp_path/'profile.json'),'--core-run-id','999',
                  '--manifest',str(tmp_path/'manifest.json')])
    assert error.value.code==2
