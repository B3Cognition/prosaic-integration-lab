"""Real installed Runtime/Harness, synthetic loopback responses, no inference."""
import copy
import importlib
import json
from dataclasses import replace
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_completeness_profile import Provider, fixture
from test_memory_span_audit_contracts import sample, ref
from lab_runner.memory_benchmark import span_audit_contracts as contracts
from lab_runner.memory_benchmark.completeness_profile import freeze_packet
from lab_runner.memory_benchmark import completeness_profile as baseline
from lab_runner.requirements_review_v1.contracts import CRITIC_SCHEMA

try:
    workflow = importlib.import_module('lab_runner.memory_benchmark.span_audit_workflow')
except ModuleNotFoundError:
    workflow = None


def test_audit_workflow_is_available():
    assert workflow is not None, 'native answer-span workflow is not implemented'


def test_source_stage_is_draft_hidden_and_completed_resume_has_zero_calls(tmp_path):
    assert workflow is not None
    packet, ledger, audit = sample.__wrapped__()
    before = copy.deepcopy(CRITIC_SCHEMA)
    with Provider([ledger, audit]) as provider:
        result = workflow.run_audit(provider.config, packet, tmp_path/'audit')
        assert result['status'] == 'completed', result
        assert result['outcome'] == 'findings'
        assert result['original'] == packet.to_dict()['draft']
        assert result['audit'] == audit
        assert result['retainedTokens'] == 0
        assert result['usage']['providerRequests'] == 2
        assert 'The fixture works.' not in provider.requests[0]['messages'][0]['content']
        assert 'The fixture works.' in provider.requests[1]['messages'][0]['content']
        for request in provider.requests:
            assert 'tools' not in request
            assert request['max_tokens'] <= 4096
            assert request['response_format']['type'] == 'json_schema'
        checkpoint = result['evidence']['checkpoint']
        assert checkpoint['bindings']['answer-audit']['dependencies'] == {'source-obligations': checkpoint['bindings']['source-obligations']}
        before_files = {p.name: p.read_bytes() for p in (tmp_path/'audit').glob('allowance-*.json')}
        again = workflow.run_audit(provider.config, packet, tmp_path/'audit')
        assert again['audit'] == audit
        assert again['usage']['providerRequests'] == 0
        assert len(provider.requests) == 2
        assert before_files == {p.name: p.read_bytes() for p in (tmp_path/'audit').glob('allowance-*.json')}
    assert CRITIC_SCHEMA == before


def test_unknown_usage_holds_full_reservation_and_never_redispatches(tmp_path):
    assert workflow is not None
    packet, ledger, audit = sample.__wrapped__()
    with Provider([ledger, audit], missing_usage=True) as provider:
        result = workflow.run_audit(provider.config, packet, tmp_path/'unknown')
        assert result['audit'] is None
        assert result['status'] == 'blocked'
        assert result['retainedTokens'] == 65536
        assert result['usage']['usageComplete'] is False
        held = (tmp_path/'unknown'/'allowance-final.json').read_bytes()
        assert len(provider.requests) == 1
        again = workflow.run_audit(provider.config, packet, tmp_path/'unknown')
        assert again['retainedTokens'] == 65536
        assert again['usage']['usageComplete'] is False
        assert len(provider.requests) == 1
        assert held == (tmp_path/'unknown'/'allowance-final.json').read_bytes()


def test_rejected_proof_retains_raw_failure_original_and_no_retry(tmp_path):
    assert workflow is not None
    packet, ledger, audit = sample.__wrapped__()
    audit['obligations'][0].update(verdict='covered', answerSpans=[])
    with Provider([ledger, audit]) as provider:
        result = workflow.run_audit(provider.config, packet, tmp_path/'invalid')
        assert result['audit'] is None
        assert result['failedStage'] == 'answer-audit'
        assert result['original'] == packet.to_dict()['draft']
        assert result['evidence']['receipts'][-1]['result']['stdout'] == json.dumps(audit, ensure_ascii=False)
        workflow.run_audit(provider.config, packet, tmp_path/'invalid')
        assert len(provider.requests) == 2


