import json
from types import SimpleNamespace
import sys
import subprocess
import pytest


def test_conversation_demo_selects_owned_chat_stack_and_its_own_capture(tmp_path,monkeypatch):
    from lab_runner import __main__ as cli
    import prosaic_integration_lab.conversation_execution as api
    import lab_runner.conversation_demo as demo
    selected=[]
    class Stack:
        def __init__(self,*args,**kwargs):
            selected.append(kwargs)
            self.owner='a'*32;self.directory=tmp_path;self.secrets=tmp_path/'secrets';self.secrets.mkdir()
            (self.secrets/'host.json').write_text('{}')
            self.baseline_image=None
            self.manifest={'endpoints':{'a':'owned-a','b':'owned-b'},'images':{},'payload_audit':'verified'}
        def start(self):pass
        def start_model(self):pass
        def start_replica(self,*args,**kwargs):pass
        def stop(self):selected.append('cleanup')
    monkeypatch.setattr(cli,'OwnedStack',Stack)
    monkeypatch.setattr(api,'require_conversation_sdk',lambda:None)
    report={'version':1,'status':'completed','independent_model_calls':9,'fixture':'conversation'}
    monkeypatch.setattr(demo,'capture_conversation',lambda config:report)
    monkeypatch.setattr(cli,'capture_accounting',lambda *args:(_ for _ in ()).throw(AssertionError('legacy demo selected')))
    monkeypatch.setattr(sys,'argv',['lab_runner','demo','--mode','conversation'])
    assert cli.main()==0
    assert selected[0]['conversation'] is True and selected[0]['users']==16
    assert selected[-1]=='cleanup'
    result=json.loads((tmp_path/'result.json').read_text())
    assert result['passed'] is True and result['fixture']=='conversation-demonstration'
    assert json.loads((tmp_path/'report/conversation.json').read_text())==report


@pytest.mark.parametrize('elapsed,passed', [(650, True), (1000, False)])
def test_conversation_suite_has_bounded_headroom_and_still_cleans_up_on_timeout(tmp_path,monkeypatch,elapsed,passed):
    from lab_runner import __main__ as cli
    from lab_runner.gates import export
    stopped=[]
    class Stack:
        def __init__(self,*args,**kwargs):
            self.owner='b'*32;self.directory=tmp_path;self.secrets=tmp_path/'secrets';self.secrets.mkdir()
            (self.secrets/'host.json').write_text('{}')
            self.baseline_image=None
            self.manifest={'endpoints':{},'images':{},'payload_audit':'verified'}
        def start(self):pass
        def start_model(self):pass
        def start_replica(self,*args,**kwargs):pass
        def stop(self):stopped.append(True)
    def suite(command,**kwargs):
        # The process boundary is slow/external; keep the real runner, JUnit
        # validation, receipt sanitization and cleanup paths under test.
        assert command[1:3]==['-m','pytest']
        if kwargs['timeout']<elapsed:
            raise subprocess.TimeoutExpired(command,kwargs['timeout'],output='PRIVATE_TOKEN')
        (tmp_path/'junit.xml').write_text('<testsuites><testsuite>'+''.join(
            '<testcase name="case-'+str(i)+'"/>' for i in range(103))+'</testsuite></testsuites>')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(cli,'OwnedStack',Stack)
    monkeypatch.setattr(cli.subprocess,'run',suite)
    monkeypatch.setattr(sys,'argv',['lab_runner','test','--mode','conversation','--context-assembly'])
    assert cli.main()==(0 if passed else 1)
    result=json.loads((tmp_path/'result.json').read_text())
    assert result['passed'] is passed and stopped==[True] and result['cleanup']=='verified'
    if passed:assert result['test_count']==103
    else:
        safe=export(result)
        assert safe['failure_code']=='execution_timeout' and safe['passed'] is False
        assert 'PRIVATE' not in json.dumps(safe)
