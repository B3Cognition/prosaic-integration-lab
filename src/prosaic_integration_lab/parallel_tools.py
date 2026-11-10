"""Public SDK witnesses. Reports carry case identity and counts, never source data."""
from dataclasses import replace
from threading import Barrier,Event,Lock,get_ident
from concurrent.futures import ThreadPoolExecutor
import json,re,uuid

CASES=('independent-overlap','concurrency-windows','ordered-evidence','serial-barrier','atomic-batch-admission','current-authorization','cancel-drain','uncertain-journal','same-key-replay','controlled-failure','guard-stop-retains-completion','safe-settlement-events','delivered-citations','bounded-buffers','receipt-adoption','lease-owner-fencing')
TRAIN={'b3-prosaic':'0.5.0','b3-prosaic-runtime':'0.9.21.dev1','b3-prosaic-runtime-postgres':'0.3.0','b3-prosaic-harness':'0.9.15.dev1','b3-prosaic-harness-postgres':'0.4.4.dev1'}


def require_parallel_tool_sdk():
    from pathlib import Path
    import prosaic_runtime as rt,prosaic_harness as h
    if 'parallel_tool_calls_v1' not in rt.ProsaicRuntime.capabilities or not hasattr(h.WorkflowPolicy(),'parallel_tools'):raise ValueError('parallel SDK capability missing')
    if any('site-packages' not in Path(module.__file__).parts for module in (rt,h)):raise ValueError('installed parallel SDKs required')


def _batch(n=2,*,same=False,names=None):
    return dict(calls=[dict(id='call'+str(i),name=names[i] if names else 'lookup',input={'component':str(0 if same else i)}) for i in range(n)])


