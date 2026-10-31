"""Smoke contracts use host process doubles; genuine installs are separate gates."""
import importlib.util
import io
from pathlib import Path
import tarfile
import json
import hashlib
import tomllib
from types import SimpleNamespace

import pytest


def implementation():
    path=Path(__file__).resolve().parents[2]/'scripts/conversation_distribution_smoke.py'
    assert path.is_file(),'conversation distribution smoke is missing'
    spec=importlib.util.spec_from_file_location('conversation_distribution_smoke',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_wheel_identity_requires_current_source_version_instead_of_historical_release(tmp_path):
    import zipfile
    module=implementation();current=tomllib.loads((module.ROOT/'pyproject.toml').read_text())['project']['version']
    def wheel(version):
        path=tmp_path/(version+'.whl')
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('prosaic_integration_lab.dist-info/METADATA',
                'Name: prosaic-integration-lab\nVersion: '+version+'\n')
        return path
    assert module.wheel_identity(wheel(current))['version']==current
    with pytest.raises(ValueError):module.wheel_identity(wheel('0.0.0'))


@pytest.mark.parametrize('train', ['context', 'blueprints', 'unified'])
def test_consumer_runs_experimental_smokes_only_for_qualified_train(tmp_path, monkeypatch, train):
    from lab_runner.gates import CONTEXT_TRAIN, CONSUMER_BLUEPRINT_TRAIN, UNIFIED_POOL_TRAIN
    module = implementation()
    calls = []
    monkeypatch.setattr(module, 'verified_wheel_paths', lambda *args: [])
    monkeypatch.setattr(module, 'wheel_identity', lambda path: {'name': 'lab', 'version': '0.5.0', 'files': {}})
    monkeypatch.setattr(module, 'verify_cli_versions', lambda *args: None)
    monkeypatch.setattr(module, '_helper', lambda name: SimpleNamespace(
        INDEX='https://pypi.org/simple', AUDIT_LAUNCH='', PUBLIC_EXAMPLE=''))
    def run(argv, **kwargs):
        calls.append(argv)
        if 'lab_runner.native_eval' in argv:
            command = argv[argv.index('lab_runner.native_eval') + 1]
            counts = {'test': 9, 'unified-test': 11, 'unified-cli-test': 13, 'unified-fallback-test': 18}
            return json.dumps({'passed': True, 'caseCount': counts[command],
                'cleanup': 'verified', 'liveInvocations': 0}).encode()
        return b'{}'
    monkeypatch.setattr(module, 'run', run)
    manifest = tmp_path / 'manifest.json'
    versions = {'context': CONTEXT_TRAIN, 'blueprints': CONSUMER_BLUEPRINT_TRAIN,
                'unified': UNIFIED_POOL_TRAIN}[train]
    manifest.write_text(json.dumps({'artifacts': [{'distribution': key, 'version': value}
                                                for key, value in versions.items()]}))
    module.consume(tmp_path / 'lab.whl', directory=tmp_path, manifest=manifest,
                   wheels=tmp_path, lock=tmp_path / 'lock', environment={})
    explorer = [call for call in calls if any(str(arg).endswith('explorer_smoke.py') for arg in call)]
    assert len(explorer) == 1
    assert '-I' in explorer[0] and '-B' in explorer[0]
    for script in ('agent_quality_smoke.py', 'retrieval_memory_smoke.py'):
        selected = [call for call in calls if any(str(arg).endswith(script) for arg in call)]
        assert len(selected) == int(train != 'context')
        if train != 'context':
            assert '-I' in selected[0] and '--source-root' in selected[0]
    installed = [call for call in calls if 'lab_runner.native_eval' in call]
    assert len(installed) == (4 if train == 'unified' else 0)
    if installed:
        assert [call[call.index('lab_runner.native_eval') + 1] for call in installed] == [
            'test', 'unified-test', 'unified-cli-test', 'unified-fallback-test']
        assert all('-I' in call and '--manifest' in call and '--wheel-dir' in call for call in installed)


@pytest.mark.parametrize('defect', ['failed', 'wrong-count', 'live-call', 'unclean'])
def test_installed_evaluation_receipt_cannot_silently_weaken_distribution_gate(tmp_path, monkeypatch, defect):
    from lab_runner.gates import UNIFIED_POOL_TRAIN
    module = implementation()
    monkeypatch.setattr(module, 'verified_wheel_paths', lambda *args: [])
    monkeypatch.setattr(module, 'wheel_identity', lambda path: {'name': 'lab', 'version': '0.6.0', 'files': {}})
    monkeypatch.setattr(module, 'verify_cli_versions', lambda *args: None)
    monkeypatch.setattr(module, '_helper', lambda name: SimpleNamespace(
        INDEX='https://pypi.org/simple', AUDIT_LAUNCH='', PUBLIC_EXAMPLE=''))
    def run(argv, **kwargs):
        if 'lab_runner.native_eval' not in argv:
            return b'{}'
        row = {'passed': True, 'caseCount': 9, 'liveInvocations': 0, 'cleanup': 'verified'}
        row.update({'failed': {'passed': False}, 'wrong-count': {'caseCount': 0},
                    'live-call': {'liveInvocations': 1}, 'unclean': {'cleanup': 'pending'}}[defect])
        return json.dumps(row).encode()
    monkeypatch.setattr(module, 'run', run)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'artifacts': [{'distribution': k, 'version': v}
        for k, v in UNIFIED_POOL_TRAIN.items()]}))
    with pytest.raises(ValueError, match='installed evaluation qualification incomplete'):
        module.consume(tmp_path / 'lab.whl', directory=tmp_path, manifest=manifest,
            wheels=tmp_path, lock=tmp_path / 'lock', environment={})


