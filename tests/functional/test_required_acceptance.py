import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from lab_runner.gates import COUNTS,required_modes


def test_native_persistence_candidate_requires_manifest_before_stack_allocation(monkeypatch):
    import pytest
    import lab_runner.__main__ as cli
    def forbidden(*args,**kwargs):raise AssertionError('unbound candidate reached stack allocation')
    monkeypatch.setattr(cli,'OwnedStack',forbidden)
    monkeypatch.setattr(sys,'argv',['lab_runner','test','--mode','native-persistence','--candidate'])
    with pytest.raises(SystemExit) as error:cli.main()
    assert error.value.code==2

def test_required_cli_runs_remaining_lanes_after_failure_and_exports_no_raw_output(monkeypatch,tmp_path):
    source = Path(__file__).resolve().parents[2]/'scripts/required_acceptance.py'
    spec = importlib.util.spec_from_file_location('required_acceptance',source)
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    monkeypatch.setattr(runner,'resolve_image',lambda candidate:'sha256:'+'1'*64)
    seen = []
    def fake(command,**kwargs):
        mode=command[command.index('--mode')+1]; seen.append(mode)
        if mode=='lago':
            assert kwargs['timeout']==900
        assert command[command.index('--consumer-image')+1] == 'sha256:'+'1'*64
        item={'mode':mode,'passed':mode != 'audit','cleanup':'verified','dependency_mode':'released',
            'test_returncode':1 if mode == 'audit' else 0,'test_count':COUNTS[mode],'skipped':0,
            'failed_tests':['PRIVATE'] if mode == 'audit' else [],'host_architecture':'arm64',
            'payload_audit':'verified','released_manifest_sha256':'f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472',
            'images':{'consumer':'sha256:'+'1'*64,'postgres':'postgres:16@sha256:'+'2'*64},'secret':'PRIVATE'}
        if mode=='lago':
            item['images']['lago']=json.loads((source.parents[1]/'dependencies/lago.json').read_text())['image']
        return SimpleNamespace(returncode=item['test_returncode'],stdout=json.dumps(item)+'\nEvidence: PRIVATE',stderr='PRIVATE')
    monkeypatch.setattr(runner.subprocess,'run',fake)
    target=tmp_path/'safe.json'
    monkeypatch.setattr(sys,'argv',['required_acceptance','--postgres-version','16','--export',str(target)])
    assert runner.main() == 1
    released=json.loads((source.parents[1]/'dependencies/releases.json').read_text())
    assert seen == list(required_modes(candidate=False,manifest=released))
    assert 'PRIVATE' not in target.read_text()
    assert json.loads(target.read_text())['passed'] is False

def test_ci_requires_native_matrix_and_exports_only_safe_summary():
    import yaml
    workflow=yaml.safe_load((Path(__file__).resolve().parents[2]/'.github/workflows/required-acceptance.yml').read_text())
    job=workflow['jobs']['acceptance']
    assert job['strategy']['matrix'] == {'runner':['ubuntu-24.04','ubuntu-24.04-arm'],'postgres':[16,18]}
    assert workflow['permissions'] == {'contents':'read'}
    steps=job['steps']
    uploads=[step for step in steps if 'upload-artifact@' in step.get('uses','')]
    assert len(uploads)==1 and uploads[0]['with']['path'].startswith('reports/required-')
    candidates=[step for step in steps if '--candidate' in step.get('run','')]
    assert candidates and all("github.event_name == 'workflow_dispatch' && inputs.candidate" in step.get('if','') for step in candidates)
    assert job['permissions']=={'contents':'read','actions':'read'}
    assert any('scripts/required_acceptance.py' in step.get('run','') for step in steps)


def test_ci_capability_selection_bootstraps_host_source_without_lab_install(tmp_path):
    import os,shlex,yaml
    root=Path(__file__).resolve().parents[2]
    workflow=yaml.safe_load((root/'.github/workflows/required-acceptance.yml').read_text())
    selected=next(step for step in workflow['jobs']['acceptance']['steps'] if step.get('id')=='conversation-sdk')
    environment={key:value for key,value in os.environ.items() if not key.startswith(('PYTHON','PIP_'))}
    output=tmp_path/'capability-output'
    environment.update(USE_CANDIDATE='false',SDK_MANIFEST='dependencies/releases.json',GITHUB_OUTPUT=str(output))
    subprocess.run([sys.executable,'-I','-c',
        "from importlib.util import find_spec; assert find_spec('prosaic_integration_lab') is None"],
        cwd=tmp_path,env=environment,check=True,capture_output=True,timeout=15)
    command=selected['run'].replace('.venv/bin/python',shlex.quote(sys.executable))
    result=subprocess.run(['/bin/bash','-e','-c',command],cwd=root,env=environment,capture_output=True,timeout=15)
    assert result.returncode==0,result.stderr.decode()
    from lab_runner.gates import supports_context_assembly
    import json
    manifest=json.loads((root/'dependencies/releases.json').read_text())
    assert output.read_text()=='enabled=true\ncontext='+str(supports_context_assembly(manifest)).lower()+'\n'


