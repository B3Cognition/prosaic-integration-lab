"""Execute released/candidate test profiles without skips or missing coverage."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = ('test_mb', 'test_memory_benchmark', 'test_memory_span_audit')


def groups(root):
    root = Path(root)
    default = sorted(p.relative_to(root).as_posix() for directory in ('tests/unit', 'tests/functional')
                     for p in (root/directory).rglob('test_*.py'))
    special = {p for p in default if p.startswith('tests/unit/') and Path(p).name.startswith(PREFIXES)}
    extra = {p.relative_to(root).as_posix() for directory in ('tests/memory_benchmark_candidate', 'tests/requirements_review_v5')
             for p in (root/directory).rglob('test_*.py')}
    common = {p for p in ('tests/unit/test_memory_workflow.py', 'tests/unit/test_memory_provider.py') if (root/p).is_file()}
    return dict(all=default, released=sorted(set(default)-special), candidate=sorted(special|extra|common))


def coverage(all_tests, released, candidate):
    for row, profile in ((all_tests,'all'), (released,'released'), (candidate,'candidate')):
        if (row['profile'] != profile or row['exitCode'] != 0 or row['skipped'] != 0
                or not row['nodeIds'] or row['collectedOnly'] != (profile == 'all')):
            raise ValueError('missing, failed, skipped or unexecuted regression profile')
    expected = set(all_tests['nodeIds'])
    union = set(released['nodeIds'])|set(candidate['nodeIds'])
    if not expected <= union:
        raise ValueError('default regression tests missing from executed profiles')
    return dict(covered=True, defaultTests=len(expected), uniqueExecutedTests=len(union),
                releasedTests=len(set(released['nodeIds'])), candidateTests=len(set(candidate['nodeIds'])))


class Evidence:
    def __init__(self):
        self.nodeids = []
        self.executed = set()
        self.skipped = 0

    def pytest_collection_modifyitems(self, items):
        self.nodeids = [item.nodeid for item in items]

    def pytest_collectreport(self, report):
        self.skipped += int(report.skipped)

    def pytest_runtest_logreport(self, report):
        self.skipped += int(report.skipped)
        if report.when == 'call':
            self.executed.add(report.nodeid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--profile', choices=['all','released','candidate'])
    parser.add_argument('--collect-only', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--coverage', nargs=3, type=Path, metavar=('ALL','RELEASED','CANDIDATE'))
    parser.add_argument('pytest_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('new evidence output required')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.coverage:
        result = coverage(*(json.loads(path.read_text()) for path in args.coverage))
        with args.output.open('x') as f: json.dump(result, f, indent=2)
        print(json.dumps(result))
        return 0
    if not args.profile or args.profile == 'all' and not args.collect_only:
        parser.error('all is collection-only; select an execution profile')
    import os
    import pytest
    os.chdir(args.root)
    evidence = Evidence()
    files = groups(args.root)[args.profile]
    if not files:
        parser.error('required test profile is empty')
    options = args.pytest_args
    if options[:1] == ['--']: options = options[1:]
    # Retain pytest's importlib isolation even for tiny external qualification fixtures.
    status = int(pytest.main(['-q','--import-mode=importlib',*(['--collect-only'] if args.collect_only else []),*files,*options], plugins=[evidence]))
    nodeids = evidence.nodeids if args.collect_only else sorted(evidence.executed)
    if not nodeids or evidence.skipped:
        status = status or 1
    result = dict(version=1,profile=args.profile,nodeIds=sorted(nodeids),
        collectedNodeIds=sorted(evidence.nodeids),skipped=evidence.skipped,exitCode=status,collectedOnly=args.collect_only)
    with args.output.open('x') as f: json.dump(result, f, indent=2)
    return status


if __name__ == '__main__':
    sys.exit(main())
