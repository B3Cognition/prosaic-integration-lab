"""Disposable resources identified by exact engine IDs and ownership labels."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import uuid

from .manifest import validate_resource

ROOT = Path(__file__).resolve().parents[1]


class EngineError(RuntimeError):
    pass


def command(engine, *args):
    try:
        result = subprocess.run([engine, *args], capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        raise EngineError('engine unavailable or command timed out') from None
    if result.returncode:
        # Engine stderr may include command configuration; keep it private.
        raise EngineError(f'engine operation failed: {args[0]}')
    return result.stdout.strip()


class OwnedStack:
    def __init__(self, engine='docker', postgres_major=16):
        if engine not in {'docker', 'podman'} or postgres_major not in {16, 18}:
            raise ValueError('unsupported engine/PostgreSQL major')
        self.engine, self.major = engine, postgres_major
        self.owner = uuid.uuid4().hex
        self.directory = ROOT / '.lab' / self.owner
        self.directory.mkdir(parents=True, mode=0o700)
        self.secrets = self.directory / 'secrets'
        self.secrets.mkdir(mode=0o700)
        self.manifest = {'owner': self.owner, 'engine': engine, 'postgres_major': postgres_major,
                         'resources': [], 'endpoints': {}, 'images': {}}
        self._save()

    def _save(self):
        temporary = self.directory / 'ownership.tmp'
        temporary.write_text(json.dumps(self.manifest, indent=2) + '\n')
        temporary.replace(self.directory / 'ownership.json')

    def _record(self, kind, identifier):
        self.manifest['resources'].append({'kind': kind, 'id': identifier})
        self._save()
        return identifier

    def _secret(self, name, content):
        path = self.secrets / name
        path.write_text(content)
        path.chmod(0o600)
        return path

    def start(self):
        command(self.engine, 'info')
        images = json.loads((ROOT / 'dependencies/images.json').read_text())
        pg_image = images[f'postgres{self.major}']
        command(self.engine, 'pull', pg_image)
        network = self._record('network', command(self.engine, 'network', 'create', '--label',
            f'io.prosaic.lab.owner={self.owner}', f'prosaic-lab-{self.owner}'))
        volume = self._record('volume', command(self.engine, 'volume', 'create', '--label',
            f'io.prosaic.lab.owner={self.owner}', f'prosaic-lab-{self.owner}'))
        admin = secrets.token_hex(24)
        password = self._secret('postgres_password', admin)
        db = self._record('container', command(self.engine, 'run', '-d', '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', network, '--network-alias', 'database',
            '-p', '127.0.0.1::5432', '-e', 'POSTGRES_PASSWORD_FILE=/run/secrets/password',
            '-v', f'{password}:/run/secrets/password:ro', '-v',
            f'{volume}:/var/lib/postgresql' + ('/data' if self.major == 16 else ''),
            pg_image))
        self.manifest['database_id'] = db
        self.manifest['network_id'] = network
        self.manifest['images']['postgres'] = pg_image
        self.manifest['images']['consumer'] = command(self.engine, 'image', 'inspect',
            'prosaic-integration-lab:dev', '--format', '{{.Id}}')
        self._save()
        deadline = time.monotonic() + 60
        while True:
            try:
                command(self.engine, 'exec', db, 'pg_isready', '-U', 'postgres')
                break
            except EngineError:
                if time.monotonic() >= deadline:
                    raise EngineError('database readiness timeout')
                time.sleep(0.2)
        port = json.loads(command(self.engine, 'inspect', db))[0]['NetworkSettings']['Ports']['5432/tcp'][0]['HostPort']
        self.manifest['database_port'] = int(port)
        credentials = {name: secrets.token_hex(24) for name in
            ('lab_migration', 'harness_runtime', 'accounting_runtime', 'app_runtime')}
        self._secret('provision.json', json.dumps({'admin_password': admin, 'roles': credentials}))
        container_config = {'namespace': f'lab-{self.owner}', 'environment': 'sandbox', 'assets': '/srv/lab/assets',
                            'fixture_events_url': 'http://model:8000/events'}
        host_config = dict(container_config)
        host_config['migration_dsn'] = f'host=127.0.0.1 port={port} dbname=lab user=lab_migration password={credentials["lab_migration"]}'
        host_config['fixture_manifest'] = str(self.directory / 'ownership.json')
        for key, role in [('harness_dsn', 'harness_runtime'), ('accounting_dsn', 'accounting_runtime'), ('app_dsn', 'app_runtime')]:
            container_config[key] = f'host=database port=5432 dbname=lab user={role} password={credentials[role]}'
            host_config[key] = f'host=127.0.0.1 port={port} dbname=lab user={role} password={credentials[role]}'
        principals = {secrets.token_hex(24): {'tenant_id': tenant, 'actor_id': actor, 'billing_account_id': account}
            for tenant, actor, account in [('tenant-a', 'alice', 'account-a'), ('tenant-a', 'bob', 'account-a'), ('tenant-b', 'carol', 'account-b')]}
        container_config['principals'] = principals
        host_config['principals'] = principals
        self._secret('service.json', json.dumps(container_config))
        self._secret('host.json', json.dumps(host_config))
        provision = self._record('container', command(self.engine, 'create', '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', network, '-v',
            f'{self.secrets / "provision.json"}:/run/secrets/provision.json:ro',
            self.manifest['images']['consumer'], 'python', 'scripts/provision.py'))
        command(self.engine, 'start', '-a', provision)
        self._save()
        return self.manifest

    def start_replica(self, name):
        identifier = self._record('container', command(self.engine, 'run', '-d', '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', self.manifest['network_id'],
            '-p', '127.0.0.1::8080', '-v', f'{self.secrets / "service.json"}:/run/secrets/service.json:ro',
            '-e', 'LAB_CONFIG=/run/secrets/service.json', self.manifest['images']['consumer'],
            'python', '-m', 'uvicorn', 'prosaic_integration_lab.app:create_app', '--factory',
            '--host', '0.0.0.0', '--port', '8080', '--no-access-log'))
        port = json.loads(command(self.engine, 'inspect', identifier))[0]['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort']
        url = f'http://127.0.0.1:{port}'
        self.manifest['endpoints'][name] = url
        self.manifest.setdefault('replica_ids', {})[name] = identifier
        self._save()
        import httpx
        deadline = time.monotonic() + 30
        while True:
            try:
                if httpx.get(url + '/readyz', timeout=2).status_code == 200:
                    return url
            except httpx.HTTPError:
                pass
            if time.monotonic() >= deadline:
                raise EngineError('replica readiness timeout')
            time.sleep(0.2)

    def start_model(self):
        identifier = self._record('container', command(self.engine, 'run', '-d', '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', self.manifest['network_id'], '--network-alias', 'model',
            '-p', '127.0.0.1::8000', self.manifest['images']['consumer'], 'python', '-m', 'uvicorn',
            'lab_runner.model:app', '--host', '0.0.0.0', '--port', '8000', '--no-access-log'))
        port = json.loads(command(self.engine, 'inspect', identifier))[0]['NetworkSettings']['Ports']['8000/tcp'][0]['HostPort']
        url = f'http://127.0.0.1:{port}'
        self.manifest['endpoints']['model'] = url
        self._save()
        import httpx
        deadline = time.monotonic() + 30
        while True:
            try:
                if httpx.get(url + '/stats', timeout=2).status_code == 200:
                    return url
            except httpx.HTTPError:
                pass
            if time.monotonic() >= deadline:
                raise EngineError('model readiness timeout')
            time.sleep(0.2)

    def stop(self):
        failures = []
        for resource in reversed(self.manifest['resources']):
            kind, identifier = resource['kind'], resource['id']
            try:
                args = ('inspect', identifier) if kind == 'container' else (kind, 'inspect', identifier)
                state = json.loads(command(self.engine, *args))[0]
                validate_resource(state, identifier, self.owner)
                mutation = ('rm', '-f', identifier) if kind == 'container' else (kind, 'rm', identifier)
                command(self.engine, *mutation)
                # Absence is verified; a failed inspection is expected after removal.
                try:
                    command(self.engine, *args)
                except EngineError:
                    continue
                raise EngineError('owned resource still exists after cleanup')
            except (EngineError, ValueError):
                failures.append({'kind': kind, 'id': identifier})
        self.manifest['cleanup'] = 'failed' if failures else 'verified'
        self.manifest['cleanup_failures'] = failures
        self._save()
        if failures:
            raise EngineError('owned fixture cleanup failed; inspect ownership manifest')
        for path in self.secrets.iterdir():
            path.unlink()
        self.secrets.rmdir()
