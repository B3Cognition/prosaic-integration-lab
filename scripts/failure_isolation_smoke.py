"""Installed offline containment qualification; synthetic providers only."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from lab_runner import failure_isolation as isolation
    from lab_runner.handoffs import correction as c, correction_fixture as f
    from lab_runner.quality.allowance import private_directory, private_write
    from lab_runner.quality.contracts import digest
    assert not Path(isolation.__file__).resolve().is_relative_to(args.source_root.resolve()), 'installed package required'
    root = private_directory(args.evidence_dir)
    assert not any(root.iterdir()), 'fresh evidence directory required'
    denied = [False]
    def guard(event, arguments):
        if denied[0] and event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo'):
            raise AssertionError('recovery attempted network access')
    sys.addaudithook(guard)
    limits = dict(providerRequests=8, toolCalls=4, reportedTokens=16384)
    rows = []
    for provider in ('openai', 'anthropic'):
        for fault in ('missing', 'lost_receipt'):
            lane = private_directory(root / (provider + '-' + fault))
            identity = digest(dict(trustedScope='offline-host', provider=provider, fault=fault))
            j = isolation.FailureIsolation(lane / 'containment.json', identity=identity, limits=limits)
            case = f.example_case('correct')
            binding = digest(case)
            with f.fixture_provider(case, provider=provider, scenario='correct',
                                    usage_fault='missing' if fault == 'missing' else 'complete', usage_stage='worker') as bad:
                token = j.admit('failed', binding=binding)
                j.start('failed', token)
                c.execute_correction(case, config=bad.config, output=lane/'failed', sample_id='failed')
                # Simulated host loss after SDK persistence, before journal completion.
                j = isolation.FailureIsolation(lane/'containment.json', identity=identity, limits=limits)
                j.isolate('failed', binding=binding, decision_digest=digest(dict(action='isolate')))
                with f.fixture_provider(case, provider=provider, scenario='correct') as good:
                    token = j.admit('other', binding=binding)
                    j.start('other', token)
                    evidence = c.execute_correction(case, config=good.config, output=lane/'other', sample_id='other')
                    score = c.score_correction(case, evidence)
                    assert score['taskAccepted'] and good.requests == 2 and not good.errors
                    j.complete('other', token, actual=score['counts'], evidence_digest=digest(evidence))
                    private_write(lane/'other-score.json', score)
                before = bad.requests
                bad.deny = True
                denied[0] = True
                try:
                    saved = c.recover_correction(case, config=bad.config, output=lane/'failed', sample_id='failed')
                    score = c.score_correction(case, saved)
                    actual = score['counts'] if score['accountingComplete'] else None
                    recovery = dict(binding=binding, decision_digest=digest(dict(action='reconcile')),
                        actual=actual, evidence_digest=digest(saved) if actual else None,
                        outcome='failed' if actual else 'unknown')
                    closed = j.recover('failed', **recovery)
                    assert j.recover('failed', **recovery) == closed
                    assert j.status()['retained'] == limits
                    assert j.inspect('other')['state'] == 'completed'
                    assert bad.requests == before and not bad.errors
                    assert (closed['actual'] is None) == (fault == 'missing')
                finally:
                    denied[0] = False
                private_write(lane/'failed-score.json', score)
                rows.append(dict(provider=provider, fault=fault, syntheticRequests=before+2,
                                 recovery=closed, status=j.status(), networkDeniedRecovery=True))
    crashes = []
    for boundary in ('admitted', 'active', 'completed'):
        lane = private_directory(root/('crash-'+boundary))
        code = '''
import os,sys
from lab_runner.failure_isolation import FailureIsolation
j=FailureIsolation(sys.argv[1],identity='a'*64,limits=dict(providerRequests=8,toolCalls=4,reportedTokens=16384))
t=j.admit('crash',binding='b'*64)
if sys.argv[2]!='admitted':j.start('crash',t)
if sys.argv[2]=='completed':j.complete('crash',t,actual=dict(providerRequests=2,toolCalls=1,reportedTokens=300),evidence_digest='d'*64)
os._exit(23)
'''
        result = subprocess.run([sys.executable, '-I', '-c', code, str(lane/'containment.json'), boundary], capture_output=True)
        assert result.returncode == 23, result.stderr.decode()
        j = isolation.FailureIsolation(lane/'containment.json', identity='a'*64, limits=limits)
        assert j.inspect('crash')['state'] == boundary
        assert j.status()['retained'] == dict(providerRequests=4, toolCalls=2, reportedTokens=8192)
        try:
            j.admit('crash', binding='b'*64)
        except ValueError:
            pass
        else:
            raise AssertionError('lost acknowledgement allowed duplicate admission')
        crashes.append(dict(boundary=boundary, exitCode=result.returncode, status=j.status()))
    private_write(args.output, dict(version=1, experimental=True, liveRequests=0,
        syntheticRequests=sum(row['syntheticRequests'] for row in rows), lanes=rows, crashes=crashes))
    print('failure isolation: 4 both-wire lanes, 4 network-denied recoveries, 3 process-loss boundaries; 0 live requests')


if __name__ == '__main__':
    main()
