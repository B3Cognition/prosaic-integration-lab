"""Offline installed-candidate qualification; synthetic providers only.

Run with isolated Python after installing the exact checksummed candidate wheels.
This is not real tokenizer, provider, database or platform certification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import socket
from unittest.mock import patch


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(mode=0o700,parents=True,exist_ok=False)
    import prosaic_runtime as runtime
    import lab_runner.memory.runner as memory
    import lab_runner.quality.runner as quality
    from lab_runner.quality.allowance import BenchmarkAllowance
    for module in (runtime,memory,quality):
        assert 'site-packages' in Path(module.__file__).resolve().parts
    assert 'token_admission_v1' in runtime.ProsaicRuntime.capabilities
    reports={}
    for format in ('raw','typed'):
        target=out/format
        report=memory.execute(output=target,fixture=True,evidence_format=format,
            fixture_scenario='public_summary' if format=='typed' else 'correct')
        assert report['baselineComplete'] and report['taskSuccess']['passed']==report['scheduledSamples']
        before={p:p.read_bytes() for p in target.rglob('*') if p.is_file()}
        with patch.object(socket,'socket',side_effect=AssertionError('network during replay')):
            assert memory.execute(output=target,fixture=True,evidence_format=format,recover_only=True)==report
        assert before=={p:p.read_bytes() for p in target.rglob('*') if p.is_file()}
        reports[format]={k:report[k] for k in ('scheduledSamples','executedSamples','providerRequests','toolCalls','reportedTokens')}
    target=out/'quality';report=quality.execute(output=target)
    assert report['baselineComplete']
    before={p:p.read_bytes() for p in target.rglob('*') if p.is_file()}
    with patch.object(socket,'socket',side_effect=AssertionError('network during replay')):
        assert quality.execute(output=target)==report
    assert before=={p:p.read_bytes() for p in target.rglob('*') if p.is_file()}
    reports['quality']={k:report[k] for k in ('scheduledSamples','executedSamples','providerRequests','toolCalls','reportedTokens')}
    from dataclasses import replace
    from lab_runner.memory.suite import load_suite
    from lab_runner.memory.corpus import Corpus
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case
    bundle=load_suite();case=bundle['cases'][0];corpus=Corpus(bundle['corpus'],bundle['historicalSources'])
    for count,expected_requests,violation in ((100,2,None),(0,1,'token_reservation_exceeded')):
        class Counter:
            def count_tokens(self,request):return count
        counter=runtime.TokenCounterRegistration(runtime.TokenCounterDescriptor(identity='synthetic',
            provider='openai-compatible',model='memory-fixture-a',framing_revision='openai-chat-v1',
            context_capacity_tokens=8192,implementation_version='1',tokenizer_assets_digest='a'*64,
            template_assets_digest='b'*64,counting_kind='exact',guarantee='Synthetic fixture units only.'),Counter())
        with fixture_provider([case]) as provider:
            config=replace(provider.config,profiles={k:replace(v,max_tokens=100) for k,v in provider.config.profiles.items()})
            evidence=execute_case(case,corpus=corpus,arm='enabled',config=config,profile='fixture-a',
                output=out/('strict-'+str(count)),sample_id='strict-synthetic',token_counter=counter)
            assert provider.requests==expected_requests and evidence['admissionViolation']==violation
            assert evidence['counts']['reportedTokens']==150*expected_requests
    # Known historical incident reproduced through the installed ledger API.
    limits=dict(providerRequests=4,toolCalls=2,reportedTokens=8192,maxSamples=2,timeoutSeconds=60)
    ledger=BenchmarkAllowance(out/'overrun'/'allowance.json',identity='a'*64,limits=limits,version=2)
    maximum={k:limits[k] for k in ('providerRequests','toolCalls','reportedTokens')}
    ledger.reserve('sample',maximum)
    actual=maximum|{'reportedTokens':8516}
    ledger.finish('sample',actual=actual,evidence_digest=hashlib.sha256(b'synthetic evidence').hexdigest())
    reopened=BenchmarkAllowance(ledger.path,identity='a'*64,limits=limits,version=2)
    assert reopened.status()['retained']==actual and reopened.status()['excess']['reportedTokens']==324
    try:reopened.reserve('forbidden',dict(providerRequests=0,toolCalls=0,reportedTokens=0))
    except ValueError:pass
    else:raise AssertionError('overrun admitted another sample')
    result=dict(version=1,origin='offline-fixture',runtimeVersion=runtime.__version__,reports=reports,
        byteIdenticalNetworkDeniedReplay=True,strictHarnessCases=2,knownOverrun=dict(reserved=8192,actual=8516,excess=324),
        liveRequests=0,tokenizerQualified=False,databaseQualified=False)
    (out/'qualification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
