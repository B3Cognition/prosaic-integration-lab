"""Launch Prosaic Explorer locally; real inference requires explicit host grants."""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import stat
import sys
import tempfile

_root = Path(__file__).resolve().parents[2]
if (_root / 'src' / 'prosaic_integration_lab').is_dir():
    sys.path.insert(0, str(_root / 'src'))


def write_launch(path, url):
    path = Path(path)
    parent = path.parent
    info = parent.stat()
    if parent.is_symlink() or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('private launch-file parent required')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(json.dumps({'url': url}) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='enable reviewed single-task real execution')
    parser.add_argument('--config', type=Path, help='private unified Runtime config; only read by host')
    parser.add_argument('--manifest', type=Path, help='checksummed released SDK manifest')
    parser.add_argument('--wheel-dir', type=Path, help='verified SDK wheel directory')
    parser.add_argument('--evidence-root', type=Path, help='existing private owned directory; retained across restarts')
    parser.add_argument('--max-units', type=int, default=20, help='durable mixed-unit ceiling; not tokens or currency')
    parser.add_argument('--port', type=int, default=0, help='loopback port; zero selects a free port')
    parser.add_argument('--no-open', action='store_true', help='write a private launch link without opening a browser')
    parser.add_argument('--launch-file', type=Path, help='new file in a private directory; never overwritten')
    offline = parser.add_mutually_exclusive_group()
    offline.add_argument('--inspect', action='store_true', help='inspect retained receipt while launcher is stopped')
    offline.add_argument('--acknowledge', action='store_true', help='record offline uncertain-effect acknowledgment, never replay')
    parser.add_argument('--run-id')
    parser.add_argument('--receipt-sha256')
    parser.add_argument('--note-file', type=Path, help='private operator acknowledgment note, at most2048bytes')
    args = parser.parse_args(argv)
    if not 1 <= args.max_units <= 256 or not 0 <= args.port <= 65535:
        parser.error('units or port outside supported range')
    is_offline = args.inspect or args.acknowledge
    if is_offline:
        if (args.live or not args.evidence_root or not args.run_id or
                any(x is not None for x in (args.config, args.manifest, args.wheel_dir, args.launch_file))):
            parser.error('offline inspection requires only evidence root and run identity')
        if args.acknowledge and (not args.receipt_sha256 or not args.note_file):
            parser.error('acknowledgment requires exact receipt digest and private note file')
    elif any(x is not None for x in (args.run_id, args.receipt_sha256, args.note_file)):
        parser.error('receipt arguments apply only to offline inspection/acknowledgment')
    elif args.live:
        if any(x is None for x in (args.config, args.manifest, args.wheel_dir, args.evidence_root)):
            parser.error('live mode requires config, manifest, wheel directory and private evidence root')
    elif any(x is not None for x in (args.config, args.manifest, args.wheel_dir, args.evidence_root)):
        parser.error('execution configuration requires explicit --live')

    coordinator = None
    try:
        if is_offline:
            from .execution import inspect_receipt, reconcile
            if args.inspect:
                result = inspect_receipt(args.evidence_root, args.run_id)
            else:
                fd = os.open(args.note_file, os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(fd, 'rb') as stream:
                    info = os.fstat(stream.fileno())
                    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                            info.st_mode & 0o077 or info.st_size > 2048):
                        raise ValueError('private note required')
                    note = stream.read(2049).decode('utf-8')
                result = reconcile(args.evidence_root, args.run_id, args.receipt_sha256, note)
            print(json.dumps(result, allow_nan=False))
            return 0
        if args.live:
            from .execution import Coordinator
            coordinator = Coordinator(args.evidence_root, args.config, manifest=args.manifest,
                                      wheel_dir=args.wheel_dir, max_units=args.max_units)
        import uvicorn
        from .app import create_app
        with tempfile.TemporaryDirectory(prefix='prosaic-explorer-launch-') as temporary:
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', args.port))
                listener.listen(128)
                origin = 'http://127.0.0.1:' + str(listener.getsockname()[1])
                code = secrets.token_urlsafe(32)
                token = secrets.token_urlsafe(32)
                url = origin + '/#connect=' + code
                launch_file = args.launch_file or Path(temporary).resolve() / 'connection.json'
                write_launch(launch_file, url)
                app = create_app(origin=origin, token=token, launch_code=code, coordinator=coordinator)
                print('Prosaic Explorer: ' + origin, flush=True)
                print('Private connection file: ' + str(launch_file), flush=True)
                print('Live execution enabled; each Run needs review.' if args.live else
                      'Documentation and simulation only; no model execution enabled.', flush=True)
                if not args.no_open:
                    import threading
                    import webbrowser
                    threading.Timer(1, webbrowser.open, args=(url,)).start()
                server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', access_log=False,
                                                     log_level='critical', proxy_headers=False))
                server.run(sockets=[listener])
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        print(json.dumps({'error': 'explorer_setup_failed',
                          'hint': 'Check private paths, released SDK audit, port and stopped-launcher requirements.'}),
              file=sys.stderr)
        return 2
    finally:
        if coordinator is not None:
            coordinator.close()


if __name__ == '__main__':
    raise SystemExit(main())