@pytest.mark.parametrize('complete_context_evidence',[False,True])
def test_extracted_context_train_requires_demo_flag_and_103_cases(tmp_path,monkeypatch,complete_context_evidence):
    from lab_runner.gates import CONTEXT_TRAIN
    module=implementation()
    lineage={'version':1,'candidates':[]}  # structural process-double evidence only
    data={'artifacts':[{'distribution':name,'version':version} for name,version in CONTEXT_TRAIN.items()],
        'candidate_lineage':lineage}
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(data))
    wheel=tmp_path/'lab.whl';wheel.write_bytes(b'wheel')
    sdist=tmp_path/'lab.tar.gz';sdist.write_bytes(b'sdist')
    monkeypatch.setattr(module,'sdk_manifest',lambda path:data)
    monkeypatch.setattr(module,'verified_wheel_paths',lambda *args:[])
    monkeypatch.setattr(module,'wheel_identity',lambda path:{'version':'0.5.0'})
    monkeypatch.setattr(module,'_helper',lambda name:SimpleNamespace(isolated_environment=lambda:{}))
    monkeypatch.setattr(module,'consume',lambda *args,**kwargs:Path('/fixture/python'))
    monkeypatch.setattr(module,'verify_observatory_source',lambda source:None)
    def extract(archive,destination):
        destination.mkdir()
        for name in ('configs/conversation-conformance.example.json','docs/conversations.md',
                     'assets/conversation/agents/assistant.md','scripts/conversation_conformance.py',
                     'tests/acceptance/test_conversation_journey.py','dependencies/public-build-inputs.json'):
            path=destination/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture')
        return destination
    monkeypatch.setattr(module,'extract_sdist',extract)
    identifier='sha256:'+'a'*64
    def process(argv,**kwargs):
        if 'pytest' in argv:
            assert 'tests/unit/test_observatory_launcher.py' in argv
            return b''
        if 'build' in argv:
            out=Path(argv[argv.index('--outdir')+1]);(out/'rebuilt.whl').write_bytes(b'rebuilt');return b''
        if any(str(arg).endswith('build_consumer.py') for arg in argv):return (identifier+'\n').encode()
        assert '--context-assembly' in argv
        kind='demo' if 'demo' in argv else 'conversation'
        receipt={'owner':'a'*32,'mode':kind,'passed':True,'cleanup':'verified','test_returncode':0,
            'test_count':103 if complete_context_evidence else 97,'skipped':0,'failed_tests':[],
            'context_assembly':complete_context_evidence,'host_architecture':'arm64','dependency_mode':'candidate',
            'payload_audit':'verified','candidate_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
            'released_manifest_sha256':hashlib.sha256((module.ROOT/'dependencies/releases.json').read_bytes()).hexdigest(),
            'candidate_lineage_sha256':hashlib.sha256((json.dumps(lineage,sort_keys=True,indent=2)+'\n').encode()).hexdigest(),
            'images':{'consumer':identifier,'postgres':'postgres:16@sha256:'+'b'*64}}
        if kind=='demo':receipt['fixture']='conversation-demonstration'
        return json.dumps(receipt).encode()
    monkeypatch.setattr(module,'run',process)
    result=module.verify(wheel,sdist,manifest,candidate=True,run_stack=True)
    assert result['passed'] is complete_context_evidence, json.dumps(result)
    if not complete_context_evidence:assert result['failure_stage']=='sdist_acceptance', result


