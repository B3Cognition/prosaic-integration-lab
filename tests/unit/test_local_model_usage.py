"""Real released Runtime/recorder through an owned synthetic local gateway."""
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


def event(value,newline=b'\n'):
    return b'data: '+json.dumps(value,separators=(',',':'),ensure_ascii=False).encode()+newline+newline


def heartbeat():
    return {'id':'chatcmpl-12345678','object':'chat.completion.chunk','created':0,
            'model':'keepalive','choices':[{'index':0,'delta':{'role':'assistant','content':''},
                                          'finish_reason':None}]}


@contextmanager
def provider(tmp_path,body):
    from prosaic_runtime import EndpointConfig
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            self.wfile.write(body);self.wfile.flush()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    key=tmp_path/'key';key.write_text('fixture-only-key')
    try:
        yield EndpointConfig(f'http://127.0.0.1:{server.server_port}/v1','qwen-fixture',
                             api_key_file=str(key)),requests
    finally:
        server.shutdown();server.server_close();worker.join(5)
        assert not worker.is_alive()


@pytest.mark.parametrize('newline',[b'\n',b'\r\n'])
@pytest.mark.parametrize('prefill',['heartbeat','comment','changed-model','heartbeat-with-usage'])
def test_local_prefill_preserves_real_recorder_counts_without_trusting_conflicts(tmp_path,newline,prefill):
    from lab_runner.chat import ModelGateway
    from prosaic_runtime import EndpointConfig,ProsaicArtifact,ProsaicRuntime,RunPolicy,RuntimeConfig
    from prosaic_runtime.accounting import MemoryRecorder
    from prosaic_integration_lab.run_observations import usage_projection
    first=heartbeat()
    if prefill=='changed-model':first.update(model='qwen-other',created=1)
    if prefill=='heartbeat-with-usage':first['usage']={'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}
    prefix=b': keep-alive'+newline+newline if prefill=='comment' else event(first,newline)
    frame={'id':'chatcmpl-12345678','object':'chat.completion.chunk','created':1,'model':'qwen-fixture'}
    content=event({**frame,'choices':[{'index':0,'delta':{'content':'OK'},'finish_reason':'stop'}]},newline)
    # Real oMLX timing extensions remain unsupported for accounting. Their
    # actual integer counts must remain visible as explicitly unqualified data.
    usage=event({**frame,'choices':[],'usage':{'prompt_tokens':7,'completion_tokens':2,
        'total_tokens':9,'total_time':1.5}},newline)
    body=prefix+content+usage+b'data: [DONE]'+newline+newline
    recorder=MemoryRecorder()
    with provider(tmp_path,body) as (profile,requests),ModelGateway(profile,maximum=1) as gateway:
        config=RuntimeConfig({'fixture':EndpointConfig(gateway.url,'qwen-fixture',
            features={'streaming':True})},{},'fixture')
        artifact=ProsaicArtifact.from_inspection({'id':'usage.md','type':'subagent',
            'frontmatter':{'tools':[]},'body':'Reply OK.'})
        result=ProsaicRuntime(config,accounting=recorder).run(artifact,
            policy=RunPolicy(timeout_s=5,max_provider_requests=1,max_tool_calls=0))
        assert result.exit_code==0 and result.stdout=='OK'
        assert gateway.used==1 and len(requests)==1
        assert requests[0]['stream_options']=={'include_usage':True}
    assert len(recorder.observations)==1
    observation=next(iter(recorder.observations.values()))
    if prefill in {'heartbeat','comment'}:
        assert observation['usage']['status']=='unsupported'
        assert observation['usage']['input_tokens']==7 and observation['usage']['output_tokens']==2
        projection=usage_projection([{'measurement_state':'unsupported','observation':observation}])
        assert projection['input'] is None and projection['output'] is None
        assert projection['providerReported']=={'input':7,'output':2,'unqualifiedCalls':1,'unknownCalls':0}
    else:
        assert observation['usage']['status']=='untrusted'
        assert 'providerReported' not in usage_projection([
            {'measurement_state':'quarantined','observation':observation}])


@pytest.mark.parametrize('width',[1,2,7,4096])
@pytest.mark.parametrize('newline',[b'\n',b'\r\n'])
def test_local_prefill_adapter_preserves_fragmented_unicode_and_all_nonheartbeat_bytes(width,newline):
    from lab_runner.chat import _local_sse_chunks
    real=event({'model':'qwen-fixture','choices':[{'delta':{'content':'東京 🧪'}}]},newline)
    rest=real+b': still alive'+newline+newline+b'data: [DONE]'+newline+newline+b'data: incomplete'
    raw=event(heartbeat(),newline)+rest
    chunks=(raw[i:i+width] for i in range(0,len(raw),width))
    assert b''.join(_local_sse_chunks(chunks))==b': keep-alive\n\n'+rest


def test_local_prefill_adapter_yields_before_reading_the_rest_of_the_response():
    from lab_runner.chat import _local_sse_chunks
    advanced=[]
    def chunks():
        yield event(heartbeat())
        advanced.append(True)
        yield b'data: [DONE]\n\n'
    output=iter(_local_sse_chunks(chunks()))
    assert next(output)==b': keep-alive\n\n' and advanced==[]
    assert b''.join(output)==b'data: [DONE]\n\n' and advanced==[True]


@pytest.mark.parametrize('path,value',[
    (('model',),'qwen-other'),(('created',),True),(('created',),1),(('id',),'foreign'),
    (('usage',),None),(('usage',),{'prompt_tokens':7}),
    (('choices',0,'index'),False),(('choices',0,'finish_reason'),'stop'),
    (('choices',0,'delta','content'),'real output'),(('choices',0,'delta','role'),'system'),
    (('choices',0,'delta','tool_calls'),[{'index':0,'function':{'arguments':'{}'}}]),
    (('extension',),'unknown'),
])
def test_local_prefill_adapter_never_hides_content_usage_or_suspicious_metadata(path,value):
    from lab_runner.chat import _local_sse_chunks
    changed=heartbeat();target=changed
    for part in path[:-1]:target=target[part]
    target[path[-1]]=value
    raw=event(changed)
    assert b''.join(_local_sse_chunks([raw]))==raw


@pytest.mark.parametrize('variant',['duplicate','event-field','multiple-data','oversized','invalid-utf8'])
def test_local_prefill_adapter_preserves_noncanonical_frames_for_sdk_validation(variant):
    from lab_runner.chat import _local_sse_chunks
    raw=event(heartbeat())
    if variant=='duplicate':raw=raw.replace(b'"model":"keepalive"',b'"model":"qwen-fixture","model":"keepalive"')
    if variant=='event-field':raw=b'event: message\n'+raw
    if variant=='multiple-data':raw=b'data: \n'+raw
    if variant=='oversized':raw=raw.replace(b'"created":0',b'"created":'+b' '*4096+b'0')
    if variant=='invalid-utf8':raw=raw.replace(b'chatcmpl-',b'chatcmpl-\xff')
    assert b''.join(_local_sse_chunks([raw]))==raw
