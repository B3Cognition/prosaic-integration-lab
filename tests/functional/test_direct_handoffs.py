"""Version2 contract/host-evidence checks at real synthetic wire boundaries."""
import pytest


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('mode,requests,roles',[('worker',2,['worker']),('critic',1,['critic']),
                                               ('handoff',3,['worker','critic'])])
@pytest.mark.parametrize('family',['correct','reject','missing','conflict'])
def test_direct_roles_receive_closed_contracts_and_host_assignment(tmp_path,provider,mode,requests,roles,family):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
    from lab_runner.handoffs.direct import execute_case,recover_case
    from lab_runner.handoffs.direct_scoring import score_direct
    case=example_case(family)
    draft=correct_worker(case,family) if mode=='critic' else None
    with fixture_provider(case,family=family,provider=provider) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='direct',mode=mode,draft=draft)
        assert p.requests==requests==e['counts']['providerRequests']
        assert [r['step'] for r in e['receipts']]==roles
        assert p.contractChecks==requests and not p.errors
        assert e['counts']['toolCalls']==(0 if mode=='critic' else 1)
        assert e['hostAssignment']['caseId']==case['caseId']
        if mode!='critic':assert 'evidence' not in e['checkpoint']['outputs']['worker']
        p.deny=True
        restored=recover_case(case,config=p.config,output=tmp_path,sample_id='direct',mode=mode,draft=draft)
        assert restored['receiptDigests']==e['receiptDigests'] and p.requests==requests
    score=score_direct(case,e)
    assert score['qualityPassed'] and score['safe']
    assert e['checkpoint']['status']==('completed' if family in ('correct','reject') else 'waiting')


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('flaw',['decision','status','facts','citations','binding'])
def test_critic_controls_detect_each_flaw_without_any_worker_call(tmp_path,provider,flaw):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
    from lab_runner.handoffs.direct import execute_case
    from lab_runner.handoffs.direct_scoring import score_direct
    case=example_case();draft=correct_worker(case,'correct')
    if flaw=='decision':draft['answer']['decision']='reject'
    if flaw=='status':draft['status']='missing'
    if flaw=='facts':draft['answer']['facts']=[]
    if flaw=='citations':draft['answer']['citations']=[]
    if flaw=='binding':draft['assignmentId']='0'*64
    with fixture_provider(case,provider=provider) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='critic',mode='critic',draft=draft)
        assert p.requests==1 and not p.errors
    score=score_direct(case,e)
    assert score['stages']=={'critic':'passed'} and score['qualityPassed'] and score['safe']
    assert score['control']==True and e['checkpoint']['outputs']['critic']['issues']==[flaw]
    assert e['checkpoint']['status']=='waiting'


@pytest.mark.parametrize('scenario,first,critic',[('wrong_worker','worker','passed'),
    ('missed_flaw','worker','failed'),('false_critic','critic','failed'),
    ('invalid_worker','worker','notRun'),('schema_instead','worker','notRun'),
    ('wrong_binding','worker','notRun'),('unknown_usage','worker','notRun'),
    ('repeat_tools','worker','notRun'),('overrun','worker','notRun'),
    ('invalid_critic','critic','failed'),('wrong_critic_binding','critic','failed')])
def test_direct_host_gates_do_not_depend_on_correct_critic(tmp_path,scenario,first,critic):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case
    from lab_runner.handoffs.direct import execute_case
    from lab_runner.handoffs.direct_scoring import score_direct
    case=example_case()
    with fixture_provider(case,scenario=scenario) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='fault')
        assert p.requests<=4 and e['counts']['toolCalls']<=2
    score=score_direct(case,e)
    assert score['firstFailure']==first and score['stages']['critic']==critic
    assert not score['qualityPassed'] and score['safe'] and e['checkpoint']['status']!='completed'


def test_critic_receives_fetched_current_values_and_no_private_gold(tmp_path):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case
    from lab_runner.handoffs.direct import execute_case
    case=example_case();case['expected']={'PRIVATE-GOLD-NEVER-SEND':'reject'}
    with fixture_provider(case,scenario='wrong_worker') as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='evidence')
        critic=p.arguments[-1]
        assert critic['currentEvidence']['origin']=='workerLookup'
        assert critic['currentEvidence']['records']==[case['records']['metrics'],case['records']['incident']]
        assert 'PRIVATE-GOLD-NEVER-SEND' not in str(p.payloads)
        assert all('currentEvidence' not in args for args in p.arguments[:-1])
    assert 'currentEvidence' not in e['receipts'][-1]['arguments']
    assert e['checkpoint']['outputs']['critic']['issues']==['decision']