@pytest.mark.parametrize('name,kind',[('../outside','file'),('project/../outside','file'),
    ('/outside','file'),('project/link','symlink'),('project/hard','hardlink')])
def test_sdist_rejects_traversal_and_links_before_extraction(tmp_path,name,kind):
    archive=tmp_path/'source.tar.gz'
    with tarfile.open(archive,'w:gz') as output:
        member=tarfile.TarInfo(name);member.size=1
        if kind=='symlink':member.type=tarfile.SYMTYPE;member.linkname='../outside';member.size=0
        if kind=='hardlink':member.type=tarfile.LNKTYPE;member.linkname='../outside';member.size=0
        output.addfile(member,io.BytesIO(b'x') if member.size else None)
    with pytest.raises(ValueError):implementation().extract_sdist(archive,tmp_path/'owned')
    assert not (tmp_path/'outside').exists()


def test_sdist_has_one_owned_root_and_bounded_files(tmp_path):
    archive=tmp_path/'source.tar.gz'
    with tarfile.open(archive,'w:gz') as output:
        for name in ('project/a','other/b'):
            member=tarfile.TarInfo(name);member.size=1;output.addfile(member,io.BytesIO(b'x'))
    with pytest.raises(ValueError):implementation().extract_sdist(archive,tmp_path/'owned')


def test_candidate_mode_must_match_original_manifest_lineage():
    module=implementation()
    module.validate_mode({'candidate_lineage':{'version':1}},candidate=True)
    with pytest.raises(ValueError):module.validate_mode({'candidate_lineage':{'version':1}},candidate=False)
    with pytest.raises(ValueError):module.validate_mode({'artifacts':[]},candidate=True)


def test_process_failure_exports_no_private_logs(tmp_path,monkeypatch):
    import subprocess
    module=implementation()
    def failing(*args,**kwargs):
        kwargs['stdout'].write(b'private-secret');kwargs['stderr'].write(b'private-endpoint')
        return subprocess.CompletedProcess(args,1)
    monkeypatch.setattr(module.subprocess,'run',failing)
    with pytest.raises(ValueError,match='isolated distribution command failed'):
        module.run(['python','-I','private-path'],directory=tmp_path,environment={})


def test_failed_stack_diagnostic_exports_only_owned_whitelisted_fields():
    import json
    raw=json.dumps({'owner':'a'*32,'mode':'demo','passed':False,'cleanup':'verified',
        'error':'EngineError','dsn':'private-secret','report_json':'private-path',
        'engine_diagnostic':{'operation':'start','return_code':1,
            'category':'engine_failed','outcome':'unknown'}}).encode()
    result=implementation().safe_stack_failure(raw)
    assert result['stack_error']=='EngineError'
    assert result['stack_receipt']['cleanup']=='verified'
    assert result['stack_receipt']['engine_diagnostic']['operation']=='start'
    encoded=json.dumps(result)
    assert 'private-secret' not in encoded and 'private-path' not in encoded


