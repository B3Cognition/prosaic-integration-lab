"""Smoke contracts use host process doubles; genuine installs are separate gates."""
import importlib.util
import io
from pathlib import Path
import tarfile

import pytest


def implementation():
    path=Path(__file__).resolve().parents[2]/'scripts/conversation_distribution_smoke.py'
    assert path.is_file(),'conversation distribution smoke is missing'
    spec=importlib.util.spec_from_file_location('conversation_distribution_smoke',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


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
