"""Measured public SDK handoffs; counters are synthetic ONLY in these fixtures."""
from dataclasses import replace
import pytest


def counter(provider, *, model='typed-handoff-fixture', count=100):
    from prosaic_runtime import TokenCounterDescriptor,TokenCounterRegistration
    class Count:
        def count_tokens(self,native):return count
    return TokenCounterRegistration(TokenCounterDescriptor(identity='measured-test',provider=provider,
        model=model,framing_revision='anthropic-messages-v1' if provider=='anthropic' else 'openai-chat-v1',
        context_capacity_tokens=32768,implementation_version='test-v1',tokenizer_assets_digest='a'*64,
        template_assets_digest='b'*64,counting_kind='exact',guarantee='Synthetic test units only.'),Count())


@pytest.mark.parametrize('provider',['openai','anthropic'])
def test_measured_handoff_records_all_roles_under_one_shared_budget(tmp_path,provider):
    from lab_runner.handoffs.execution import execute_counted_case,recover_case
    from lab_runner.handoffs.fixture import fixture_provider,example_case
    from lab_runner.quality.contracts import decode
    case=example_case()
    with fixture_provider(case,provider=provider) as p:
        ep=p.config.profiles['fixture']
        result=execute_counted_case(case,config=p.config,output=tmp_path,sample_id='measured',
                                    token_counter=counter(ep.provider))
        assert result['checkpoint']['status']=='completed'
        assert result['counts']==dict(providerRequests=4,toolCalls=1,reportedTokens=600)
        trace=decode((tmp_path/'measured-context-trace.json').read_bytes())
        assert len(trace['intents'])==len(trace['observations'])==len(trace['proposals'])==4
        assert all(o['usage']['total_tokens']==150 for o in trace['observations'].values())
        p.deny=True
        restored=recover_case(case,config=p.config,output=tmp_path,sample_id='measured')
        assert restored['receiptDigests']==result['receiptDigests'] and p.requests==4


@pytest.mark.parametrize('kind',['missing','model','provider'])
def test_counter_binding_is_checked_before_dispatch(tmp_path,kind):
    from lab_runner.handoffs.execution import execute_counted_case
    from lab_runner.handoffs.fixture import fixture_provider,example_case
    with fixture_provider(example_case()) as p:
        reg=None if kind=='missing' else counter('anthropic' if kind=='provider' else 'openai-compatible',
            model='foreign' if kind=='model' else 'typed-handoff-fixture')
        with pytest.raises(ValueError,match='counter'):
            execute_counted_case(example_case(),config=p.config,output=tmp_path,sample_id='mismatch',token_counter=reg)
        assert p.requests==0


def test_shared_token_exhaustion_does_not_reset_at_next_role(tmp_path):
    from lab_runner.handoffs.execution import execute_counted_case
    from lab_runner.handoffs.fixture import fixture_provider,example_case
    with fixture_provider(example_case()) as p:
        reg=counter('openai-compatible',count=7600)
        result=execute_counted_case(example_case(),config=p.config,output=tmp_path,sample_id='shared',token_counter=reg)
        assert p.requests==1
    assert result['checkpoint']['status']=='blocked'
