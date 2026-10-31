"""Reference transport through real public Runtime/Harness and loopback HTTP."""
import copy
import importlib
import json
from dataclasses import replace
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_completeness_profile import Provider
from test_memory_span_audit_refs import packet,ledger_wire,audit_wire
from lab_runner.answer_span_refs import contracts


def api():
    assert (Path(__file__).parents[2]/'lab_runner/answer_span_refs/workflow.py').is_file(),'native resolved audit workflow missing'
    return importlib.import_module('lab_runner.answer_span_refs.workflow')


@pytest.mark.parametrize('case',['omitted','complete','unavailable'])
def test_real_wire_calls_resolve_without_changing_native_evidence(case,tmp_path):
    workflow=api();p=packet(case);absent=case=='unavailable';complete=case=='complete'
    source=ledger_wire(contracts,p,absent);ledger=contracts.resolve_ledger(source,p)
    audit=audit_wire(contracts,p,ledger,complete,absent)
    with Provider([source,audit]) as provider:
        result=workflow.run_audit(provider.config,p,tmp_path/'run')
        assert result['status']=='completed' and result['outcome']==('findings' if case=='omitted' else 'clear'),result
        assert result['original']==contracts.canonical_packet(p).to_dict()['draft']
        assert result['audit']==contracts.resolve_audit(audit,p,ledger)
        assert result['usage']['providerRequests']==2 and result['usage']['reportedTokens']==100
        assert result['retainedTokens']==0
        assert provider.requests[0]['response_format']['json_schema']['schema']==contracts.ledger_schema(p)
        assert provider.requests[1]['response_format']['json_schema']['schema']==contracts.audit_schema(p,ledger)
        if case=='omitted':assert 'Memory exists.' not in provider.requests[0]['messages'][0]['content']
        assert 'sha256' not in provider.requests[0]['messages'][0]['content']
        assert all(not r.get('tools') and r['max_tokens']==4096 for r in provider.requests)
        state=result['evidence']['checkpoint']
        assert state['outputs']['source-obligations']['canonical']==ledger
        native=json.loads((tmp_path/'run/transport/source-obligations.json').read_text())
        assert native['elapsedSeconds']>=0
        assert json.loads(native['result']['stdout'])==source
        assert 'questionRefs' in native['result']['stdout'] and 'questionSpans' not in native['result']['stdout']
        receipt=result['evidence']['receipts'][0]['result']
        assert json.loads(receipt['stdout'])['canonical']==ledger
        assert receipt['metadata']['invocation_budgets_v1']['reported_tokens']==native['result']['token_usage']==50
        before={f.relative_to(tmp_path/'run').as_posix():f.read_bytes() for f in (tmp_path/'run').rglob('*.json')}
        again=workflow.run_audit(provider.config,p,tmp_path/'run')
        assert again['usage']['providerRequests']==0 and again['audit']==result['audit'] and len(provider.requests)==2
        assert before=={f.relative_to(tmp_path/'run').as_posix():f.read_bytes() for f in (tmp_path/'run').rglob('*.json')}


def test_native_unknown_retains_reservation_and_never_redispatches(tmp_path):
    workflow=api();p=packet();source=ledger_wire(contracts,p)
    with Provider([source],missing_usage=True) as provider:
        result=workflow.run_audit(provider.config,p,tmp_path/'unknown')
        assert result['audit'] is None and result['retainedTokens']==65536 and not result['usage']['usageComplete']
        raw=(tmp_path/'unknown/transport/source-obligations.json').read_bytes()
        held=(tmp_path/'unknown/allowance-final.json').read_bytes()
        again=workflow.run_audit(provider.config,p,tmp_path/'unknown')
        assert again['retainedTokens']==65536 and len(provider.requests)==1
        assert raw==(tmp_path/'unknown/transport/source-obligations.json').read_bytes()
        assert held==(tmp_path/'unknown/allowance-final.json').read_bytes()


