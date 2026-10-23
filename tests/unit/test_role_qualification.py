"""Consumer behavior, with a shipping contract unrelated to the rollout example."""
import copy
import json
import pytest
from lab_runner.quality.contracts import digest

SCHEMA=dict(type='object',properties=dict(route=dict(enum=['ground','hold']),
    references=dict(type='array',uniqueItems=True,items=dict(type='string'))),
    required=['route','references'],additionalProperties=False)


def api():
    import importlib.util
    assert importlib.util.find_spec('lab_runner.role_qualification'),'consumer role qualification missing'
    import lab_runner.role_qualification as module
    return module


def binding(**changes):
    data=dict(role='shipping-worker',schema=SCHEMA,profile_fingerprint='a'*64,adapter_revision='adapter-v1',
        evaluator_revision='shipping-policy-v1',evidence_revision='host-manifest-v1',suite_revision='suite-v1')
    return api().qualification_binding(**(data|changes))


def checks():
    h=api()
    return [h.FieldCheck('/route','hold',evidence_refs=('manifest:parcel',)),
        h.FieldCheck('/references',['manifest:parcel'],comparison='set',evidence_refs=('manifest:parcel',))]


def observation(b,scenario='safe-hold',case='parcel-1',**assessment):
    return dict(caseId=case,scenario=scenario,bindingDigest=digest(b),evidenceDigest='b'*64,
        assessment=api().assess_output('{"route":"hold","references":["manifest:parcel"]}',
            SCHEMA,checks=checks(),**assessment))


def test_other_domain_diagnostics_are_grounded_and_do_not_echo_values():
    result=api().assess_output('{"route":"ground","references":[]}',SCHEMA,checks=checks())
    assert result['status']=='failed'
    assert result['diagnostics']==[
        dict(code='field_mismatch',field='/route',evidenceRefs=['manifest:parcel']),
        dict(code='field_mismatch',field='/references',evidenceRefs=['manifest:parcel'])]
    assert 'ground' not in json.dumps(result) and 'hold' not in json.dumps(result)


@pytest.mark.parametrize('kind,code',[('json','invalid_json'),('schema','schema_mismatch'),
    ('exit','unusable_output'),('usage','unknown_usage'),('budget','budget_violation'),('abstain','abstained')])
def test_unusable_or_abstaining_output_does_not_qualify(kind,code):
    h=api();b=binding();kwargs={};text='{"route":"hold","references":["manifest:parcel"]}'
    if kind=='json':text='{"route":"hold","route":"ground"}'
    if kind=='schema':text='{"route":"hold","references":[],"selfQualified":true}'
    if kind=='exit':kwargs['exit_code']=1
    if kind=='usage':kwargs['usage_known']=False
    if kind=='budget':kwargs['budget_violation']=True
    if kind=='abstain':kwargs['abstained']=True
    result=h.assess_output(text,SCHEMA,checks=checks(),**kwargs)
    assert result['status']!='passed' and code in [d['code'] for d in result['diagnostics']]
    obs=observation(b);obs['assessment']=result
    report=h.qualification_report(b,[obs],required_scenarios=['safe-hold'],origin='live')
    assert not report['qualified'] and not report['liveEligible']


def test_schema_references_are_rejected_without_resolving_network():
    with pytest.raises(ValueError,match='inline'):
        api().assess_output('{}',dict(type='object',additionalProperties=False,
            properties={'route':{'$ref':'https://invalid.example/private'}}))


def test_canonical_comparison_does_not_equate_bool_and_number_and_supports_escaped_pointers():
    h=api();schema=dict(type='object',additionalProperties=False,properties={'a/b':dict(type='object')})
    result=h.assess_output('{"a/b":{"x~y":true}}',schema,
        checks=[h.FieldCheck('/a~1b/x~0y',1,evidence_refs=('policy:units',))])
    assert result['status']=='failed' and result['diagnostics'][0]['field']=='/a~1b/x~0y'


def test_complete_synthetic_qualification_is_never_live_eligible():
    h=api();b=binding();report=h.qualification_report(b,[observation(b)],required_scenarios=['safe-hold'],origin='synthetic')
    assert report['qualified'] and not report['liveEligible']
    with pytest.raises(ValueError,match='live'):
        h.require_qualification(report,expected_binding=b,trusted_digest=digest(report),required_scenarios=['safe-hold'])


def test_live_report_requires_host_pinned_integrity_and_complete_scenarios():
    h=api();b=binding();obs=[observation(b),observation(b,'missing-manifest','parcel-2')]
    report=h.qualification_report(b,obs,required_scenarios=['safe-hold','missing-manifest'],origin='live')
    assert report['qualified'] and report['liveEligible']
    assert h.require_qualification(report,expected_binding=b,trusted_digest=digest(report),
        required_scenarios=['missing-manifest','safe-hold']) is None
    with pytest.raises(ValueError):
        h.require_qualification(report,expected_binding=b,trusted_digest='0'*64,required_scenarios=report['requiredScenarios'])
    tampered=copy.deepcopy(report);tampered['observations'][0]['assessment']['status']='failed'
    with pytest.raises(ValueError):
        h.require_qualification(tampered,expected_binding=b,trusted_digest=digest(tampered),required_scenarios=report['requiredScenarios'])
    partial=h.qualification_report(b,obs[:1],required_scenarios=['safe-hold','missing-manifest'],origin='live')
    assert not partial['qualified']
    with pytest.raises(ValueError):
        h.qualification_report(b,[obs[0],obs[0]],required_scenarios=['safe-hold'],origin='live')


@pytest.mark.parametrize('change',['profile_fingerprint','adapter_revision','evaluator_revision','evidence_revision','suite_revision','schema','limits'])
def test_role_contract_configuration_changes_invalidate_existing_qualification(change):
    h=api();b=binding();report=h.qualification_report(b,[observation(b)],required_scenarios=['safe-hold'],origin='live')
    value='c'*64 if change=='profile_fingerprint' else 'changed-v2'
    if change=='schema':value=SCHEMA|dict(description='updated contract')
    if change=='limits':value=b['limits']|dict(outputTokens=256)
    updated=binding(**{change:value})
    with pytest.raises(ValueError):
        h.require_qualification(report,expected_binding=updated,trusted_digest=digest(report),required_scenarios=['safe-hold'])


@pytest.mark.parametrize('bad',[0,True,513])
def test_qualification_never_raises_current_output_limit(bad):
    with pytest.raises(ValueError):binding(limits=dict(providerRequests=4,toolCalls=2,reportedTokens=8192,timeoutSeconds=600,outputTokens=bad))
