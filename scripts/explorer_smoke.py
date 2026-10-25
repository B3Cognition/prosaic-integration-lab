"""Exercise installed Explorer assets and HTTP bootstrap without Node or model calls.

Run with the clean consumer's Python and -I; this helper never adds source paths.
"""
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler


def verify():
    import lab_runner.explore
    installed = Path(lab_runner.explore.__file__).resolve()
    if not installed.is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError('Explorer must come from installed wheel')
    web = installed.parent / 'web'
    if not list((web / 'font-licenses').glob('*.txt')):
        raise ValueError('font licenses missing')
    if not (web / 'third-party-licenses.txt').is_file():
        raise ValueError('bundled JavaScript notices missing')
    opener = build_opener(ProxyHandler({}))
    with tempfile.TemporaryDirectory(prefix='lab-explorer-installed-') as temporary:
        root = Path(temporary).resolve()
        connection = root / 'connection.json'
        with (root / 'server.log').open('wb') as log:
            process = subprocess.Popen([sys.executable, '-I', '-B', '-m', 'lab_runner.explore',
                '--no-open', '--launch-file', str(connection)], cwd=root,
                stdout=log, stderr=log, start_new_session=True)
            try:
                deadline = time.monotonic() + 15
                while not connection.exists():
                    if process.poll() is not None or time.monotonic() > deadline:
                        raise ValueError('installed Explorer did not start')
                    time.sleep(.05)
                parts = urlsplit(json.loads(connection.read_text())['url'])
                origin = parts.scheme + '://' + parts.netloc
                def get(path):
                    for _ in range(100):
                        try:
                            return opener.open(origin + path, timeout=2).read()
                        except HTTPError:
                            raise
                        except OSError:
                            if process.poll() is not None:
                                raise ValueError('installed Explorer exited')
                            time.sleep(.05)
                    raise ValueError('installed Explorer unavailable')
                index = get('/').decode()
                if 'Prosaic Explorer' not in index:
                    raise ValueError('installed index missing')
                resources = re.findall(r'(?:src|href)="(/assets/[^"<>]+)"', index)
                if not resources:
                    raise ValueError('installed bundle missing')
                fonts = set()
                for resource in resources:
                    content = get(resource)
                    if content != (web / resource.lstrip('/')).read_bytes():
                        raise ValueError('served assets differ')
                    if resource.endswith('.css'):
                        fonts.update(re.findall(r'url\((/assets/[^)]+\.woff2?)\)', content.decode()))
                if not fonts:
                    raise ValueError('local fonts missing')
                for resource in sorted(fonts):
                    if get(resource) != (web / resource.lstrip('/')).read_bytes():
                        raise ValueError('served font differs')
                try:
                    get('/api/status')
                except HTTPError as error:
                    if error.code != 401:
                        raise
                else:
                    raise ValueError('status accepted unauthenticated request')
                request = Request(origin + '/api/bootstrap', data=b'{}', method='POST', headers={
                    'Origin': origin, 'Content-Type': 'application/json',
                    'X-Explorer-Launch': parts.fragment.removeprefix('connect=')})
                token = json.loads(opener.open(request, timeout=2).read())['token']
                status = json.loads(opener.open(Request(origin + '/api/status',
                    headers={'Authorization': 'Bearer ' + token}), timeout=2).read())
                if status['liveEnabled'] is not False or status['runs'] != []:
                    raise ValueError('default launcher gained live authority')
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
    return {'passed': True, 'installedExplorer': True, 'bundledResources': len(resources),
            'localFonts': len(fonts), 'liveInvocations': 0, 'cleanup': 'verified'}


if __name__ == '__main__':
    print(json.dumps(verify(), sort_keys=True))