def test_changed_packet_or_endpoint_rejects_resume_without_dispatch(tmp_path):
    assert workflow is not None
    packet, ledger, audit = sample.__wrapped__()
    with Provider([ledger, audit]) as provider:
        workflow.run_audit(provider.config, packet, tmp_path/'bound')
        q, draft, frames, identity = fixture()
        draft['claims'][0]['text'] = 'A changed original answer.'
        other = contracts.freeze_audit(freeze_packet(q, draft, frames, identity=identity))
        with pytest.raises(ValueError): workflow.run_audit(provider.config, other, tmp_path/'bound')
        with Provider([ledger, audit]) as different:
            with pytest.raises(ValueError): workflow.run_audit(different.config, packet, tmp_path/'bound')
            assert different.requests == []
        assert len(provider.requests) == 2


def test_unrecognized_partial_directory_cannot_replace_an_execution(tmp_path):
    assert workflow is not None
    packet, ledger, audit = sample.__wrapped__()
    path = tmp_path/'partial';path.mkdir();(path/'unknown-evidence').write_text('preserve')
    with Provider([ledger, audit]) as provider:
        with pytest.raises(ValueError): workflow.run_audit(provider.config, packet, path)
        assert provider.requests == []
        assert (path/'unknown-evidence').read_text() == 'preserve'


def test_unknown_allowance_cannot_be_forged_into_settlement(tmp_path):
    packet, ledger, audit = sample.__wrapped__()
    with Provider([ledger],missing_usage=True) as provider:
        workflow.run_audit(provider.config,packet,tmp_path/'held')
        path=tmp_path/'held'/'allowance-final.json'
        final=json.loads(path.read_text())
        final.update(state='reported',retainedTokens=0,reportedTokens=0,usageComplete=True)
        final.pop('sha256');final['sha256']=baseline._sha(final);path.write_text(json.dumps(final))
        with pytest.raises(ValueError): workflow.run_audit(provider.config,packet,tmp_path/'held')
        assert len(provider.requests)==1


def test_changed_serving_features_invalidate_resume(tmp_path):
    packet, ledger, audit = sample.__wrapped__()
    with Provider([ledger,audit]) as provider:
        workflow.run_audit(provider.config,packet,tmp_path/'features')
        config=provider.config
        changed=replace(config,profiles={config.default_profile:replace(config.profiles[config.default_profile],features={'streaming':False})})
        with pytest.raises(ValueError): workflow.run_audit(changed,packet,tmp_path/'features')
        assert len(provider.requests)==2


def test_oversized_stage_output_stops_before_second_call(tmp_path):
    packet, ledger, audit = sample.__wrapped__()
    ledger['questionParts'][0]['reason']='x'*17000
    with Provider([ledger,audit]) as provider:
        result=workflow.run_audit(provider.config,packet,tmp_path/'large')
        assert result['audit'] is None
        assert result['original']==packet.to_dict()['draft']
        assert result['retainedTokens']==65536
        assert result['usage']['reportedTokens']==50
        assert result['usage']['usageComplete'] is False
        assert result['usage']['runtimeUsageComplete'] is True
        assert len(provider.requests)==1
        again=workflow.run_audit(provider.config,packet,tmp_path/'large')
        assert again['retainedTokens']==65536 and again['usage']['providerRequests']==0
        assert len(provider.requests)==1


def test_settled_allowance_cannot_disagree_with_reported_native_tokens(tmp_path):
    packet,ledger,audit=sample.__wrapped__()
    with Provider([ledger,audit]) as provider:
        workflow.run_audit(provider.config,packet,tmp_path/'settled')
        path=tmp_path/'settled'/'allowance-final.json'
        value=json.loads(path.read_text());value['reportedTokens']=999
        value.pop('sha256');value['sha256']=baseline._sha(value);path.write_text(json.dumps(value))
        with pytest.raises(ValueError): workflow.run_audit(provider.config,packet,tmp_path/'settled')
        assert len(provider.requests)==2
