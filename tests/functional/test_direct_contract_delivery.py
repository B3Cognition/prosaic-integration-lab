"""Mutation qualification of the real wire contract, not just scripted outputs."""
from copy import deepcopy
import json
import pytest


@pytest.mark.parametrize('decision',['approve','reject'])
def test_unread_additional_fact_is_insufficient_without_changing_v1(decision):
    from lab_runner.handoffs.direct_fixture import example_case
    from lab_runner.handoffs.contracts import request_for,target
    from lab_runner.handoffs.direct_contracts import expected_worker
    case=example_case('reject' if decision=='reject' else 'correct')
    row=dict(recordId='extra',factId='latency',authority='auditor',revision=3,value=10)
    case['records']['extra']=row
    case['recordIndex'].append({k:row[k] for k in ('recordId','factId','authority','revision')})
    request=request_for(case);rows=[case['records'][k] for k in ('metrics','incident')]
    legacy=target(request,rows);direct=expected_worker(request,rows)
    assert legacy['status']==direct['status']=='unread' and legacy['answer']['decision']==decision
    assert direct['answer']==legacy['answer']|dict(decision='insufficient')


def test_status_precedence_is_conflict_then_unread_then_missing():
    from lab_runner.handoffs.direct_fixture import example_case
    from lab_runner.handoffs.contracts import request_for,assignment
    from lab_runner.handoffs.direct_contracts import expected_worker,instructions
    missing=example_case('missing');request=request_for(missing)
    assert expected_worker(request,[])['status']=='unread'
    assert expected_worker(request,[missing['records']['metrics']])['status']=='missing'
    conflict=example_case('conflict');conflict['records'].pop('incident')
    conflict['recordIndex']=[r for r in conflict['recordIndex'] if r['recordId']!='incident']
    assert expected_worker(request_for(conflict),[])['status']=='conflict'
    for role in ('worker','critic'):
        assert 'Status precedence is conflict, then unread, then missing, then ready.' in instructions(role,assignment(request))


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('mode',['worker','critic','handoff'])
def test_unread_additional_fact_does_not_misgrade_compliant_critic(tmp_path,provider,mode):
    from lab_runner.handoffs.direct_fixture import example_case,fixture_provider,correct_worker
    from lab_runner.handoffs.direct import execute_case
    from lab_runner.handoffs.direct_scoring import score_direct
    case=example_case('extra_unread')
    controls=dict(draft=correct_worker(case,'extra_unread'),record_ids=['metrics','incident']) if mode=='critic' else {}
    with fixture_provider(case,family='extra_unread',provider=provider) as p:
        evidence=execute_case(case,config=p.config,output=tmp_path,sample_id='extra',mode=mode,**controls)
        assert not p.errors
    score=score_direct(case,evidence)
    assert score['safe'] and score['qualityPassed']==(mode=='critic')
    if mode!='worker':assert score['stages']['critic']=='passed'
    assert evidence['checkpoint']['status']=='waiting'


