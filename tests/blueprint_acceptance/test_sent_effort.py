"""Installed public sent-effort blueprint: real synthetic wires and fake CLIs."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from uuid import uuid4
import json,os,runpy,subprocess,sys
import pytest
from lab_runner.blueprints import copy_blueprint
from lab_runner.rule_admission.fixtures import ScriptedProvider,scripted_provider

KEY='reasoning_effort_v1'

@pytest.fixture(autouse=True)
def loopback(monkeypatch):monkeypatch.setenv('no_proxy','*');monkeypatch.setenv('NO_PROXY','*')
@pytest.fixture(params=['openai-compatible','anthropic'])
def wire(request):return request.param

def copied(tmp_path):
    project=copy_blueprint('sent-effort',tmp_path/'effort')
    return project,runpy.run_path(str(project/'host.py'))

def rows(result,count):
    trace=result.metadata[KEY]
    assert trace['version']==1 and trace['attempt_count']==count and trace['complete'] is True and trace['omitted_attempts']==0
    assert [r['index'] for r in trace['attempts']]==list(range(1,count+1))
    assert all(r['provider_confirmation']=='not_observed' for r in trace['attempts'])
    return trace['attempts']

def test_installed_ownership_and_capabilities():
    import prosaic_runtime,prosaic_harness
    from importlib.metadata import version
    assert (version('b3-prosaic-runtime'),version('b3-prosaic-harness')) in {('0.9.18','0.9.12'),('0.9.19','0.9.13'),('0.9.20','0.9.14'),('0.9.21.dev1','0.9.15.dev1'),('0.9.21','0.9.15')}
    assert KEY in prosaic_runtime.ProsaicRuntime.capabilities
    for module in (prosaic_runtime,prosaic_harness):assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix))

@pytest.mark.parametrize('entry',['run','turn','prepared'])
@pytest.mark.parametrize('requested',[None,'high','none'])
def test_both_wires_compare_actual_controls_defaults_omission_and_call_ids(tmp_path,wire,entry,requested):
    from prosaic_runtime.accounting import MemoryRecorder
    project,host=copied(tmp_path)
    with scripted_provider(wire) as provider:
        recorder=MemoryRecorder(provider_id=wire)
        rt=host['build_runtime'](project=project,base_url=provider.url,provider=wire,accounting=recorder)
        a=host['load_agent'](project)
        if requested is not None and wire=='openai-compatible':a=replace(a,frontmatter={**a.frontmatter,'effort':requested})
        prepared=rt.prepare_turn(a,message='Review');digest=a.digest;identity=prepared.context_identity
        provider.queue_text('done')
        if entry=='run':result=host['run_review'](rt,a)
        elif entry=='prepared':result=rt.turn(prepared).result
        else:result=rt.turn(a,message='Review').result
        assert result.exit_code==0
        row=rows(result,1)[0];sent={k:v for k,v in provider.requests[0].items() if k in ('reasoning_effort','chat_template_kwargs')}
        assert row['sent']==sent==({'reasoning_effort':requested or 'low'} if wire=='openai-compatible' else {})
        assert row['requested_effort']==(requested if wire=='openai-compatible' else None)
        assert row['configured_effort']==('low' if wire=='openai-compatible' else None)
        assert row['provider_call_id']==provider.captured_headers[0]['x-client-request-id']==next(iter(recorder.intents))
        assert a.digest==digest and rt.prepare_turn(a,message='Review').context_identity==identity
        report=host['effort_report'](result);report['trace']['attempts'].clear();assert rows(result,1)

@pytest.mark.parametrize('model,effort,fmt,sent',[
 ('gemma-4-31B-it-oQ4e-mtp','high','thinking_toggle',{'chat_template_kwargs':{'enable_thinking':True}}),
 ('gemma-4-31B-it-oQ4e-mtp','none','thinking_toggle',{'chat_template_kwargs':{'enable_thinking':False}}),
 ('ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ','xhigh','chat_template_effort',{'chat_template_kwargs':{'enable_thinking':True},'reasoning_effort':'xhigh'}),
 ('ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ','none','thinking_toggle',{'chat_template_kwargs':{'enable_thinking':False}})])
def test_binary_and_chat_template_controls_never_invent_neutral_tiers(tmp_path,model,effort,fmt,sent):
    project,host=copied(tmp_path)
    with scripted_provider() as provider:
        rt=host['build_runtime'](project=project,base_url=provider.url,model=model)
        a=host['load_agent'](project);a=replace(a,frontmatter={**a.frontmatter,'effort':effort})
        provider.queue_text('done');out=host['run_review'](rt,a);assert out.exit_code==0
        row=rows(out,1)[0];assert row['format']==fmt and row['sent']==sent
        assert sent=={k:v for k,v in provider.requests[0].items() if k in ('reasoning_effort','chat_template_kwargs')}

@pytest.mark.parametrize('kind',['tool','repair','adapter'])
def test_all_attempts_are_retained_and_join_existing_accounting(tmp_path,wire,kind):
    from prosaic_runtime import CustomTool,ProsaicArtifact,RunPolicy,RuntimeAdapter,generic_guards
    from prosaic_runtime.accounting import MemoryRecorder
    project,host=copied(tmp_path);rec=MemoryRecorder(provider_id=wire)
    tools={'lookup':CustomTool('lookup','Synthetic lookup',{'type':'object','additionalProperties':False},lambda a:{'ok':True},'v1')} if kind=='tool' else {}
    with scripted_provider(wire) as provider:
        rt=host['build_runtime'](project=project,base_url=provider.url,provider=wire,accounting=rec,custom_tools=tools,guards=generic_guards())
        a=host['load_agent'](project)
        if kind=='tool':
            a=replace(a,frontmatter={**a.frontmatter,'tools':['lookup']});provider.queue_calls(('one','lookup',{}));provider.queue_text('done')
        elif kind=='repair':
            a=replace(a,body='- ALWAYS answer JSON. <!-- enforce: strict_json(stage=final, on_violation=retry) -->\n');provider.queue_text('bad');provider.queue_text('{}')
        else:provider.queue_text('one');provider.queue_text('two')
        policy=RunPolicy(allowed_tools=frozenset(tools),max_provider_requests=2,max_tool_calls=1)
        if kind=='adapter':
            def invoke(a,args,*,execute,**kwargs):
                first=execute('one');first.metadata[KEY]['attempts'].clear()
                second=execute('two');second.metadata[KEY]={'fake':'private'};return second
            result=RuntimeAdapter(rt,version='synthetic-v1',invoke=invoke).run(a,policy=policy)
        else:result=rt.turn(a,message='Review',policy=policy).result
        assert result.exit_code==0 and len(provider.requests)==2
        trace=rows(result,2)
        assert [r['provider_call_id'] for r in trace]==[h['x-client-request-id'] for h in provider.captured_headers]
        assert set(rec.intents)=={r['provider_call_id'] for r in trace}

@pytest.mark.parametrize('when',['prepare','observe','cancel'])
def test_failure_boundaries_are_not_claimed_as_delivered_or_retried(tmp_path,wire,when):
    from prosaic_runtime.accounting import MemoryRecorder,AccountingError
    project,host=copied(tmp_path)
    class Recorder(MemoryRecorder):
        def prepare(self,intent):
            if when=='prepare':raise AccountingError('PRIVATE_PREPARE')
            return super().prepare(intent)
        def observe(self,*args):raise AccountingError('PRIVATE_OBSERVE')
    with scripted_provider(wire) as provider:
        rt=host['build_runtime'](project=project,base_url=provider.url,provider=wire,accounting=Recorder(provider_id=wire))
        provider.queue_text('done');out=rt.turn(host['load_agent'](project),message='Review',cancelled=(lambda:True) if when=='cancel' else None).result
        assert out.exit_code!=0 and len(provider.requests)==(1 if when=='observe' else 0)
        rows(out,len(provider.requests));assert 'PRIVATE_' not in json.dumps(out.metadata[KEY])

@pytest.mark.parametrize('backend',['claude-code','codex-cli'])
@pytest.mark.parametrize('requested,default',[(None,None),(None,'medium'),('high','low')])
def test_native_actual_child_argv_and_original_profile_annotations(tmp_path,backend,requested,default):
    from prosaic_runtime import NativeRuntime,NativeRuntimeConfig,NativeProfile,NativePolicy
    project,host=copied(tmp_path);a=host['load_agent'](project)
    if requested:a=replace(a,frontmatter={**a.frontmatter,'effort':requested})
    executable=tmp_path/'fake-agent'
    executable.write_text(f'#!{sys.executable}\nimport sys,json\nsys.stdin.read()\ntext=json.dumps(sys.argv[1:])\n'+
        ("print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':text}))\n" if backend=='claude-code' else
         "print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':text}}))\nprint(json.dumps({'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}}))\n"))
    executable.chmod(0o755)
    rt=NativeRuntime(NativeRuntimeConfig({'local':NativeProfile(backend,'synthetic','fixture',str(executable),effort=default)},routes={'fast':'local'},default_profile='local'))
    out=rt.run(a,cwd=tmp_path,policy=NativePolicy());assert out.exit_code==0
    row=rows(out,1)[0];argv=json.loads(out.stdout);actual=requested or default
    sent=['--effort',actual] if actual and backend=='claude-code' else ['-c','model_reasoning_effort='+json.dumps(actual)] if actual else []
    actual_pairs=[argv[i:i+2] for i,value in enumerate(argv[:-1])
                  if value=='--effort' or (value=='-c' and argv[i+1].startswith('model_reasoning_effort='))]
    assert actual_pairs==([sent] if sent else []) and row['sent']=={'argv':sent}
    assert row['provider_call_id'] is None and row['requested_effort']==requested and row['configured_effort']==default
    assert str(tmp_path) not in json.dumps(out.metadata[KEY])


def test_old_result_absence_and_public_view_are_not_fabricated(tmp_path):
    from prosaic_runtime import Result
    _,host=copied(tmp_path)
    assert host['effort_report'](Result(0,'',''))=={'available':False,'trace':None}
    assert host['public_view']({'status':'completed','calls':1,'result':'private','outputs':'private'})=={'status':'completed','calls':1}


def test_copyable_cli_requires_live_opt_in(tmp_path):
    project,_=copied(tmp_path)
    out=subprocess.run([sys.executable,str(project/'host.py')],cwd=project,capture_output=True,text=True,timeout=15)
    assert out.returncode!=0 and '--live is required' in out.stderr


@contextmanager
def effort_provider(wire,*,stream=False,status=200):
    """Owned synthetic HTTP server; captures only test inputs, never a live endpoint."""
    fixture=ScriptedProvider(wire)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            fixture.captured_headers.append({k.lower():v for k,v in self.headers.items()})
            code,document=fixture._reply(self.rfile.read(int(self.headers['Content-Length'])))
            code=status if code==200 else code
            content_type='application/json';body=json.dumps(document).encode()
            if code==200 and stream:
                content_type='text/event-stream'
                if wire=='openai-compatible':
                    text=document['choices'][0]['message']['content']
                    events=[{'choices':[{'index':0,'delta':{'content':text},'finish_reason':None}]},
                            {'choices':[{'index':0,'delta':{},'finish_reason':'stop'}],'usage':{'prompt_tokens':2,'completion_tokens':3,'total_tokens':5}}]
                    body=(''.join('data: '+json.dumps(e)+'\n\n' for e in events)+'data: [DONE]\n\n').encode()
                else:
                    text=document['content'][0]['text']
                    events=[('message_start',{'type':'message_start','message':{'type':'message','id':'synthetic','model':'synthetic-model','role':'assistant','content':[],'usage':{'input_tokens':2,'output_tokens':0}}}),
                            ('content_block_start',{'type':'content_block_start','index':0,'content_block':{'type':'text','text':''}}),
                            ('content_block_delta',{'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':text}}),
                            ('content_block_stop',{'type':'content_block_stop','index':0}),
                            ('message_delta',{'type':'message_delta','delta':{'stop_reason':'end_turn'},'usage':{'output_tokens':3}}),('message_stop',{'type':'message_stop'})]
                    body=''.join('event: '+name+'\ndata: '+json.dumps(e)+'\n\n' for name,e in events).encode()
            self.send_response(code);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    worker=Thread(target=server.serve_forever,daemon=True);worker.start();fixture.url=f'http://127.0.0.1:{server.server_port}/v1'
    try:yield fixture
    finally:server.shutdown();server.server_close();worker.join(timeout=5);assert not worker.is_alive()


@pytest.mark.parametrize('entry',['run','turn','prepared'])
def test_streamed_actual_controls_are_retained(tmp_path,wire,entry):
    project,host=copied(tmp_path)
    with effort_provider(wire,stream=True) as provider:
        rt=host['build_runtime'](project=project,base_url=provider.url,provider=wire,streaming=True)
        a=host['load_agent'](project);provider.queue_text('done')
        if entry=='run':result=host['run_review'](rt,a)
        elif entry=='prepared':result=rt.turn(rt.prepare_turn(a,message='Review')).result
        else:result=rt.turn(a,message='Review').result
        assert result.exit_code==0 and provider.requests[0]['stream'] is True
        row=rows(result,1)[0];assert row['sent']==({'reasoning_effort':'low'} if wire=='openai-compatible' else {})


@pytest.mark.parametrize('status',[401,429,503])
def test_http_error_keeps_an_attempt_without_delivery_claim(tmp_path,wire,status):
    project,host=copied(tmp_path)
    with effort_provider(wire,status=status) as provider:
        rt=host['build_runtime'](project=project,base_url=provider.url,provider=wire);provider.queue_text('unused')
        result=host['run_review'](rt,host['load_agent'](project))
        assert result.exit_code!=0 and len(provider.requests)==1;rows(result,1)


def test_file_reopen_and_saved_receipt_recovery_preserves_trace_without_call(tmp_path,wire):
    from prosaic_harness import Harness,FileRunStore
    from prosaic_runtime import ExecutionContext
    from prosaic_runtime.accounting import MemoryRecorder
    project,host=copied(tmp_path);saved=[]
    class LostAck(BaseException):pass
    class FaultStore(FileRunStore):
        def save_receipt(self,run_id,invocation_id,receipt,lease):
            super().save_receipt(run_id,invocation_id,receipt,lease);saved.append(deepcopy(receipt))
            if receipt['step']=='second':raise LostAck()
    store=FaultStore(tmp_path/'store',namespace='effort');store.initialize();run_id=uuid4().hex
    try:
        with scripted_provider(wire) as provider:
            rec=MemoryRecorder(provider_id=wire);rt=host['build_runtime'](project=project,base_url=provider.url,provider=wire,accounting=rec)
            flow=host['workflow'](rt,project=project);provider.queue_text('{"approved":true}');provider.queue_text('{"approved":true}')
            h=Harness(flow,store=store,run_id=run_id,runtime=rt,context=ExecutionContext(tenant_id='trusted'))
            assert h.run({})['status']=='waiting'
            store.close();store=FaultStore(tmp_path/'store',namespace='effort');store.initialize();h=Harness(flow,store=store,run_id=run_id,runtime=rt)
            with pytest.raises(LostAck):h.resume(choice='approve',expected_revision=h.status().revision)
            assert len(saved)==len(provider.requests)==2
            ids={r['result']['metadata'][KEY]['attempts'][0]['provider_call_id'] for r in saved};assert ids==set(rec.intents)
            accounting_before=deepcopy((rec.intents,rec.observations))
            receipt_bytes=[json.dumps(r,sort_keys=True,separators=(',',':')).encode() for r in saved]
            store.close();store=FileRunStore(tmp_path/'store',namespace='effort');store.initialize();h=Harness(flow,store=store,run_id=run_id,runtime=rt)
            assert h.recovery_evidence()['recoveryStatus']=='receiptAvailable'
            assert h.resume()['status']=='completed' and len(provider.requests)==2
            assert (rec.intents,rec.observations)==accounting_before
            for r,original_bytes in zip(saved,receipt_bytes):
                loaded=store.load_receipt(run_id,r['id']);assert loaded==r
                assert json.dumps(loaded,sort_keys=True,separators=(',',':')).encode()==original_bytes

    finally:store.close()


def test_actual_pre_effort_file_receipts_adopt_without_inventing_trace(tmp_path,wire,create_legacy_receipts):
    from types import SimpleNamespace
    from prosaic_harness import Harness,FileRunStore
    from prosaic_runtime.accounting import MemoryRecorder
    project,host=copied(tmp_path);run_id=uuid4().hex;directory=tmp_path/'legacy-store'
    with scripted_provider(wire) as provider:
        provider.queue_text('{"approved":true}');provider.queue_text('{"approved":true}')
        old=create_legacy_receipts(kind='file',project=project,url=provider.url,wire=wire,
                                   run_id=run_id,directory=directory)
        assert old['runtimeVersion']=='0.9.17' and len(provider.requests)==2
        assert len(old['accounting']['intents'])==len(old['accounting']['observations'])==2
        original=[json.dumps(r,sort_keys=True,separators=(',',':')).encode() for r in old['receipts']]
        recorder=MemoryRecorder(provider_id=wire)
        runtime=host['build_runtime'](project=project,base_url=provider.url,provider=wire,accounting=recorder)
        store=FileRunStore(directory,namespace='effort');store.initialize()
        try:
            h=Harness(host['workflow'](runtime,project=project),store=store,run_id=run_id,runtime=runtime)
            assert h.recovery_evidence()['recoveryStatus']=='receiptAvailable'
            assert h.resume()['status']=='completed' and len(provider.requests)==2
            assert recorder.intents==recorder.observations=={}
            for receipt,encoded in zip(old['receipts'],original):
                loaded=store.load_receipt(run_id,receipt['id'])
                assert json.dumps(loaded,sort_keys=True,separators=(',',':')).encode()==encoded
                assert KEY not in loaded['result']['metadata']
                assert host['effort_report'](SimpleNamespace(metadata=loaded['result']['metadata']))=={'available':False,'trace':None}
        finally:store.close()


@pytest.mark.parametrize('first',['http','native'])
def test_public_pool_fallback_retains_both_transport_attempts(tmp_path,first):
    from prosaic_runtime import UnifiedRuntime,UnifiedRuntimeConfig,NativeRuntimeConfig,NativeProfile,NativePolicy,ProfilePool,PoolPolicy,RunPolicy
    project,host=copied(tmp_path);executable=tmp_path/'fake-codex'
    events=([{'type':'turn.failed','error':{'code':'usage_limit_reached'}}] if first=='native' else
            [{'type':'item.completed','item':{'type':'agent_message','text':'done'}},{'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}}])
    executable.write_text(f'#!{sys.executable}\nimport sys\nsys.stdin.read()\nprint({"".join(json.dumps(e)+chr(10) for e in events)!r},end="")\nsys.exit({1 if first=="native" else 0})\n');executable.chmod(0o755)
    with effort_provider('openai-compatible',status=429 if first=='http' else 200) as provider:
        provider.queue_text('done');api=host['build_runtime'](project=project,base_url=provider.url)
        native=NativeRuntimeConfig({'native':NativeProfile('codex-cli','synthetic','native',str(executable),effort='low')},default_profile='native')
        order=('local','native') if first=='http' else ('native','local')
        config=UnifiedRuntimeConfig(native,api.config,{'pool':ProfilePool(order)},'pool',{'local':'api'},capacity_file=str(tmp_path/'capacity.json'))
        result=UnifiedRuntime(config).run(host['load_agent'](project),cwd=tmp_path,
            policy=PoolPolicy(timeout_s=5,max_attempts=2,max_native_attempts=1,native_policy=NativePolicy(),api_policy=RunPolicy(max_provider_requests=2,max_tool_calls=0),required_capabilities=frozenset({KEY})))
        assert result.exit_code==0
        trace=rows(result,2);assert [r['transport'] for r in trace]==(['http','process'] if first=='http' else ['process','http'])
        assert len(provider.requests)==1


def test_public_unified_override_keeps_unused_default_as_annotation_only(tmp_path):
    from prosaic_runtime import UnifiedRuntime,UnifiedRuntimeConfig,NativeRuntimeConfig,NativeProfile,NativePolicy,ProfilePool,PoolPolicy
    project,host=copied(tmp_path);a=host['load_agent'](project);a=replace(a,frontmatter={**a.frontmatter,'effort':'high'})
    executable=tmp_path/'fake-codex'
    executable.write_text(f'#!{sys.executable}\nimport sys,json\nsys.stdin.read()\ntext=json.dumps(sys.argv[1:])\n'+
        "print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':text}}))\nprint(json.dumps({'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}}))\n")
    executable.chmod(0o755)
    native=NativeRuntimeConfig({'native':NativeProfile('codex-cli','synthetic','fixture',str(executable),effort='max')},default_profile='native')
    config=UnifiedRuntimeConfig(native,None,{'pool':ProfilePool(('native',))},'pool',{},capacity_file=str(tmp_path/'capacity.json'))
    result=UnifiedRuntime(config).run(a,cwd=tmp_path,policy=PoolPolicy(timeout_s=5,max_attempts=1,max_native_attempts=1,native_policy=NativePolicy()))
    assert result.exit_code==0
    row=rows(result,1)[0]
    assert row['requested_effort']=='high' and row['configured_effort']=='max'
    assert row['sent']=={'argv':['-c','model_reasoning_effort="high"']}
    assert row['sent']['argv'][1] in json.loads(result.stdout)