def test_unowned_or_malformed_command_output_supplies_no_stack_diagnostic():
    module=implementation()
    for raw in (b'private-secret',b'{broken',b'{"mode":"demo","error":"private-secret"}'):
        assert module.safe_stack_failure(raw)=={}


def test_stack_diagnostic_bootstraps_lab_runner_outside_pytest(tmp_path):
    import subprocess
    import sys
    script=Path(__file__).resolve().parents[2]/'scripts/conversation_distribution_smoke.py'
    source="""
import importlib.util,json,sys
spec=importlib.util.spec_from_file_location('distribution_probe',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
row={'owner':'a'*32,'mode':'demo','passed':False,'cleanup':'verified','error':'EngineError'}
result=module.safe_stack_failure(json.dumps(row).encode())
assert result['stack_error']=='EngineError'
from lab_runner.gates import validate
"""
    result=subprocess.run([sys.executable,'-I','-B','-c',source,str(script)],
        cwd=tmp_path,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr


def test_lab_version_command_preserves_existing_five_sdk_json_contract():
    module=implementation()
    data={'artifacts':[{'distribution':'b3-prosaic','version':'0.4.1'}]}
    module.verify_cli_versions(b'{"b3-prosaic":"0.4.1"}\n',data)
    with pytest.raises(ValueError):module.verify_cli_versions(b'0.5.0\n',data)
    with pytest.raises(ValueError):module.verify_cli_versions(b'{"b3-prosaic":"9.0"}',data)


def test_cli_creates_missing_report_parent_after_success(tmp_path,monkeypatch,capsys):
    import json
    module=implementation()
    receipt={'event':'conversation_distribution','passed':True,'candidate':True}
    monkeypatch.setattr(module,'verify',lambda *args,**kwargs:receipt.copy())
    destination=tmp_path/'reports'/'conversation-distribution-pg16.json'
    code=module.main(['--wheel','wheel.whl','--sdist','source.tar.gz',
        '--manifest','manifest.json','--candidate','--export',str(destination)])
    assert code==0
    assert json.loads(destination.read_text())==receipt
    assert json.loads(capsys.readouterr().out)==receipt


def test_bounded_process_output_keeps_final_immutable_image_id(tmp_path,monkeypatch):
    import subprocess
    module=implementation();identifier=b'sha256:'+b'a'*64+b'\n'
    def successful(*args,**kwargs):
        kwargs['stdout'].write(b'x'*70000+b'\n'+identifier)
        return subprocess.CompletedProcess(args,0)
    monkeypatch.setattr(module.subprocess,'run',successful)
    output=module.run(['python','-I','build-consumer'],directory=tmp_path,environment={})
    assert len(output)<=65536 and output.endswith(identifier)


def test_actual_demo_stdout_selects_execution_receipt_before_separate_report(tmp_path,monkeypatch,capsys):
    import json
    from tests.unit.test_conversation_runner import test_conversation_demo_selects_owned_chat_stack_and_its_own_capture
    test_conversation_demo_selects_owned_chat_stack_and_its_own_capture(tmp_path,monkeypatch)
    output=capsys.readouterr().out.encode()
    records=[json.loads(line) for line in output.decode().splitlines() if line.startswith('{')]
    assert len(records)==2 and records[-1]['fixture']=='conversation' and 'passed' not in records[-1]
    result=implementation().execution_receipt(output,command='demo')
    assert result['passed'] is True and result['cleanup']=='verified'


@pytest.mark.parametrize('rows',[[],[{'mode':'conversation','passed':True,'cleanup':'pending'}],
    [{'mode':'conversation','passed':False,'cleanup':'verified'}],
    [{'mode':'conversation','passed':True,'cleanup':'verified'}]*2,
    [{'fixture':'conversation','status':'completed'}]])
def test_diagnostic_or_ambiguous_stack_output_cannot_qualify(rows):
    import json
    with pytest.raises(ValueError):
        implementation().execution_receipt(('\n'.join(json.dumps({'owner':'a'*32,**row}) for row in rows)).encode(),command='test')