def test_ci_selects_installed_cli_for_trusted_workflow_preflight(tmp_path):
    import os
    import yaml
    from prosaic import __version__
    root=Path(__file__).resolve().parents[2]
    workflow=yaml.safe_load((root/'.github/workflows/required-acceptance.yml').read_text())
    steps=workflow['jobs']['acceptance']['steps']
    command=next((step.get('run','') for step in steps
        if step.get('name')=='Select installed CLI bindings'),'')
    bin_directory=tmp_path/'.venv/bin'
    bin_directory.mkdir(parents=True)
    installed_cli=Path(sys.executable).parent/'prosaic'
    assert installed_cli.is_file(),'the selected SDK wheel must install its public CLI'
    (bin_directory/'prosaic').symlink_to(installed_cli)
    path_file=tmp_path/'github-path'
    environment={'PATH':'/usr/bin:/bin','GITHUB_PATH':str(path_file)}
    subprocess.run(['/bin/bash','-e','-c',command],cwd=tmp_path,env=environment,
        check=True,capture_output=True,timeout=10)
    selected=path_file.read_text().splitlines() if path_file.exists() else []
    environment['PATH']=os.pathsep.join([*selected,environment['PATH']])
    result=subprocess.run(['prosaic','--version'],cwd=tmp_path,env=environment,
        check=True,capture_output=True,text=True,timeout=10)
    assert __version__ in result.stdout

def test_missing_image_fails_gate_with_safe_summary_before_owned_resources(monkeypatch,tmp_path,capsys):
    source=Path(__file__).resolve().parents[2]/'scripts/required_acceptance.py'
    spec=importlib.util.spec_from_file_location('required_missing_image',source)
    runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    def unavailable(candidate): raise runner.EngineError('PRIVATE')
    monkeypatch.setattr(runner,'resolve_image',unavailable)
    target=tmp_path/'safe.json'
    monkeypatch.setattr(sys,'argv',['required_acceptance','--postgres-version','16','--export',str(target)])
    assert runner.main() == 1
    assert json.loads(target.read_text()) == {'passed':False,'postgres_major':16,'lanes':[],
        'event':'required_image_unavailable'}
    assert 'PRIVATE' not in capsys.readouterr().out

def test_candidate_checkout_history_can_archive_exact_released_baseline(tmp_path):
    import hashlib
    import io
    import tarfile
    import yaml
    root=Path(__file__).resolve().parents[2]
    workflow=yaml.safe_load((root/'.github/workflows/required-acceptance.yml').read_text())
    checkout=next(step for step in workflow['jobs']['acceptance']['steps'] if 'checkout@' in step.get('uses',''))
    depth=checkout.get('with',{}).get('fetch-depth',1)
    source=tmp_path/'fresh-shallow'
    if not (root/'.git').exists():
        # Source/SDist archives do not carry historical Git objects. This test
        # requires the original repository, supplied explicitly by the caller.
        import os
        root=Path(os.environ['LAB_HISTORY_TEST_REPOSITORY'])
    # Actions checks out a detached exact commit. Exercise that state too,
    # without touching the caller's branch or assuming a named current branch.
    detached=tmp_path/'detached-origin'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    subprocess.run(['git','clone','--no-checkout',root.as_uri(),str(detached)],
        check=True,capture_output=True,timeout=30)
    subprocess.run(['git','checkout','--detach',commit],cwd=detached,
        check=True,capture_output=True,timeout=30)
    subprocess.run(['git','clone','--depth=1','--single-branch','--no-tags',
        detached.as_uri(),str(source)],check=True,capture_output=True,timeout=30)
    baseline='59752bef3e6b3ffde0ecbf38f34815d184043e20'
    missing=subprocess.run(['git','cat-file','-e',baseline+'^{commit}'],cwd=source,capture_output=True)
    assert missing.returncode!=0,'regression must start with the historical object absent'
    if depth==0:
        subprocess.run(['git','fetch','--unshallow','--no-tags','origin'],cwd=source,
            check=True,capture_output=True,timeout=30)
    elif depth!=1:
        subprocess.run(['git','fetch','--depth='+str(depth),'--no-tags','origin'],cwd=source,
            check=True,capture_output=True,timeout=30)
    result=subprocess.run(['git','archive',baseline],cwd=source,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr.decode()
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        manifest=archive.extractfile('dependencies/releases.json').read()
        assert hashlib.sha256(manifest).hexdigest()=='f972db9d828b6ab0ffcf6ca210082e5cbc3b7678f5a1b8f42bbc482b9aafb472'
        for filename in ('approval.yml','runtime.yml','schemas/result.json','subagents/author.md','synthetic.yml'):
            assert archive.extractfile('assets/'+filename).read()==(root/'assets/legacy-0.2.0'/filename).read_bytes()
