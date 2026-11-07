"""Explicitly opt-in example; configure a copied blueprint before real model calls."""
import argparse
import json
from pathlib import Path
import runpy

from prosaic_harness import Harness, Workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--request', type=Path, default=Path(__file__).with_name('request.json'))
    args = parser.parse_args()
    if not args.live:
        parser.error('--live explicitly authorizes model calls; no calls were made')
    checks = runpy.run_path(str(Path(__file__).with_name('checks.py')))
    request = json.loads(args.request.read_text())
    checks['_index'](request, 'insights', 'id')  # Owned host input validation before reserving a run.
    harness = Harness(Workflow.load(Path(__file__).with_name('workflow.yml')),
                      args.run_dir, validators=checks['validators']())
    print(json.dumps(harness.run(request), indent=2))


if __name__ == '__main__':
    main()
