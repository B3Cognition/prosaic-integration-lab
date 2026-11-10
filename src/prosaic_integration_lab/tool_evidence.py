"""Synthetic public consumer witnesses; sanitized reports contain no source payload."""
from dataclasses import replace
import json,re,time,uuid

CASES=('safe-approved-event','event-only-legacy-return','denied-secret-display','admitted-typed-output',
    'fabricated-citation','selected-inline-citation','exact-deferred-partial-read','replay-one-effect',
    'receipt-adoption-zero-work','retained-source-revocation','metadata-number-guard-isolation','unsupported-forged-delivery')
TRAIN={'b3-prosaic':'0.5.0','b3-prosaic-runtime':'0.9.20.dev2','b3-prosaic-runtime-postgres':'0.3.0',
    'b3-prosaic-harness':'0.9.14.dev2','b3-prosaic-harness-postgres':'0.4.3.dev2'}


def require_tool_evidence_sdk():
    from importlib import metadata
    from pathlib import Path
    import prosaic_runtime as runtime,prosaic_harness as harness
    if not {'tool_events_v1','tool_results_v1','citations_v1'}<=runtime.ProsaicRuntime.capabilities or not hasattr(harness,'VerifiedToolReceipt'):
        raise ValueError('installed tool evidence capability unavailable')
    import importlib
    for module,name in [('prosaic','b3-prosaic'),('prosaic_runtime','b3-prosaic-runtime'),('prosaic_runtime_postgres','b3-prosaic-runtime-postgres'),
            ('prosaic_harness','b3-prosaic-harness'),('prosaic_harness_postgres','b3-prosaic-harness-postgres')]:
        owner=metadata.distribution(name);source=Path(importlib.import_module(module).__file__).resolve()
        if owner.version!=TRAIN[name] or 'site-packages' not in source.parts or source not in {Path(owner.locate_file(f)).resolve() for f in owner.files}:
            raise ValueError('installed tool evidence SDK identity differs')


def _id(payload,kind='ev'):
    return re.findall(kind+r'_[0-9a-f]{64}',json.dumps(payload))[-1]