def run_case(case,provider,*,settings):
    require_parallel_tool_sdk()
    if case not in CASES:raise ValueError('unknown parallel scenario')
    import prosaic_runtime as rt,prosaic_harness as h
    from lab_runner.parallel_tools import endpoint
    from lab_runner.blueprints.parallel_tools.host import build_host
    owner=get_ident();seen=[];events=[];threads=[];gate=Barrier(2);grant=Event();release=Event();cancel=Event();known=Event();lock=Lock();active=[0,0]
    cite_granted=[True]
    n=5 if case=='concurrency-windows' else 3 if case in {'serial-barrier','cancel-drain','guard-stop-retains-completion'} else 2
    concurrent=case not in {'serial-barrier','atomic-batch-admission','current-authorization','uncertain-journal','same-key-replay','controlled-failure','bounded-buffers','receipt-adoption','lease-owner-fencing'}
    def read(a,c):
        i=int(a['component']);threads.append(get_ident());seen.append(i)
        with lock:active[0]+=1;active[1]=max(active)
        try:
            if case=='concurrency-windows':
                if i<4:gate.wait(timeout=3)
                if i>=2:assert len([e for e in events if e['event']=='tool_completed'])>=i//2*2
            elif case in {'ordered-evidence','safe-settlement-events'}:
                gate.wait(timeout=3)
                if i==0:assert release.wait(4)
            elif case=='cancel-drain':gate.wait(timeout=3);assert release.wait(4)
            elif concurrent:gate.wait(timeout=3)
            if case=='current-authorization':grant.set()
            if case=='bounded-buffers':
                if i==0:known.set();return 14
                assert known.wait(3);return rt.ToolResultV1(data={'oversized':'x'*16384})
            if case=='controlled-failure' and i==1:return rt.ToolFailure('not_found')
            return 14+i
        finally:
            with lock:active[0]-=1
    def authorize(a,c):
        if case=='current-authorization' and a['component']=='1':assert grant.wait(3);return False
        return True
    def sink(event):
        events.append(event)
        assert get_ident()==owner or case=='cancel-drain'
        if case in {'ordered-evidence','safe-settlement-events'} and event['event']=='tool_execution_settled' and event['parallelToolV1']['batchIndex']==1:release.set()
    with endpoint(provider) as (url,requests,replies):
        binding=build_host(base_url=url,provider=provider,lookup=read,authorize=authorize,operation_key=(lambda a,c:'same-key') if case in {'same-key-replay','uncertain-journal'} else None,require_citations=case=='delivered-citations',evidence_allowed=lambda use:use.purpose!='cite' or cite_granted[0])
        tools=dict(binding._tools);policy=binding.run_policy;agent=binding.agent;guards=[];scope=rt.InvocationScope(uuid.uuid4().hex,operation_namespace='parallel-'+uuid.uuid4().hex)
        contracts=binding.tool_contracts.bind(scope)
        if case=='serial-barrier':
            original=tools['lookup'];tools['barrier']=rt.CustomTool('barrier','Serial',original.parameters,lambda a,c:seen.append(1) or 15,'1',with_context=True)
            policy=replace(policy,allowed_tools=frozenset({'lookup','barrier'}));agent=rt.ProsaicArtifact('analyst','subagent',{'tools':['lookup','barrier']},agent.body)
        if case=='guard-stop-retains-completion':
            guards=[rt.Guard('reject','1',('after_tool',),lambda stage,ctx:rt.Verdict(False))]
            agent=rt.ProsaicArtifact('analyst','subagent',agent.frontmatter,agent.body+'\nALWAYS check. <!-- enforce: reject(stage=after_tool, on_violation=fail) -->')
        runtime=rt.ProsaicRuntime(replace(binding.config,allowed_tools=policy.allowed_tools),custom_tools=tools,guards=guards)
        replies.extend([_batch(n,same=case=='same-key-replay',names=['lookup','barrier','lookup'] if case=='serial-barrier' else None),'done'])
        if case=='delivered-citations':
            replies[-1]=lambda payload:'Counts '+','.join('[cite:'+eid+']' for eid in dict.fromkeys(re.findall(r'ev_[0-9a-f]{64}',json.dumps(payload))))
        if case in {'receipt-adoption','lease-owner-fencing'}:
            store=settings.get('session_store')
            if store is None:store=h.MemorySessionStore(namespace='parallel');store.initialize(parallel_tools=True)
            scope=h.ConversationScope(store.namespace,'sandbox','parallel','tenant','actor')
            chat=h.Conversation(binding,store=store,scope=scope);session=chat.create()
            if case=='receipt-adoption':
                def saved(event):
                    if event['event']=='receiptSaved':raise RuntimeError('lost acknowledgment')
                try:chat.send(session.session_id,message_id='one',message='Review',expected_revision=session.revision,on_event=saved)
                except RuntimeError:pass
                else:raise AssertionError('receipt boundary not reached')
                before=len(requests),len(seen);result=h.Conversation(binding,store=store,scope=scope).recover(session.session_id)
                assert result.document['status']=='completed' and before==(len(requests),len(seen))==(2,2)
            else:
                foreign=replace(scope,tenant='foreign')
                try:h.Conversation(binding,store=store,scope=foreign).status(session.session_id)
                except (ValueError,h.StoreError):pass
                else:raise AssertionError('foreign owner read accepted')
                with store.lease(session.session_id,scope=scope):
                    try:chat.send(session.session_id,message_id='one',message='Review',expected_revision=session.revision)
                    except (ValueError,h.StoreError):pass
                    else:raise AssertionError('competing owner dispatch accepted')
                if settings.get('session_dsn'):
                    import psycopg
                    with store.lease(session.session_id,scope=scope) as old:
                        with psycopg.connect(settings['session_dsn']) as conn:conn.execute("UPDATE prosaic_harness_conversations.leases SET expires_at=clock_timestamp()-interval '1 second' WHERE session_id=%s",(session.session_id,))
                        with store.lease(session.session_id,scope=scope):
                            try:store.save_session(session.session_id,session.state,session.revision,old,scope=scope)
                            except h.LeaseLost:pass
                            else:raise AssertionError('stale owner save accepted')
                assert not requests and not seen
            return dict(case=case,provider=provider,passed=True,providerRequests=len(requests),toolCallbacks=len(seen))
        options=dict(tool_contract_bindings=contracts,on_event=sink)
        if case in {'same-key-replay','uncertain-journal'}:
            journal=settings['journal'];options['tool_journal']=journal
            if case=='uncertain-journal':
                class LostClaim:
                    identity=journal.identity;contract_version=journal.contract_version
                    def claim(self,*args):journal.claim(*args);raise RuntimeError('lost claim acknowledgment')
                    def commit(self,*args):return journal.commit(*args)
                options['tool_journal']=LostClaim()
        if case=='atomic-batch-admission':policy=replace(policy,max_tool_calls=1)
        if case=='cancel-drain':
            with ThreadPoolExecutor(1) as pool:
                future=pool.submit(runtime.turn,agent,message='Review',policy=policy,cancelled=cancel.is_set,**options)
                try:
                    # A worker-side rendezvous establishes two entered callbacks.
                    while len(seen)<2:
                        if future.done():raise AssertionError('callbacks did not enter')
                        cancel.wait(.01)
                    cancel.set();assert not future.done()
                finally:release.set()
                turn=future.result(timeout=5)
        else:turn=runtime.turn(agent,message='Review',policy=policy,**options)
        evidence=turn.evidence.to_dict();schedule=evidence['parallelToolsV1']['schedule'];calls=[call for batch in schedule['batches'] for call in batch['calls']]
        failed=case in {'atomic-batch-admission','uncertain-journal','cancel-drain','guard-stop-retains-completion','bounded-buffers'}
        assert (turn.result.exit_code!=0)==failed
        if case=='independent-overlap':assert active[1]==2 and len(set(threads))==2
        if case=='concurrency-windows':assert active[1]==2 and sorted(seen)==[0,1,2,3,4]
        if case in {'ordered-evidence','safe-settlement-events'}:
            assert [e['parallelToolV1']['batchIndex'] for e in events if e['event']=='tool_execution_settled']==[1,0]
            assert [c['callIndex'] for c in evidence['toolContractV1']['evidence']['calls']]==[0,1]
            assert 'PRIVATE' not in json.dumps(events)
        if case=='serial-barrier':assert seen==[0,1,2]
        if case=='atomic-batch-admission':
            assert seen==[] and len(requests)==1
            replies[:]=[_batch(names=['lookup','forged']),'unused']
            malformed=runtime.turn(agent,message='Review',policy=binding.run_policy,**options)
            assert malformed.result.exit_code!=0 and seen==[] and len(requests)==2
        if case=='current-authorization':assert seen==[0] and calls[1]['handlerEntered'] is False
        if case=='cancel-drain':assert sorted(seen)==[0,1] and len(requests)==1 and len(evidence['toolOutcomes'])==2
        if case=='uncertain-journal':
            assert not seen
            replies[:]=[_batch(), 'unused'];options['tool_journal']=journal
            again=runtime.turn(agent,message='Review',policy=policy,**options);assert again.result.exit_code!=0 and not seen
        if case=='same-key-replay':assert seen==[0] and [c['state'] for c in calls]==['completed','replayed'] and len([e for e in events if e['event']=='tool_started'])==1
        if case=='controlled-failure':assert calls[1]['outcomeCode']=='controlled_failure' and len(seen)==2
        if case=='guard-stop-retains-completion':assert sorted(seen)==[0,1] and calls[2]['state']=='notStarted' and evidence['toolContractV1']['evidence']['deliveries']=={}
        if case=='delivered-citations':
            assert rt.CitationsV1.from_dict(evidence['toolContractV1']['citations']).verify_answer(turn.result.stdout) and len(requests)==2
            cite_granted[0]=False
            replies[:]=[_batch(),lambda payload:'Results '+','.join('[cite:'+eid+']' for eid in dict.fromkeys(re.findall(r'ev_[0-9a-f]{64}',json.dumps(payload))))]
            revoked=runtime.turn(agent,message='Review',policy=policy,**options)
            assert revoked.result.exit_code!=0 and revoked.result.stdout==''
        if case=='bounded-buffers':assert calls[0]['state']=='completed' and calls[1]['state']=='uncertain'
        assert active[0]==0
        return dict(case=case,provider=provider,passed=True,providerRequests=len(requests),toolCallbacks=len(seen))
