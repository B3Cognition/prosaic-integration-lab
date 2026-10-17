import pytest


def test_live_counter_admission_has_no_fallback():
    from lab_runner.quality.token_admission import admit_live_counters
    with pytest.raises(ValueError,match='trusted token counter'):
        admit_live_counters(None,None,['unqualified'])


def test_execution_budget_uses_public_sdk_and_unchanged_case_caps():
    from lab_runner.quality.token_admission import execution_scope
    from prosaic_runtime import TokenCounterRegistration, TokenCounterDescriptor
    class Counter:
        def count_tokens(self,request):return 3
    registration=TokenCounterRegistration(TokenCounterDescriptor(
        identity='synthetic',provider='openai-compatible',model='fixture',framing_revision='openai-chat-v1',
        context_capacity_tokens=8192,implementation_version='1',tokenizer_assets_digest='a'*64,
        template_assets_digest='b'*64,counting_kind='exact',guarantee='Synthetic test units only.'),Counter())
    caps=dict(timeoutSeconds=10,providerRequests=4,toolCalls=2,reportedTokens=8192)
    scope=execution_scope(caps,registration)
    assert scope.token_admission==registration.descriptor.to_dict()
    assert scope.provider_requests==0 and scope.reported_tokens==0 and scope.reserved_tokens==0


@pytest.mark.parametrize('count,expected_requests,breach',[(100,2,None),(0,1,'token_reservation_exceeded')])
def test_installed_sdk_admission_spans_actual_harness_memory_execution(tmp_path,count,expected_requests,breach):
    from dataclasses import replace
    from memory_helpers import development
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case
    from prosaic_runtime import TokenCounterDescriptor,TokenCounterRegistration
    class Counter:
        def count_tokens(self,request):return count
    case,corpus,_,_=development()
    counter=TokenCounterRegistration(TokenCounterDescriptor(identity='synthetic',provider='openai-compatible',
        model='memory-fixture-a',framing_revision='openai-chat-v1',context_capacity_tokens=8192,
        implementation_version='1',tokenizer_assets_digest='a'*64,template_assets_digest='b'*64,
        counting_kind='exact',guarantee='Synthetic fixture input units only.'),Counter())
    with fixture_provider([case]) as provider:
        # Deliberately narrow the synthetic output bound to expose a provider
        # breach below the unchanged 8192-token per-case ceiling.
        config=replace(provider.config,profiles={k:replace(v,max_tokens=100) for k,v in provider.config.profiles.items()})
        result=execute_case(case,corpus=corpus,arm='enabled',config=config,profile='fixture-a',
                            output=tmp_path,sample_id='strict-fixture',token_counter=counter)
        assert provider.requests==expected_requests
    assert result['admissionViolation']==breach
    assert result['counts']['reportedTokens']==150*expected_requests


def test_counter_provenance_supports_receipt_only_recovery_without_code(tmp_path):
    from lab_runner.quality.token_admission import counter_identity,admit_live_counters
    from prosaic_runtime import EndpointConfig,RuntimeConfig,TokenCounterDescriptor,TokenCounterRegistration
    class Counter:
        def count_tokens(self,request):return 100
    config=RuntimeConfig({'fixture':EndpointConfig('http://127.0.0.1:1','fixture',max_tokens=100)}, {},'fixture')
    counter=TokenCounterRegistration(TokenCounterDescriptor(identity='synthetic',provider='openai-compatible',model='fixture',
        framing_revision='openai-chat-v1',context_capacity_tokens=8192,implementation_version='1',
        tokenizer_assets_digest='a'*64,template_assets_digest='b'*64,counting_kind='exact',
        guarantee='Synthetic fixture only.'),Counter())
    counters=admit_live_counters({'fixture':counter},config,['fixture'])
    expected=counter_identity(counters,output=tmp_path,config=config,profiles=['fixture'])
    assert counter_identity({},output=tmp_path,config=config,profiles=['fixture'],recover_only=True)==expected
