import argparse
from importlib.metadata import PackageNotFoundError, version
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='store_true', required=True)
    parser.parse_args()
    try:
        version('b3-prosaic')
    except PackageNotFoundError:
        prefix = ''
    else:
        prefix = 'b3-'
    print(json.dumps({prefix + name: version(prefix + name) for name in (
        'prosaic', 'prosaic-runtime', 'prosaic-harness',
        'prosaic-runtime-postgres', 'prosaic-harness-postgres')}))


if __name__ == '__main__':
    main()