@pytest.mark.parametrize('value',['canonical-bypass','forged-ref','oversize-wire'])
def test_invalid_wire_is_preserved_and_cannot_become_success(value,tmp_path):
    workflow=api();p=packet();source=ledger_wire(contracts,p)
    if value=='canonical-bypass':source=contracts.resolve_ledger(source,p)
    if value=='forged-ref':source['obligations'][0]['sourceRefs']=['forged']
    if value=='oversize-wire':source['unresolved']=['x'*17000]
    with Provider([source]) as provider:
        result=workflow.run_audit(provider.config,p,tmp_path/'invalid')
        assert result['audit'] is None and result['failedStage']=='source-obligations'
        raw=json.loads((tmp_path/'invalid/transport/source-obligations.json').read_text())
        assert json.loads(raw['result']['stdout'])==source
        workflow.run_audit(provider.config,p,tmp_path/'invalid')
        assert len(provider.requests)==1


@pytest.mark.parametrize('mutation',['raw','raw-type','envelope','endpoint-feature','packet'])
def test_tampered_binding_refuses_resume_before_dispatch(mutation,tmp_path):
    workflow=api();p=packet();source=ledger_wire(contracts,p);ledger=contracts.resolve_ledger(source,p)
    audit=audit_wire(contracts,p,ledger)
    with Provider([source,audit]) as provider:
        workflow.run_audit(provider.config,p,tmp_path/'bound')
        config=provider.config
        if mutation in ('raw','raw-type'):
            path=tmp_path/'bound/transport/source-obligations.json';value=json.loads(path.read_text())
            value['result']['stdout']=(value['result']['stdout'].replace('Displayed','Changed') if mutation=='raw' else 7)
            path.write_text(json.dumps(value))
        if mutation=='envelope':
            path=tmp_path/'bound/run.json';value=json.loads(path.read_text())
            value['outputs']['source-obligations']['transport']['recordSha256']='0'*64;path.write_text(json.dumps(value))
        if mutation=='endpoint-feature':
            config=replace(config,profiles={'fixture':replace(config.profiles['fixture'],features={'streaming':True})})
        if mutation=='packet':p=packet('complete')
        with pytest.raises(ValueError):workflow.run_audit(config,p,tmp_path/'bound')
        assert len(provider.requests)==2


def test_unknown_capture_seal_refuses_mutation_without_releasing_hold(tmp_path):
    workflow=api();p=packet();source=ledger_wire(contracts,p)
    with Provider([source],missing_usage=True) as provider:
        workflow.run_audit(provider.config,p,tmp_path/'unknown')
        held=(tmp_path/'unknown/allowance-final.json').read_bytes()
        path=tmp_path/'unknown/transport/source-obligations.json';value=json.loads(path.read_text())
        value['result']['stdout']+=' ';path.write_text(json.dumps(value))
        with pytest.raises(ValueError):workflow.run_audit(provider.config,p,tmp_path/'unknown')
        assert len(provider.requests)==1 and held==(tmp_path/'unknown/allowance-final.json').read_bytes()


def test_second_stage_unknown_preserves_accepted_ledger_and_both_raw_records(tmp_path):
    workflow=api();p=packet();source=ledger_wire(contracts,p);ledger=contracts.resolve_ledger(source,p)
    audit=audit_wire(contracts,p,ledger)
    with Provider([source,audit]) as provider:
        class MissingSecond:
            def __bool__(self):return len(provider.requests)==2
        provider.missing_usage=MissingSecond()
        result=workflow.run_audit(provider.config,p,tmp_path/'second-unknown')
        assert result['retainedTokens']==65536 and result['audit'] is None and result['failedStage']=='answer-audit'
        assert result['usage']['providerRequests']==2 and result['usage']['reportedTokens']==50
        assert result['evidence']['checkpoint']['outputs']['source-obligations']['canonical']==ledger
        assert len(list((tmp_path/'second-unknown/transport').glob('*.json')))==2
        again=workflow.run_audit(provider.config,p,tmp_path/'second-unknown')
        assert again['retainedTokens']==65536 and len(provider.requests)==2


