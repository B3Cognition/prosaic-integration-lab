"""Run with -I in an isolated installed-wheel environment; no live model calls."""
import argparse
from pathlib import Path
import socket
import sys
import tempfile


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-root',required=True);args=p.parse_args()
    import lab_runner.memory as memory
    from lab_runner.memory.runner import preflight,execute
    from lab_runner.memory.suite import load_suite
    owner=Path(memory.__file__).resolve();root=Path(args.source_root).resolve()
    assert not owner.is_relative_to(root) and owner.is_relative_to(Path(sys.prefix).resolve())
    suite=load_suite();assert len(suite['cases'])==12
    original=socket.socket
    def forbidden(*a,**k):raise AssertionError('socket in memory preflight')
    socket.socket=forbidden
    try:
        report=preflight();assert report['executedSamples']==0 and report['scheduledSamples']==48
    finally:socket.socket=original
    subset={**suite,'cases':suite['cases'][:2]}
    with tempfile.TemporaryDirectory(prefix='memory-installed-smoke-') as output:
        report=execute(output=Path(output).resolve(),bundle=subset,fixture=True)
        assert report['baselineComplete'] and report['taskSuccess']['passed']==8
        assert report['providerRequests']==report['fixtureCounts']['providerRequests']==16
        assert report['toolCalls']==report['fixtureCounts']['toolCalls']==8
    print('retrieval-memory installed smoke passed: frozen12case suite, pure preflight,8native fixture samples')


if __name__=='__main__':main()