def run_tool_evidence_scenario(case,*,provider,session_store=None,journal=None):
    require_tool_evidence_sdk()
    if case not in CASES:raise ValueError('unknown tool evidence scenario')
    import prosaic_runtime as runtime,prosaic_harness as harness
    from lab_runner.tool_evidence import endpoint
    from lab_runner.blueprints.tool_evidence.host import bindings,dependents_tool
    from prosaic_harness.context_packs import capture_sources
    calls=[];events=[];allowed=[True]
    records=[{'name':'dependent-'+str(index)} for index in range(14)]
    with endpoint(provider) as (url,requests,replies):
        binding=bindings(base_url=url,provider=provider,lookup=lambda component:calls.append(component) or records,
            evidence_allowed=lambda use:allowed[0],display_allowed=lambda use:case!='denied-secret-display')
        if case=='event-only-legacy-return':
            tool=dependents_tool(lambda component:calls.append(component) or records,legacy=True)
            rt=runtime.ProsaicRuntime(binding.config,custom_tools={'dependents':tool})
            scope=runtime.InvocationScope(uuid.uuid4().hex)
            result=rt.run_tool('dependents',{'component':'csb-frontend','credential':'PRIVATE-ARG'},policy=binding.run_policy,
                tool_contract_bindings=replace(binding.tool_contracts.bind(scope),citations=None),on_event=events.append)
            assert result.exit_code==0 and json.loads(result.stdout)=={'count':14,'dependents':records}
            assert len(calls)==1 and requests==[]
        elif case=='unsupported-forged-delivery':
            from prosaic_runtime.structured_tools import StructuredToolLoop,ToolRequest
            scope=runtime.InvocationScope(uuid.uuid4().hex)
            try:
                runtime.NativeRuntime(binding.config).turn(binding.agent,message='Review',tool_contract_bindings=binding.tool_contracts.bind(scope))
            except (ValueError,runtime.TurnAdmissionError):pass
            else:raise AssertionError('native citations accepted')
            loop=StructuredToolLoop(binding._tools,arguments={},deadline=time.monotonic()+30,allowed_tools={'dependents'},
                tool_contract_bindings=replace(binding.tool_contracts.bind(scope),citations=None))
            _,data=loop.dispatch(ToolRequest('dependents',{'component':'csb-frontend'}))
            try:loop.attest_delivery(runtime.Result(0,json.dumps(data),''))
            except ValueError:pass
            else:raise AssertionError('bare output became delivery')
            assert loop.evidence.to_dict()['deliveries']=={} and requests==[] and len(calls)==1
        elif case=='replay-one-effect':
            if journal is None:
                raise ValueError('explicit host journal fixture required')
            original=binding._tools['dependents']
            tool=runtime.CustomTool('dependents',original.description,original.parameters,
                lambda args,ctx:calls.append(args['component']) or runtime.ToolResultV1(data={'count':14},evidence=(runtime.EvidenceDraftV1('graph','r1','PRIVATE-LOCATOR','/count','Dependents'),)),
                '1',with_context=True,operation_key=lambda args,ctx:'operation',result_contract=runtime.ToolResultContractV1('1'),event_policy=original.event_policy)
            rt=runtime.ProsaicRuntime(binding.config,custom_tools={'dependents':tool})
            for _ in range(2):
                scope=runtime.InvocationScope(uuid.uuid4().hex,operation_namespace='fixture-'+getattr(journal,'identity','owned'))
                result=rt.run_tool('dependents',{'component':'csb-frontend'},policy=binding.run_policy,tool_journal=journal,
                    operation_context=scope,tool_contract_bindings=replace(binding.tool_contracts.bind(scope),citations=None),on_event=events.append)
                assert result.exit_code==0
            assert len(calls)==1 and requests==[] and any(event.get('toolEventV1',{}).get('phase')=='replayed' for event in events)
        else:
            store=session_store
            if store is None:store=harness.MemorySessionStore(namespace='tool-evidence');store.initialize(tool_contracts=True,context_packs=True)
            scope=harness.ConversationScope(store.namespace,'sandbox','tool-evidence','tenant','actor')
            candidates=None
            if case in {'selected-inline-citation','exact-deferred-partial-read'}:
                deferred=case=='exact-deferred-partial-read'
                pack_scope=harness.ContextScope(**dict(namespace=scope.namespace,environment=scope.environment,application=scope.application,tenant=scope.tenant,actor=scope.actor))
                spec=harness.ContextPackSpec('selected','1',[harness.ContextSlot('task',required=True),harness.ContextSlot('facts',
                    required=False,availability='discoverable' if deferred else 'inline')],task_source='task')
                packs=harness.ContextPackBindings(specs={'selected':spec},sources={'task':harness.InputSource('/task'),'facts':harness.InputSource('/facts')},
                    scope=pack_scope,authorizer=harness.ContextAuthorizer('packs','1',lambda use:True))
                source={'task':'Review dependents','facts':'14 dependents; PRIVATE-NEIGHBOR'}
                candidates=harness.ContextPacker().compose(spec,capture_sources(spec,{'request':source},{},packs))
                reader=harness.ContextPackReader(tool_contracts=True) if deferred else None
                tools={'read_context_item':reader.as_tool()} if reader else {}
                config=replace(binding.config,allowed_tools=frozenset(tools))
                agent=runtime.ProsaicArtifact('analyst','subagent',{'name':'analyst','description':'Selected evidence','tools':list(tools)},'ALWAYS cite exact supplied evidence.')
                binding=harness.ConversationBindings(agent,version='pack-1',config=config,policy=harness.ConversationPolicy(),context_packs=packs,
                    custom_tools=tools,tool_contracts=binding.tool_contracts,
                    run_policy=runtime.RunPolicy(allowed_tools=frozenset(tools),max_provider_requests=2 if deferred else 1,max_tool_calls=1 if deferred else 0))
                if deferred:
                    parent=candidates.variants[0]['index'][0]['citationId']
                    replies.extend([{'name':'read_context_item','input':{'citationId':parent,'start':0,'end':13}},lambda payload:'Captured [cite:'+_id(payload)+']'])
                else:replies.append(lambda payload:'Captured [cite:'+_id(payload,'ctx')+']')
            elif case=='fabricated-citation':replies.append('Fabricated [cite:ev_'+'0'*64+']')
            else:
                replies.append({'name':'dependents','input':{'component':'csb-frontend','credential':'PRIVATE-ARG'}})
                replies.append(lambda payload:('EUR 424242' if case=='metadata-number-guard-isolation' else '14 dependents')+' [cite:'+_id(payload)+']')
            if case=='metadata-number-guard-isolation':
                from prosaic_runtime.guards import value_in_tool_output
                agent=runtime.ProsaicArtifact('analyst','subagent',binding.agent.frontmatter,binding.agent.body+'\nALWAYS use values. <!-- enforce: value_in_tool_output(stage=final, on_violation=fail) -->')
                binding=harness.ConversationBindings(agent,version='guard-1',config=binding.config,policy=binding.policy,custom_tools=binding._tools,
                    run_policy=binding.run_policy,tool_contracts=binding.tool_contracts,guards=[value_in_tool_output(tool_result_contract='v1')])
            chat=harness.Conversation(binding,store=store,scope=scope);session=chat.create()
            options=dict(message_id='one',message='Find actual dependents',expected_revision=session.revision,context_pack=candidates)
            def observer(event):
                events.append(event)
                if case=='receipt-adoption-zero-work' and event['event']=='receiptSaved':raise RuntimeError('fixture lost acknowledgment')
            if case=='receipt-adoption-zero-work':
                try:chat.send(session.session_id,on_event=observer,**options)
                except RuntimeError:pass
                else:raise AssertionError('crash fixture did not fire')
                result=harness.Conversation(binding,store=store,scope=scope).recover(session.session_id)
            else:result=chat.send(session.session_id,on_event=observer,**options)
            if case in {'fabricated-citation','metadata-number-guard-isolation'}:
                assert result.document['failureCode']==('citationViolation' if case=='fabricated-citation' else 'ruleViolation')
            else:
                assert result.document['status']=='completed' and result.document['citations']['markers']
                state=store.load_session(session.session_id,scope=scope).state;aid=state['turns'][0]['attempts'][0]
                eid=result.document['citations']['markers'][0]['evidenceId']
                view=chat.citation_view(session.session_id,aid,eid);assert view['available'] and 'PRIVATE' not in json.dumps(view)
                if case=='exact-deferred-partial-read':
                    assert view['content']=='14 dependents' and eid!=parent and 'PRIVATE-NEIGHBOR' not in json.dumps(requests)
                    replies.append('Unopened parent [cite:'+parent+']')
                    bad=chat.send(session.session_id,message_id='parent',message='Cite the index',expected_revision=result.document['revision'],context_pack=candidates)
                    assert bad.document['failureCode']=='citationViolation'
                if case=='retained-source-revocation':
                    ref=chat.retain_citation(session.session_id,aid,eid);allowed[0]=False
                    assert not chat.citation_view(session.session_id,aid,eid)['available']
                    try:chat.history(session.session_id)
                    except harness.ConversationError as error:assert error.code=='evidenceUseDenied'
                    else:raise AssertionError('revoked history remained readable')
                    implicit=chat.send(session.session_id,message_id='two',message='Continue without imports',expected_revision=result.document['revision'])
                    assert implicit.document['failureCode']=='evidenceUseDenied'
                    denied=chat.send(session.session_id,message_id='three',message='Reuse',expected_revision=implicit.document['revision'],retained_evidence=(ref,))
                    assert denied.document['failureCode']=='evidenceUseDenied'
                if case=='admitted-typed-output':assert view['content']==records and 'count' not in view
                if case=='safe-approved-event':assert any(event.get('toolEventV1',{}).get('display',{}).get('count')==14 for event in events)
            assert len(requests)==(3 if case=='exact-deferred-partial-read' else 1 if case in {'fabricated-citation','selected-inline-citation'} else 2)
            assert len(calls)==(0 if candidates is not None or case=='fabricated-citation' else 1)
        assert all(value not in json.dumps(events) for value in ('PRIVATE-ARG','PRIVATE-LOCATOR','PRIVATE-NEIGHBOR'))
        if case=='denied-secret-display':assert not any('display' in e.get('toolEventV1',{}) for e in events)
        return dict(version=1,case=case,provider=provider,passed=True,providerRequests=len(requests),effects=len(calls))
