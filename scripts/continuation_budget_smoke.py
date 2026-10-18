"""Installed provider-neutral continuation admission; synthetic loopback only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Event,Thread
import json
import sys


def has_result(native):
    return any(m.get('role')=='tool' or isinstance(m.get('content'),list) and
        any(b.get('type')=='tool_result' for b in m['content'] if isinstance(b,dict))
        for m in native['messages'])


@contextmanager
def fixture(provider,*,text_only=False,unknown=False,overrun=False,hold=False):
    class State:
        requests=0
        started=Event()
        release=Event()
    state=State()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            native=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            state.requests+=1;state.started.set()
            if hold and not state.release.wait(10):self.send_error(504);return
            tool=not text_only and not has_result(native)
            output=1500 if overrun else 50
            if provider=='anthropic':
                assert self.path=='/v1/messages'
                content=([dict(type='tool_use',id='lookup1',name='lookup',input={})] if tool else
                    [dict(type='text',text='done')])
                result=dict(id='synthetic',type='message',role='assistant',model=native['model'],
                    content=content,stop_reason='tool_use' if tool else 'end_turn',
                    usage=dict(input_tokens=100,output_tokens=output))
            else:
                assert self.path=='/v1/chat/completions'
                message=(dict(role='assistant',content=None,tool_calls=[dict(id='lookup1',type='function',
                    function=dict(name='lookup',arguments='{}'))]) if tool else dict(role='assistant',content='done'))
                result=dict(id='synthetic',model=native['model'],choices=[dict(index=0,message=message,
                    finish_reason='tool_calls' if tool else 'stop')],usage=dict(prompt_tokens=100,
                    completion_tokens=output,total_tokens=100+output))
            if unknown:result.pop('usage')
            raw=json.dumps(result).encode();self.send_response(200)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    state.url=f'http://127.0.0.1:{server.server_port}/v1'
    try:yield state
    finally:
        state.release.set();server.shutdown();server.server_close();thread.join(timeout=3)
        assert not thread.is_alive()


def setup(provider,fx,*,count=1307,text_only=False):
    from prosaic_runtime import (TokenCounterDescriptor,TokenCounterRegistration,
        ExecutionBudget,CustomTool,EndpointConfig,RuntimeConfig,ProsaicRuntime,ProsaicArtifact,RunPolicy)
    from lab_runner.memory_policy.budget import make_plan,guard_registration
    class Counter:
        def count_tokens(self,native):return count if text_only or has_result(native) else 100
    desc=TokenCounterDescriptor(identity='synthetic-continuation-'+provider,provider=provider,
        model='continuation-fixture',framing_revision='anthropic-messages-v1' if provider=='anthropic' else 'openai-chat-v1',
        context_capacity_tokens=32768,implementation_version='synthetic-v1',tokenizer_assets_digest='a'*64,
        template_assets_digest='b'*64,counting_kind='exact',guarantee='Synthetic units only; not tokenizer qualification.')
    plan=make_plan(counter_descriptor=desc.to_dict(),quote_identity='c'*64,request_sha256='d'*64,
        input_bounds=[100]*4,max_requests=4,output_tokens=512,token_ceiling=8192,
        reported_tokens=0,inflight_tokens=0,continuation_budget=True)
    guard=guard_registration(TokenCounterRegistration(desc,Counter()),plan)
    budget=ExecutionBudget(timeout_s=600,max_provider_requests=4,max_tool_calls=2,
        max_reported_tokens=8192,token_counter=guard.registration)
    tools={} if text_only else {'lookup':CustomTool('lookup','Read synthetic records',
        {'type':'object','additionalProperties':False},lambda args:{'records':['x'*2048]},'v1')}
    endpoint=EndpointConfig(fx.url,desc.model,provider=provider,max_tokens=512,features={'streaming':False})
    runtime=ProsaicRuntime(RuntimeConfig({'fixture':endpoint},{},'fixture',frozenset(tools)),custom_tools=tools)
    agent=ProsaicArtifact('synthetic','subagent',{'tools':list(tools)},'Read the records and answer.')
    policy=RunPolicy(allowed_tools=frozenset(tools),timeout_s=600,max_provider_requests=4,
        max_tool_calls=2,max_reported_tokens=8192,bounded_tool_recovery=True)
    return runtime,agent,policy,budget,guard


def run():
    results=[]
    for provider in ('openai-compatible','anthropic'):
        for mode in ('variable','exact-fit','exhausted','unknown','overrun','concurrent','request-cap'):
            text=mode in {'unknown','overrun','concurrent','request-cap'}
            with fixture(provider,text_only=text,unknown=mode=='unknown',overrun=mode=='overrun',hold=mode=='concurrent') as fx:
                count={'exact-fit':7530,'exhausted':7600,'concurrent':4000}.get(mode,1307 if not text else 100)
                runtime,agent,policy,budget,guard=setup(provider,fx,count=count,text_only=text)
                def invoke():
                    with budget.activate():return runtime.run(agent,policy=policy)
                if mode=='concurrent':
                    with ThreadPoolExecutor(max_workers=1) as pool:
                        first=pool.submit(invoke)
                        try:
                            assert fx.started.wait(5)
                            assert budget.reserved_tokens==4512
                            second=invoke()
                            assert second.metadata['failure_reason']=='token_limit'
                            assert fx.requests==budget.provider_requests==1
                        finally:fx.release.set()
                        assert first.result(timeout=5).exit_code==0
                    assert budget.reported_tokens==150 and budget.reserved_tokens==0
                elif mode=='request-cap':
                    assert all(invoke().exit_code==0 for _ in range(4))
                    assert invoke().exit_code!=0 and fx.requests==budget.provider_requests==4
                else:
                    result=invoke()
                    if mode in {'variable','exact-fit'}:
                        assert result.exit_code==0 and fx.requests==2 and budget.reported_tokens==300
                        assert budget.tool_calls==1 and budget.reserved_tokens==0
                        assert guard.proposals[1]['inputBound']==count
                        assert guard.proposals[1]['quotedInputBound']==100
                    elif mode=='exhausted':
                        assert result.metadata['failure_reason']=='token_limit'
                        assert fx.requests==1 and budget.reported_tokens==150
                        assert guard.proposals[-1]['reason']=='withinContext'
                    elif mode=='unknown':
                        assert not budget.usage_complete and budget.reserved_tokens==612
                        assert invoke().metadata['failure_reason']=='usage_unknown' and fx.requests==1
                    else:
                        assert result.metadata['failure_reason']=='token_reservation_exceeded'
                        assert budget.reservation_exceeded and budget.reported_tokens==1600
                        assert invoke().metadata['failure_reason']=='token_reservation_exceeded' and fx.requests==1
                assert budget.provider_requests<=4 and budget.tool_calls<=2
                results.append(dict(provider=provider,mode=mode,providerRequests=fx.requests,
                    toolCalls=budget.tool_calls,reportedTokens=budget.reported_tokens,
                    usageComplete=budget.usage_complete,reservedTokens=budget.reserved_tokens))
    return dict(version=1,origin='synthetic-loopback-only',scenarios=len(results),liveDispatches=0,
        limits=dict(providerRequests=4,toolCalls=2,reportedTokens=8192,timeoutSeconds=600,outputTokens=512),results=results)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    import lab_runner.memory_policy as package
    origin=Path(package.__file__).resolve()
    assert origin.is_relative_to(Path(sys.prefix).resolve()) and not origin.is_relative_to(args.source_root.resolve())
    report=run();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('Installed continuation budget qualification passed:',report['scenarios'],'synthetic scenarios; no live inference.')


if __name__=='__main__':main()
