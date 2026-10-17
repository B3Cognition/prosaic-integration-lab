"""A complete two-profile comparison over actual SDK calls and scripted providers."""
from dataclasses import replace


def test_complete_profiles_compare_correct_and_incorrect_trajectories(tmp_path):
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.execution import execute_case,CASE_LIMITS
    from lab_runner.quality.runner import identity,fingerprint,schedule
    from lab_runner.quality.reporting import public_result,summarize,compare
    suite=load_suite();reports=[]
    for index,scenario in enumerate(('correct','wrong')):
        with fixture_provider(scenario=scenario) as provider:
            config=replace(provider.config,profiles={'fixture':replace(
                provider.config.profiles['fixture'],model='quality-'+scenario)})
            fp=fingerprint(config.profiles['fixture']);rows=schedule(suite,[fp],1);results=[]
            for case,row in zip(suite['cases'],rows):
                evidence=execute_case(case,config=config,profile='fixture',output=tmp_path/('p'+str(index)),
                    sample_id=row['sampleId'],limits=CASE_LIMITS)
                results.append(public_result(case,evidence,profile_fingerprint=fp,repetition=1))
            assert provider.requests==sum(r['counts']['providerRequests'] for r in results)
        report=summarize(rows,results,identity=identity(suite,CASE_LIMITS),origin='fixture',recovery=[])
        assert report['baselineComplete']
        reports.append(report)
    comparison=compare(reports)
    assert comparison['baselineComplete'] and comparison['origin']=='fixture'
    assert comparison['groups'][0]['taskSuccess']['rate']==1
    assert comparison['groups'][1]['taskSuccess']['rate']==0