def test_wrong_draft_part_id_cannot_become_an_accepted_native_audit(tmp_path):
    workflow=api();p=packet();source=ledger_wire(contracts,p);ledger=contracts.resolve_ledger(source,p)
    audit=audit_wire(contracts,p,ledger);audit['questionParts']['part']=audit['questionParts'].pop(contracts.PART_IDS[0])
    with Provider([source,audit]) as provider:
        result=workflow.run_audit(provider.config,p,tmp_path/'wrong-id')
        assert result['audit'] is None and result['failedStage']=='answer-audit' and result['retainedTokens']==0
        assert result['usage']['usageComplete'] and result['usage']['reportedTokens']==100
        raw=json.loads((tmp_path/'wrong-id/transport/answer-audit.json').read_text())
        assert json.loads(raw['result']['stdout'])==audit
        workflow.run_audit(provider.config,p,tmp_path/'wrong-id')
        assert len(provider.requests)==2


@pytest.mark.parametrize('failure',['deadline','cancelled'])
def test_terminal_adapter_capture_can_be_inspected_without_acceptance_or_dispatch(failure,tmp_path):
    from copy import deepcopy
    workflow=api();p=packet();source=ledger_wire(contracts,p);ledger=contracts.resolve_ledger(source,p)
    with Provider([source,audit_wire(contracts,p,ledger)]) as provider:
        result=workflow.run_audit(provider.config,p,tmp_path/'terminal')
        evidence=deepcopy(result['evidence'])
        # Public adapter terminal receipts can replace callback metadata after
        # a successful native capture. Model them without patching SDK engines.
        evidence['checkpoint']['outputs']={}
        evidence['checkpoint']['status']='blocked'
        evidence['receipts']=evidence['receipts'][:1]
        receipt=evidence['receipts'][0]['result']
        receipt['metadata'].pop(workflow.META)
        receipt.update(exit_code=1,stdout='',timed_out=failure=='deadline')
        receipt['metadata'].pop('failure_reason',None)
        if failure=='cancelled':receipt['metadata']['failure_reason']='cancelled'
        request=workflow._request(provider.config,p)
        raw=(tmp_path/'terminal/transport/source-obligations.json').read_bytes()
        workflow._verify_trace(evidence,p,request,tmp_path/'terminal')
        assert evidence['checkpoint']['outputs']=={} and len(provider.requests)==2
        assert raw==(tmp_path/'terminal/transport/source-obligations.json').read_bytes()
        # Neither a successful receipt nor an unrecognized failure may use
        # the terminal-inspection exception to bypass its native binding.
        receipt.update(exit_code=0,timed_out=False)
        with pytest.raises(ValueError):workflow._verify_trace(evidence,p,request,tmp_path/'terminal')
        receipt.update(exit_code=1)
        receipt['metadata']['failure_reason']='unrecognized'
        with pytest.raises(ValueError):workflow._verify_trace(evidence,p,request,tmp_path/'terminal')


@pytest.mark.parametrize('case',['omitted','complete','unavailable','unknown-usage'])
def test_explicit_resolved_fixture_cli_case(case,tmp_path):
    assert (Path(__file__).parents[2]/'lab_runner/answer_span_refs/fixture.py').is_file(),'resolved fixture is missing'
    fixture=importlib.import_module('lab_runner.answer_span_refs.fixture')
    value=fixture.run_fixture(tmp_path/case,case=case)
    assert value['originalUnchanged'] and value['resumeProviderRequests']==0 and value['realModelCalls']==0
    assert value['memoryDefault'] is False and value['sueDefault'] is False
    assert value['outcome']==('findings' if case=='omitted' else 'unresolved' if case=='unknown-usage' else 'clear')
    assert value['retainedTokens']==(65536 if case=='unknown-usage' else 0)
    assert value['rawNativeRecords']==(1 if case=='unknown-usage' else 2)
