"""List or copy examples; this command performs no model calls."""
import argparse
from . import BLUEPRINTS, copy_blueprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    copy = commands.add_parser('copy')
    copy.add_argument('name', choices=tuple(BLUEPRINTS))
    copy.add_argument('destination')
    args = parser.parse_args()
    if args.command == 'list':
        print('\n'.join(BLUEPRINTS))
    else:
        print(copy_blueprint(args.name, args.destination))


if __name__ == '__main__':
    main()
