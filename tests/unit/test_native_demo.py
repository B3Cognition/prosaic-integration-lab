"""Adoption client protocol and safe receipt; real SQL is required acceptance."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import httpx
import pytest


DECISION = {'type':'object','properties':{'confirmed':{'type':'boolean'}},
            'required':['confirmed'],'additionalProperties':False}


class FixtureHTTP:
    """Only the external HTTP boundary is replaced in these client tests."""
    def __init__(self, *, invalid_response_status=422, usage_calls=2):
        self.model_calls = 11
        self.reset = False
        self.invalid_response_status = invalid_response_status
        self.usage_calls = usage_calls
        self.run = {'run_id':'1'*32,'status':'waiting','revision':'2'*64,'interaction':{
            'version':1,'runId':'1'*32,'revision':'2'*64,'stepId':'confirm',
            'question':'Accept the synthetic review?','choices':['accept','reject'],
            'responseSchemaDigest':'3'*64,'responseSchema':DECISION,
            'reviewOutputs':{'review':{'entity_id':'sample-1','approved':True}},
            'private':'PRIVATE_INTERACTION'}}
        self.proposal = {'proposal_id':'4'*32,'reference':{'private':'PRIVATE_BINDING'}}
        self.started = False

    def request(self, request):
        path = request.url.path
        body = json.loads(request.content) if request.content else None
        status = 200
        if request.url.host == 'model.invalid':
            if path == '/control':
                self.reset = body == {}
                result = {'status':'configured'}
            else:
                result = {'calls':self.model_calls,'private':'PRIVATE_PROVIDER'}
        elif request.headers['Authorization'] == 'Bearer PRIVATE_BOB_TOKEN':
            status, result = 404, {'detail':'not_found'}
        elif path == '/workflow-catalogue':
            result = {'manifest':{'agents':{'finder':{},'reviewer':{}},
                'schemas':{'found':{},'reviewed':{},'decision':{}},
                'validators':{'approved':{}},'allowAgentComposition':True,
                'private':'PRIVATE_CATALOGUE'},'proposal_schema':{'type':'object'}}
        elif path == '/workflow-proposals':
            result = self.proposal
        elif path == '/native-runs':
            if not self.started:
                self.model_calls += 2
                self.started = True
            result = self.run
        elif path.endswith('/usage'):
            result = {'total_calls':self.usage_calls,'complete_calls':self.usage_calls,
                'unresolved_calls':0,'billing_eligible':False,'private':'PRIVATE_USAGE'}
        elif path.endswith('/resume'):
            if body['expected_revision'] == 'stale':
                status, result = 409, {'detail':'revision_conflict'}
            elif body['response'] == {'confirmed':'invalid'}:
                status, result = self.invalid_response_status, {'detail':'response_schema_invalid'}
            else:
                self.run = {'run_id':'1'*32,'status':'completed','revision':'5'*64,'interaction':None,
                    'private':'PRIVATE_STATE'}
                result = self.run
        else:
            result = self.run
        return httpx.Response(status,json=copy.deepcopy(result))


def config():
    return {'a':'http://a.invalid','b':'http://b.invalid','model':'http://model.invalid',
        'app_dsn':'PRIVATE_DSN','assets':'/PRIVATE_ASSETS',
        'principals':{'PRIVATE_ALICE_TOKEN':{'actor_id':'alice'},
                      'PRIVATE_BOB_TOKEN':{'actor_id':'bob'}}}


def capture(monkeypatch, fixture):
    assert importlib.util.find_spec('lab_runner.native_demo') is not None, 'native adoption client is missing'
    from lab_runner import native_demo
    client_type = httpx.Client
    monkeypatch.setattr(native_demo.httpx,'Client',
        lambda **kwargs:client_type(transport=httpx.MockTransport(fixture.request),**kwargs))
    return native_demo.capture_native(config())


def test_native_demo_runs_cross_replica_protocol_and_exports_only_curated_fixture_fields(monkeypatch):
    fixture = FixtureHTTP()
    report = capture(monkeypatch,fixture)
    assert report['status'] == 'completed'
    assert report['independent_model_calls'] == 2
    assert report['usage'] == {'total_calls':2,'complete_calls':2,'unresolved_calls':0,'billing_eligible':False}
    assert report['checks'] == {'admission_without_model_calls':True,'proposal_replay':True,
        'start_replay':True,'invalid_response_unchanged':True,'stale_revision_unchanged':True,
        'owner_isolation':True,'resume_without_model_calls':True}
    assert report['interaction']['reviewOutputs'] == {'review':{'entity_id':'sample-1','approved':True}}
    assert report['interaction']['responseSchema'] == DECISION
    assert 'PRIVATE' not in json.dumps(report)
    assert fixture.reset


@pytest.mark.parametrize('settings',[{'invalid_response_status':200},{'usage_calls':1}])
def test_native_demo_rejects_unproved_protocol_or_accounting_and_resets_model(monkeypatch,settings):
    fixture = FixtureHTTP(**settings)
    with pytest.raises(ValueError):
        capture(monkeypatch,fixture)
    assert fixture.reset


def test_native_demo_open_report_rejected_before_allocating_owned_resources(monkeypatch,tmp_path):
    import lab_runner.__main__ as cli
    def forbidden(*args,**kwargs):
        pytest.fail('invalid native demo allocated an owned stack')
    monkeypatch.setattr(cli,'OwnedStack',forbidden)
    monkeypatch.setattr(sys,'argv',['lab_runner','demo','--mode','native','--candidate',
        '--candidate-manifest',str(tmp_path/'candidate.json'),'--open-report'])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


def test_native_demo_requires_explicit_complete_candidate_manifest_before_allocation(monkeypatch):
    import lab_runner.__main__ as cli
    def forbidden(*args,**kwargs):
        pytest.fail('unbound native candidate allocated an owned stack')
    monkeypatch.setattr(cli,'OwnedStack',forbidden)
    monkeypatch.setattr(sys,'argv',['lab_runner','demo','--mode','native','--candidate'])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


@pytest.mark.parametrize('content',['{','{"artifacts":[]}'])
def test_native_demo_rejects_incomplete_manifest_before_owned_resources(monkeypatch,tmp_path,content):
    import lab_runner.__main__ as cli
    manifest=tmp_path/'candidate.json'
    manifest.write_text(content)
    def forbidden(*args,**kwargs):
        pytest.fail('invalid SDK manifest allocated an owned stack')
    monkeypatch.setattr(cli,'OwnedStack',forbidden)
    monkeypatch.setattr(sys,'argv',['lab_runner','demo','--mode','native','--candidate',
        '--candidate-manifest',str(manifest)])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


@pytest.mark.parametrize('cleanup_fails',[False,True])
def test_native_demo_cli_writes_checked_receipt_and_returns_cleanup_result(monkeypatch,tmp_path,capsys,cleanup_fails):
    import lab_runner.__main__ as cli
    from lab_runner import native_demo
    fixture=FixtureHTTP()
    client_type=httpx.Client
    monkeypatch.setattr(native_demo.httpx,'Client',
        lambda **kwargs:client_type(transport=httpx.MockTransport(fixture.request),**kwargs))
    distributions={'b3-prosaic':'0.4.0','b3-prosaic-runtime':'0.8.0',
        'b3-prosaic-runtime-postgres':'0.2.0','b3-prosaic-harness':'0.7.0',
        'b3-prosaic-harness-postgres':'0.2.0'}
    manifest=tmp_path/'candidate.json'
    manifest.write_text(json.dumps({'artifacts':[
        {'distribution':name,'version':version,'filename':name.replace('-','_')+'-'+version+'-py3-none-any.whl',
         'sha256':'6'*64} for name,version in distributions.items()]}))

    class ExternalStack:
        def __init__(self,*args,**kwargs):
            self.directory=tmp_path/'evidence'
            self.secrets=self.directory/'secrets'
            self.secrets.mkdir(parents=True)
            self.owner='7'*32
            self.baseline_image=None
            self.manifest={'endpoints':{'a':'http://a.invalid','b':'http://b.invalid','model':'http://model.invalid'},
                'images':{},'payload_audit':'verified','candidate_manifest_sha256':'8'*64,
                'candidate_lineage_sha256':'9'*64}
            (self.secrets/'host.json').write_text(json.dumps(config()))
        def start(self): pass
        def start_model(self): pass
        def start_replica(self,*args,**kwargs): pass
        def stop(self):
            if cleanup_fails:
                raise RuntimeError('PRIVATE_CLEANUP_FAILURE')

    def wrong_demo(*args,**kwargs):
        pytest.fail('native CLI selected the accounting walkthrough')
    monkeypatch.setattr(cli,'OwnedStack',ExternalStack)
    monkeypatch.setattr(cli,'capture_accounting',wrong_demo)
    monkeypatch.setattr(sys,'argv',['lab_runner','demo','--mode','native','--candidate',
        '--candidate-manifest',str(manifest)])
    assert cli.main() == (1 if cleanup_fails else 0)
    result=json.loads((tmp_path/'evidence/result.json').read_text())
    assert result['passed'] is (not cleanup_fails)
    assert result['cleanup'] == ('failed' if cleanup_fails else 'verified')
    assert result['fixture'] == 'native-workflow-demonstration'
    assert 'qualification' not in result and 'test_count' not in result
    report=json.loads(Path(result['report_json']).read_text())
    assert report['status']=='completed' and report['independent_model_calls']==2
    assert 'PRIVATE' not in capsys.readouterr().out and fixture.reset
