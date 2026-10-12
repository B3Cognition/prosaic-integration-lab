import json
from types import SimpleNamespace
import sys


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
