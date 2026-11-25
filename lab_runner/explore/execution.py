"""Private durable Explorer admission around the installed public Runtime CLI.

The journal records authority, never a license to replay. Unknown reservations
remain charged even after an operator acknowledges the risk of uncertain effects.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import tempfile
import threading
import time
import uuid

import yaml

from lab_runner.live_allowance import SharedLiveAllowance
from lab_runner.native_eval.provenance import audit_candidate
from lab_runner.native_eval.realistic_cases import CASE_IDS, OUTPUTS, prepare, grade
from lab_runner.native_eval.unified import require_unified
from lab_runner.native_eval.unified_benchmark import cli_command

POLICY = dict(nativeTimeoutSeconds=60, localTimeoutSeconds=180, poolTimeoutSeconds=300,
              maxAttempts=3, maxNativeAttempts=2, maxApiRequests=8, maxToolCalls=7,
              maxToolRounds=8, maxReportedTokens=65536, nativePermissions='workspace-write')
EVENTS = {'profile_selected', 'profile_attempt', 'profile_skipped', 'profile_fallback',
          'profile_started', 'profile_completed', 'profile_failed'}
REASONS = {'capacity_unavailable', 'unavailable', 'quota_exhausted', 'cooling_down',
           'provider_request_limit', 'tool_call_limit', 'timeout', 'execution_failure',
           'tool_effect_uncertain', 'permission_denied', 'unsupported_capability'}
RECEIPT_KEYS = {'runId', 'requestId', 'task', 'state', 'passed', 'durationMs',
                'selectedProfile', 'events', 'output', 'failureReason',
                'recoveryRequired', 'usage', 'startedAt'}
TIMEOUT_REASONS = {'timeout', 'native_timeout', 'api_timeout', 'pool_timeout', 'deadline_exceeded'}


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _private_path(path, directory=False):
    path = Path(path)
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('private storage unavailable')
    info = path.stat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if not kind(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('owned private storage required')
    return info


def _read(path, limit=16_777_216):
    _private_path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        if os.fstat(fd).st_size > limit: raise ValueError('private record limit')
        return os.read(fd, limit + 1)
    finally:
        os.close(fd)


def _write(path, value):
    data = _encoded(value)
    if len(data) > 16_777_216: raise ValueError('private record limit')
    _private_path(path.parent, True)
    if path.exists() or path.is_symlink(): _private_path(path)
    fd, temporary = tempfile.mkstemp(prefix='.explorer-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


class _Store:
    def __init__(self, root):
        self.root = Path(root)
        _private_path(self.root, True)
        self.identity = (self.root.stat().st_dev, self.root.stat().st_ino)
        self.fd = os.open(self.root / 'explorer.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            _private_path(self.root / 'explorer.lock')
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, ValueError):
            os.close(self.fd)
            raise ValueError('root_locked') from None
        self.path = self.root / 'state.json'
        lock = os.fstat(self.fd)
        self.lock_identity = (lock.st_dev, lock.st_ino)

    def check(self):
        info = _private_path(self.root, True)
        if (info.st_dev, info.st_ino) != self.identity:
            raise ValueError('private storage changed')
        lock = _private_path(self.root / 'explorer.lock')
        if (lock.st_dev, lock.st_ino) != self.lock_identity:
            raise ValueError('storage_invalid')

    def read(self):
        self.check()
        if not self.path.exists(): return {'version': 1, 'runs': [], 'acknowledgments': []}
        value = json.loads(_read(self.path))
        if (type(value) is not dict or value.get('version') != 1 or
                type(value.get('runs')) is not list or len(value['runs']) > 64 or
                type(value.get('acknowledgments')) is not list):
            raise ValueError('invalid Explorer journal')
        return value

    def write(self, value):
        self.check(); _write(self.path, value)

    def close(self):
        os.close(self.fd)


def _receipt(row):
    result = {key: deepcopy(value) for key, value in row['receipt'].items() if key in RECEIPT_KEYS}
    result['receiptSha256'] = hashlib.sha256(_encoded(result)).hexdigest()
    return result


def _blocked(state):
    acknowledged = {(a['runId'], a['receiptSha256']) for a in state['acknowledgments']}
    return any(r['receipt']['recoveryRequired'] and
               (r['receipt']['runId'], _receipt(r)['receiptSha256']) not in acknowledged
               for r in state['runs'])


def _task_output(workspace, task):
    try:
        _private_path(workspace, True)
        target = workspace / OUTPUTS[task]
        fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 32768: return ''
            return os.read(fd, 32768).decode('utf-8', errors='replace')
        finally:
            os.close(fd)
    except (OSError, ValueError):
        return ''


class Coordinator:
    def __init__(self, root, config_path, *, manifest, wheel_dir, max_units=20):
        self._store = _Store(root)
        self._mutex = threading.RLock()
        self._closed = False
        self._process = None
        self._cancel = threading.Event()
        self._active = None
        self._future = None
        try:
            self._config_path = Path(config_path)
            self._frozen = {}
            self._freeze(self._config_path)
            raw = yaml.safe_load(_read(self._config_path, 65536))
            if type(raw) is not dict or raw.get('kind') != 'unified':
                raise ValueError('unified host configuration required')
            for key in ('native_config', 'api_config'):
                if raw.get(key) is not None:
                    self._freeze(self._config_path.parent / raw[key])
            audit_candidate(manifest, wheel_dir)
            config = require_unified().UnifiedRuntimeConfig.load(self._config_path)
            self._profiles = []
            for name in config.pools[config.default_pool].profiles:
                if config.native_config and name in config.native_config.profiles:
                    profile = config.native_config.profiles[name]
                    backend = profile.backend
                else:
                    profile = config.api_config.profiles[name]
                    backend = 'api'
                model = ''.join(c for c in profile.model[:256] if c.isprintable())
                self._profiles.append({'name': name, 'backend': backend, 'model': model})
            self._names = {p['name'] for p in self._profiles}
            self._allowance = SharedLiveAllowance(self._store.root / 'allowance.json', max_calls=max_units, ceiling=256)
            self._state = self._store.read()
            for row in self._state['runs']:
                if row['receipt']['state'] == 'running':
                    row['receipt'].update(state='uncertain', recoveryRequired=True,
                                          failureReason='execution_uncertain')
                    row['settledActual'] = None
            # A terminal receipt is durable before quota settlement. Repeating
            # settlement is idempotent and never dispatches or releases unknowns.
            self._store.write(self._state)
            for row in self._state['runs']:
                if row.get('reservation'):
                    self._allowance.finish(row['reservation'], actual_requests=row.get('settledActual'))
            self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='explorer')
        except Exception:
            self._store.close()
            raise ValueError('config_invalid') from None

    def _freeze(self, path):
        # Check the unresolved path first: normalizing link/../file would erase
        # the symlink and freeze a different file from the SDK's resolve().
        _private_path(path)
        path = Path(os.path.abspath(path))
        data = _read(path, 65536)
        info = path.stat()
        self._frozen[path] = (info.st_dev, info.st_ino, hashlib.sha256(data).digest())

    def _check(self):
        if self._closed: raise ValueError('blocked')
        self._store.check()
        for path, identity in self._frozen.items():
            data = _read(path, 65536); info = path.stat()
            if (info.st_dev, info.st_ino, hashlib.sha256(data).digest()) != identity:
                raise ValueError('config_changed')

    def status(self):
        with self._mutex:
            return {'liveEnabled': True, 'profiles': deepcopy(self._profiles), 'policy': dict(POLICY),
                    'allowance': self._allowance.status(), 'blocked': _blocked(self._state),
                    'activeRunId': self._active, 'runs': [_receipt(r) for r in self._state['runs']]}

    def submit(self, request_id, task, local_timeout_s=180):
        if (type(request_id) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', request_id) or
                task not in CASE_IDS or type(local_timeout_s) is not int or local_timeout_s not in (180, 240)):
            raise ValueError('invalid_request')
        with self._mutex:
            self._check()
            for row in self._state['runs']:
                if row['receipt']['requestId'] == request_id:
                    if row['receipt']['task'] != task or row['timeout'] != local_timeout_s:
                        raise ValueError('request_conflict')
                    return _receipt(row)
            if self._active: raise ValueError('busy')
            if _blocked(self._state): raise ValueError('blocked')
            if len(self._state['runs']) >= 64: raise ValueError('blocked')
            if self._allowance.status()['remaining'] < 10: raise ValueError('allowance_exhausted')
            run_id = uuid.uuid4().hex
            receipt = dict(runId=run_id, requestId=request_id, task=task, state='running', passed=False,
                           durationMs=0, selectedProfile=None, events=[], output='', failureReason=None,
                           recoveryRequired=False, usage=dict(nativeAttempts=None, apiRequests=None,
                           apiToolCalls=None, knownTokens=None), startedAt=time.time())
            row = {'receipt': receipt, 'timeout': local_timeout_s, 'reservation': None}
            self._state['runs'].append(row)
            # Persist authority before either reserving quota or dispatching.
            self._store.write(self._state)
            try:
                row['reservation'] = self._allowance.reserve(maximum_requests=10)
                self._store.write(self._state)
                self._active = run_id
                self._cancel.clear()
                self._future = self._executor.submit(self._work, row)
            except Exception:
                receipt.update(state='uncertain', recoveryRequired=True, failureReason='execution_uncertain')
                self._store.write(self._state)
                raise ValueError('blocked') from None
            return _receipt(row)

    def get(self, run_id):
        with self._mutex:
            for row in self._state['runs']:
                if row['receipt']['runId'] == run_id: return _receipt(row)
            raise ValueError('not_found')

    @staticmethod
    def _interrupt(process):
        # Every invocation starts a new session: this PID is the exact owned
        # process-group ID. Give Runtime's leader a bounded chance to clean up,
        # then remove remaining group members even if the leader already exited.
        if process.poll() is None:
            try: process.send_signal(signal.SIGINT)
            except ProcessLookupError: pass
            try: process.wait(timeout=2)
            except subprocess.TimeoutExpired: pass
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        process.wait(timeout=2)

    def _invoke(self, command):
        if self._cancel.is_set(): raise ValueError('blocked')
        env = dict(os.environ)
        for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', 'ANTHROPIC_BASE_URL'):
            env.pop(key, None)
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=env, start_new_session=True)
        with self._mutex: self._process = process
        data = bytearray(); total = 0; deadline = time.monotonic() + 330
        try:
            with selectors.DefaultSelector() as selector:
                for stream in (process.stdout, process.stderr):
                    os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ)
                while selector.get_map():
                    if self._cancel.is_set() or time.monotonic() > deadline:
                        raise ValueError('execution interrupted')
                    for key, _ in selector.select(.05):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk: selector.unregister(key.fileobj); continue
                        total += len(chunk)
                        if total > 1_048_576: raise ValueError('CLI output limit')
                        if key.fileobj is process.stdout: data.extend(chunk)
                process.wait(timeout=2)
            events = [json.loads(line) for line in data.splitlines()]
            if (not events or len(events) > 1024 or events[-1].get('event') != 'result' or
                    process.returncode != (0 if events[-1]['exit_code'] == 0 else 1)):
                raise ValueError('terminal receipt absent')
            return events[-1], events[:-1]
        finally:
            self._interrupt(process)
            process.stdout.close(); process.stderr.close()
            with self._mutex: self._process = None

    def _work(self, row):
        started = time.monotonic(); receipt = row['receipt']; observed = None
        workspace = self._store.root / ('workspace-' + receipt['runId'])
        result_fields = dict(state='uncertain', passed=False, recoveryRequired=True,
                             failureReason='execution_uncertain')
        try:
            self._check()
            workspace.mkdir(mode=0o700)
            prepare(receipt['task'], workspace)
            result, events = self._invoke(cli_command(self._config_path, receipt['task'], workspace,
                                                     local_timeout_s=row['timeout']))
            metadata = result['metadata']; info = metadata['unified_execution_v1']
            def count(key, maximum):
                value = info.get(key)
                if value is None: return None
                if type(value) is not int or not 0 <= value <= maximum: raise ValueError('invalid usage')
                return value
            tokens = info.get('known_tokens')
            # This aggregate may include native observations. The CLI enforces
            # the API token cap; native internal usage has no such claimed cap.
            if type(tokens) is not int or not 0 <= tokens <= 9007199254740991:
                tokens = None
            usage = dict(nativeAttempts=count('native_attempts', 2), apiRequests=count('api_provider_requests', 8),
                         apiToolCalls=count('api_tool_calls', 7), knownTokens=tokens)
            if usage['nativeAttempts'] is not None and usage['apiRequests'] is not None:
                observed = usage['nativeAttempts'] + usage['apiRequests']
            recovery = (bool(metadata.get('recovery_required')) or observed is None or
                        result.get('timed_out') is True or metadata.get('failure_reason') in TIMEOUT_REASONS)
            # Never dereference model-created output links, including before grading.
            output = _task_output(workspace, receipt['task'])
            passed = bool(output) and result['exit_code'] == 0 and grade(receipt['task'], workspace)['passed']
            filtered = []
            for event in events:
                if event.get('event') not in EVENTS: continue
                entry = {'event': event['event']}
                if event.get('profile') in self._names: entry['profile'] = event['profile']
                if event.get('reason') in REASONS: entry['reason'] = event['reason']
                filtered.append(entry)
            reason = metadata.get('failure_reason')
            result_fields = dict(state='uncertain' if recovery else 'completed' if passed else 'failed',
                                 passed=passed and not recovery, recoveryRequired=recovery, usage=usage,
                                 output=output, events=filtered[:128],
                                 selectedProfile=metadata.get('profile') if metadata.get('profile') in self._names else None,
                                 failureReason='execution_uncertain' if recovery else None if passed else
                                 reason if reason in REASONS else 'contract_failed' if result['exit_code'] == 0 else 'execution_failure')
        except Exception:
            pass  # Provider/configuration errors are never public diagnostic strings.
        finally:
            with self._mutex:
                result_fields['output'] = _task_output(workspace, receipt['task'])
                if self._cancel.is_set():
                    result_fields.update(state='cancelled', passed=False, recoveryRequired=True,
                                         failureReason='interrupted')
                    observed = None
                receipt.update(result_fields, durationMs=round((time.monotonic() - started) * 1000))
                row['settledActual'] = observed
                self._store.write(self._state)
                try: self._allowance.finish(row['reservation'], actual_requests=observed)
                except Exception:
                    receipt.update(state='uncertain', passed=False, recoveryRequired=True,
                                   failureReason='execution_uncertain')
                    self._store.write(self._state)
                self._active = None

    def cancel(self, run_id):
        with self._mutex:
            row = self.get(run_id)
            if self._active == run_id: self._cancel.set()
            return row

    def close(self):
        with self._mutex:
            if self._closed: return
            self._cancel.set()
        self._executor.shutdown(wait=True)
        with self._mutex:
            self._closed = True
            self._store.close()


def reconcile(root, run_id, receipt_sha256, note):
    if (type(note) is not str or not 1 <= len(note.encode()) <= 2048 or
            any(ord(c) < 32 and c not in '\n\t' for c in note) or
            type(receipt_sha256) is not str or not re.fullmatch('[0-9a-f]{64}', receipt_sha256)):
        raise ValueError('invalid_request')
    store = _Store(root)
    try:
        state = store.read()
        for row in state['runs']:
            receipt = _receipt(row)
            if receipt['runId'] != run_id: continue
            if receipt['state'] == 'running' or not receipt['recoveryRequired'] or receipt['receiptSha256'] != receipt_sha256:
                raise ValueError('receipt_conflict')
            acknowledgment = {'runId': run_id, 'receiptSha256': receipt_sha256, 'note': note, 'acknowledgedAt': time.time()}
            if not any(a['runId'] == run_id and a['receiptSha256'] == receipt_sha256 for a in state['acknowledgments']):
                state['acknowledgments'].append(acknowledgment)
                store.write(state)
            return {'runId': run_id, 'acknowledged': True, 'blocked': _blocked(state)}
        raise ValueError('not_found')
    finally:
        store.close()


def inspect_receipt(root, run_id):
    """Inspect retained evidence offline without opening profiles or providers.

    An interrupted admission has no live owner once this exclusive lock succeeds.
    It becomes uncertain, never runnable. Its reservation stays fully retained.
    """
    store = _Store(root)
    try:
        state = store.read()
        changed = False
        for row in state['runs']:
            if row['receipt']['state'] == 'running':
                row['receipt'].update(state='uncertain', passed=False, recoveryRequired=True,
                                      failureReason='execution_uncertain')
                row['settledActual'] = None
                changed = True
        if changed: store.write(state)
        for row in state['runs']:
            if row['receipt']['runId'] == run_id: return _receipt(row)
        raise ValueError('not_found')
    finally:
        store.close()
