import argparse
from importlib.metadata import version
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='store_true', required=True)
    parser.parse_args()
    print(json.dumps({name: version(name) for name in (
        'prosaic', 'prosaic-runtime', 'prosaic-harness',
        'prosaic-runtime-postgres', 'prosaic-harness-postgres')}))


if __name__ == '__main__':
    main()
