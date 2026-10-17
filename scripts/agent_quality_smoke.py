"""Run with an installed wheel's Python -I; no external service or credentials."""
import argparse
from pathlib import Path
import tempfile
from importlib.metadata import distribution


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True)
    args=parser.parse_args()
    import lab_runner.quality.suite as package
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.runner import preflight
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    from lab_runner.quality.scoring import score_case
    installed=Path(distribution('prosaic-integration-lab').locate_file('lab_runner/quality/suite.py')).resolve()
    assert Path(package.__file__).resolve()==installed
    assert not installed.is_relative_to(args.source_root.resolve()/'lab_runner')
    suite=load_suite();assert len(suite['cases'])==10
    report=preflight();assert report['origin']=='unexecuted' and report['executedSamples']==0
    case=suite['cases'][0]
    with tempfile.TemporaryDirectory(prefix='quality-wheel-') as temporary:
        with fixture_provider() as provider:
            evidence=execute_case(case,config=provider.config,profile='fixture',
                output=Path(temporary).resolve(),sample_id='installed-smoke',limits=provider.case_limits)
            assert provider.requests==2 and evidence['counts']['providerRequests']==2
        assert score_case(case,evidence)['state']=='passed'
        evidence['answer']['decision']='reject'
        assert score_case(case,evidence)['state']=='failed'
    print('agent quality installed smoke passed: 10 cases, real fixture dispatch, correct/wrong scoring')


if __name__=='__main__':main()