def _map_strings(value,replace):
    if isinstance(value,str):return replace(value)
    if isinstance(value,list):return [_map_strings(v,replace) for v in value]
    if isinstance(value,dict):return {k:_map_strings(v,replace) for k,v in value.items()}
    return value


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('role',['worker','critic'])
def test_each_transmitted_semantic_clause_is_required_and_cannot_be_contradicted(tmp_path,provider,role):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker,_strings,_contract
    from lab_runner.handoffs.direct import execute_case
    case=example_case()
    with fixture_provider(case,provider=provider) as p:
        execute_case(case,config=p.config,output=tmp_path,sample_id='clauses',mode=role,
                     **(dict(draft=correct_worker(case)) if role=='critic' else {}))
        assert not p.errors
        payload=p.payloads[0]
    prompt=next(s for s in _strings(payload) if 'OUTPUT_CONTRACT_BEGIN\n' in s)
    lines=[s for s in prompt.split('OUTPUT_CONTRACT_BEGIN',1)[0].splitlines() if s.strip() and not s.startswith('ROLE ')]
    assert len(lines)>=12
    for line in lines:
        for replacement in ('','CONTRADICTED: '+line.replace('only','never').replace('exactly','arbitrarily')):
            mutated=_map_strings(payload,lambda s:s.replace(line,replacement))
            with pytest.raises(AssertionError,match='guidance'):
                _contract(mutated)


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('role',['worker','critic'])
def test_complete_nested_transmitted_schema_is_independently_qualified(tmp_path,provider,role):
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker,_contract
    from lab_runner.handoffs.direct import execute_case
    case=example_case()
    with fixture_provider(case,provider=provider) as p:
        execute_case(case,config=p.config,output=tmp_path,sample_id='schemas',mode=role,
                     **(dict(draft=correct_worker(case)) if role=='critic' else {}))
        payload=p.payloads[0]
    _,schema,_=_contract(payload)
    mutants=[]
    for key in ('required','additionalProperties'):
        variant=deepcopy(schema)
        node=variant['properties']['answer'] if role=='worker' else variant
        node[key]=[] if key=='required' else True;mutants.append(variant)
    variant=deepcopy(schema)
    node=variant['properties']['answer']['properties']['citations']['items'] if role=='worker' else variant['properties']['issues']
    if role=='worker':node['additionalProperties']=True
    else:node['items']['enum'].append('arbitrary')
    mutants.append(variant)
    for variant in mutants:
        def replace(s):
            if 'OUTPUT_CONTRACT_BEGIN\n' not in s:return s
            before,rest=s.split('OUTPUT_CONTRACT_BEGIN\n',1);_,after=rest.split('\nOUTPUT_CONTRACT_END',1)
            return before+'OUTPUT_CONTRACT_BEGIN\n'+json.dumps(variant)+'\nOUTPUT_CONTRACT_END'+after
        with pytest.raises(AssertionError,match='schema'):
            _contract(_map_strings(payload,replace))


@pytest.mark.parametrize('provider',['openai','anthropic'])
def test_wire_qualification_checks_public_task_index_and_fetched_values(tmp_path,provider):
    from lab_runner.handoffs import direct_fixture as fx
    from lab_runner.handoffs.direct import execute_case
    case=fx.example_case()
    with fx.fixture_provider(case,provider=provider) as p:
        execute_case(case,config=p.config,output=tmp_path,sample_id='inputs',mode='worker')
        first,last=p.payloads
    for key,value in [('task','Different instructions'),('recordIndex',[]),('sourcesSha256','0'*64)]:
        def replace(s):
            if '## Arguments\n' not in s:return s
            prefix,raw=s.split('## Arguments\n',1);args=json.loads(raw);args['request'][key]=value
            return prefix+'## Arguments\n'+json.dumps(args)
        with pytest.raises(AssertionError,match='request'):
            fx._validate_wire(_map_strings(first,replace),case)
    mutated=_map_strings(last,lambda s:s.replace('"value": 98','"value": 1'))
    assert mutated!=last
    with pytest.raises(AssertionError,match='tool result'):
        fx._validate_wire(mutated,case)


@pytest.mark.parametrize('mode',['worker','critic','handoff'])
def test_direct_human_stop_preserves_correct_role_qualification(tmp_path,mode):
    from prosaic_harness import Harness,FileRunStore
    from lab_runner.handoffs.direct import execute_case,recover_case,materials
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
    from lab_runner.handoffs.direct_scoring import score_direct
    from lab_runner.quality.contracts import digest
    case=example_case('missing');controls=dict(draft=correct_worker(case,'missing')) if mode=='critic' else {}
    with fixture_provider(case,family='missing') as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='stop',mode=mode,**controls)
        assert score_direct(case,e)['qualityPassed']
        workflow,_,_=materials(case,p.config,tmp_path,'stop',mode=mode,**controls)
        store=FileRunStore(tmp_path/'store',namespace='direct-handoffs');store.initialize()
        try:
            h=Harness(workflow,store=store,run_id=digest(dict(sampleId='stop'))[:32]);snapshot=h.status();p.deny=True
            h.resume(choice='stop',expected_revision=snapshot.revision)
        finally:store.close()
        final=recover_case(case,config=p.config,output=tmp_path,sample_id='stop',mode=mode,**controls)
        assert final['receiptDigests']==e['receiptDigests']
    score=score_direct(case,final)
    assert score['qualityPassed'] and score['safe'] and score['outcome']=='stopped'
