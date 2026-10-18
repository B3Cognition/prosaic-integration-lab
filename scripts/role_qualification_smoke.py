"""Installed consumer blueprint qualification; scripted transport only."""
import argparse
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--evidence-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from lab_runner import role_qualification as q
    from lab_runner.handoffs.direct import execute_case
    from lab_runner.handoffs.direct_fixture import fixture_provider,example_case,correct_worker
    from lab_runner.handoffs.direct_contracts import output_schemas
    from lab_runner.handoffs.diagnostics import diagnose_direct
    from lab_runner.quality.contracts import digest
    from lab_runner.quality.allowance import private_directory,private_write
    assert not Path(q.__file__).resolve().is_relative_to(args.source_root.resolve())
    root=private_directory(args.evidence_dir);samples=[];all_reports=[]
    for provider in ('openai','anthropic'):
        observations={r:[] for r in ('worker','critic')}
        bindings={role:q.qualification_binding(role=role,schema=output_schemas()[role],
            profile_fingerprint=digest(dict(provider=provider,model='synthetic-only',outputTokens=512)),
            adapter_revision='direct-v2',evaluator_revision='rollout-diagnostics-v1',
            evidence_revision='scoped-host-records-v1',suite_revision='synthetic-roles-v1')
            for role in observations}
        for family in ('correct','reject','missing','conflict','unread','extra_unread'):
            case=example_case(family)
            for role in ('worker','critic'):
                sample=provider+'-'+family+'-'+role;out=private_directory(root/sample)
                ids=['metrics'] if family=='unread' else ['metrics','incident'] if family=='extra_unread' else None
                controls=dict(draft=correct_worker(case,family),record_ids=ids) if role=='critic' else {}
                with fixture_provider(case,provider=provider,family=family) as p:
                    evidence=execute_case(case,config=p.config,output=out,sample_id=sample,mode=role,**controls)
                    before=digest(evidence);requests=p.requests;p.deny=True
                    diagnosis=diagnose_direct(case,evidence)
                    assert digest(evidence)==before and p.requests==requests and not p.errors
                assessment=diagnosis['roles'][role];assert assessment['status']=='passed',(sample,assessment)
                assert evidence['counts']['providerRequests']<=4 and evidence['counts']['toolCalls']<=2
                assert evidence['counts']['reportedTokens']<=8192
                private_write(out/'evidence.json',evidence);private_write(out/'diagnostics.json',diagnosis)
                observations[role].append(dict(caseId=sample,scenario=family,bindingDigest=digest(bindings[role]),
                    evidenceDigest=digest(evidence),assessment=assessment))
                samples.append(dict(sample=sample,provider=provider,role=role,status=assessment['status'],counts=evidence['counts']))
        for role,rows in observations.items():
            report=q.qualification_report(bindings[role],rows,required_scenarios=[r['scenario'] for r in rows],origin='synthetic')
            assert report['qualified'] and not report['liveEligible']
            try:q.require_qualification(report,expected_binding=bindings[role],trusted_digest=digest(report),required_scenarios=report['requiredScenarios'])
            except ValueError:pass
            else:raise AssertionError('synthetic evidence admitted live use')
            private_write(root/(provider+'-'+role+'-qualification.json'),report);all_reports.append(digest(report))
    # Another consumer domain uses the same primitives without the rollout adapter.
    schema=dict(type='object',properties={'dispatch':{'enum':['hold','send']}},required=['dispatch'],additionalProperties=False)
    result=q.assess_output('{"dispatch":"send"}',schema,
        checks=[q.FieldCheck('/dispatch','hold',evidence_refs=('manifest:missing',))])
    assert result['status']=='failed' and result['diagnostics'][0]['evidenceRefs']==['manifest:missing']
    private_write(args.output,dict(origin='synthetic',liveRequests=0,samples=samples,qualificationDigests=all_reports,
        secondDomain=result,limits=q.LIMITS))
    print('Installed role blueprint:24both-wire lanes,4synthetic qualifications; live use rejected; zero live requests.')


if __name__=='__main__':main()