@pytest.mark.parametrize('provider',['openai','anthropic'])
def test_direct_shared_budget_blocks_critic_and_reuse_cannot_dispatch(tmp_path,provider):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case
    from lab_runner.handoffs.direct import execute_case,recover_case
    from lab_runner.handoffs.direct_scoring import score_direct
    from lab_runner.quality.contracts import decode
    from prosaic_runtime import TokenCounterDescriptor,TokenCounterRegistration
    class Counter:
        calls=0
        def count_tokens(self,native):
            self.calls+=1
            return 100 if self.calls<=2 else 7600
    case=example_case()
    with fixture_provider(case,provider=provider) as p:
        ep=p.config.profiles['fixture']
        counter=TokenCounterRegistration(TokenCounterDescriptor(identity='direct-budget-test',provider=ep.provider,
            model=ep.model,framing_revision='anthropic-messages-v1' if provider=='anthropic' else 'openai-chat-v1',
            context_capacity_tokens=32768,implementation_version='test-v1',tokenizer_assets_digest='a'*64,
            template_assets_digest='b'*64,counting_kind='exact',guarantee='Synthetic test units only.'),Counter())
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='shared',token_counter=counter)
        assert p.requests==2 and e['checkpoint']['status']=='blocked'
        trace=(tmp_path/'shared-context-trace.json').read_bytes()
        with pytest.raises(ValueError,match='receipt-only'):
            execute_case(case,config=p.config,output=tmp_path,sample_id='shared',token_counter=counter)
        p.deny=True
        restored=recover_case(case,config=p.config,output=tmp_path,sample_id='shared')
        assert restored['receiptDigests']==e['receiptDigests'] and p.requests==2
        assert (tmp_path/'shared-context-trace.json').read_bytes()==trace
        assert len(decode(trace)['proposals'])==3
    assert score_direct(case,e)['safe'] and not score_direct(case,e)['qualityPassed']


@pytest.mark.parametrize('record_ids',[[],['metrics','metrics'],['foreign'],[{}],['metrics',1]])
def test_control_record_selection_rejected_before_dispatch(tmp_path,record_ids):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
    from lab_runner.handoffs.direct import execute_case
    case=example_case()
    with fixture_provider(case) as p:
        with pytest.raises(ValueError,match='controlled evidence'):
            execute_case(case,config=p.config,output=tmp_path,sample_id='bad-control',mode='critic',
                draft=correct_worker(case),record_ids=record_ids)
        assert p.requests==0


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('mode',['worker','critic','handoff'])
def test_unread_is_not_missing_and_critic_can_be_qualified_independently(tmp_path,provider,mode):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
    from lab_runner.handoffs.direct import execute_case
    from lab_runner.handoffs.direct_scoring import score_direct
    case=example_case()
    controls=dict(draft=correct_worker(case,'unread'),record_ids=['metrics']) if mode=='critic' else {}
    with fixture_provider(case,provider=provider,family='unread') as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='unread',mode=mode,**controls)
        assert not p.errors
    score=score_direct(case,e)
    assert score['safe'] and score['qualityPassed']==(mode=='critic')
    assert e['checkpoint']['status']=='waiting'
    if mode!='worker':assert score['stages']['critic']=='passed'
    if mode!='critic':assert e['checkpoint']['outputs']['worker']['status']=='unread'


def test_authority_and_revision_are_selected_before_values(tmp_path):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case
    from lab_runner.handoffs.direct import execute_case
    from lab_runner.handoffs.direct_scoring import score_direct
    case=example_case()
    for key,authority,revision in [('stale','auditor',1),('untrusted','observer',100)]:
        row=case['records']['metrics']|dict(recordId=key,authority=authority,revision=revision,value=1)
        case['records'][key]=row
        case['recordIndex'].append({k:row[k] for k in ('recordId','factId','authority','revision')})
    with fixture_provider(case) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='authority')
        assert not p.errors
    assert score_direct(case,e)['qualityPassed']


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('scenario',['missed_flaw','false_critic','invalid_critic','wrong_critic_binding'])
def test_critic_alone_fails_bad_reviews_without_worker_dispatch(tmp_path,provider,scenario):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
    from lab_runner.handoffs.direct import execute_case
    from lab_runner.handoffs.direct_scoring import score_direct
    case=example_case();draft=correct_worker(case)
    if scenario=='missed_flaw':draft['answer']['decision']='reject'
    with fixture_provider(case,provider=provider,scenario=scenario) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='critic-fault',mode='critic',draft=draft)
        assert p.requests==1 and not p.errors
    score=score_direct(case,e)
    assert score['control'] and score['stages']==dict(critic='failed')
    assert not score['qualityPassed'] and score['safe'] and e['counts']['toolCalls']==0
