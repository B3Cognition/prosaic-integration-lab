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
    def __init__(self, engine='docker', postgres_major=16, users=3, *, candidate=False, identity=False):
        from .workload import identities
        self.identities = identities(users)
        if engine not in {'docker', 'podman'} or postgres_major not in {16, 18}:
            raise ValueError('unsupported engine/PostgreSQL major')
        self.engine, self.major = engine, postgres_major
        self.candidate = candidate
        self.identity = identity
        self.owner = uuid.uuid4().hex
        self.directory = ROOT / '.lab' / self.owner
        self.directory.mkdir(parents=True, mode=0o700)
        self.secrets = self.directory / 'secrets'
        self.secrets.mkdir(mode=0o700)
        self.manifest = {'owner': self.owner, 'engine': engine, 'postgres_major': postgres_major,
                         'resources': [], 'endpoints': {}, 'images': {},
                         'dependency_mode': 'candidate' if candidate else 'released'}
        self._save()

    def _save(self):
        temporary = self.directory / 'ownership.tmp'
        temporary.write_text(json.dumps(self.manifest, indent=2) + '\n')
        temporary.replace(self.directory / 'ownership.json')

    def _record(self, kind, identifier):
        self.manifest['resources'].append({'kind': kind, 'id': identifier})
        self._save()
        return identifier

    def _create(self, kind, name, *args):
        intent = {'kind': kind, 'name': name}
        if intent in self.manifest.get('pending_resources', []):
            raise EngineError('creation outcome unresolved; refusing repeat mutation')
        self.manifest.setdefault('pending_resources', []).append(intent)
        self._save()  # Durable intention precedes the engine mutation.
        position = 1 if kind == 'container' else 2
        creation = (*args[:position], '--label', f'io.prosaic.lab.resource={name}', *args[position:])
        identifier = command(self.engine, *creation)
        inspection = ('inspect', identifier) if kind == 'container' else (kind, 'inspect', identifier)
        state = json.loads(command(self.engine, *inspection))[0]
        validate_resource(state, identifier, self.owner)
        self._record(kind, identifier)
        self.manifest['pending_resources'].remove(intent)
        self._save()
        return identifier

    def _ids(self, kind, *, owned_only=False):
        args = ['ps', '-a', '-q', '--no-trunc'] if kind == 'container' else [kind, 'ls', '-q']
        if kind == 'network':
            args.append('--no-trunc')
        if owned_only:
            args += ['--filter', f'label=io.prosaic.lab.owner={self.owner}']
        return command(self.engine, *args).splitlines()

    def _reconcile_intents(self):
        for intent in list(self.manifest.get('pending_resources', [])):
            kind, name = intent['kind'], intent['name']
            found = False
            for identifier in self._ids(kind, owned_only=True):
                args = ('inspect', identifier) if kind == 'container' else (kind, 'inspect', identifier)
                state = json.loads(command(self.engine, *args))[0]
                labels = state.get('Labels') or state.get('Config', {}).get('Labels') or {}
                if labels.get('io.prosaic.lab.resource') != name:
                    continue
                validate_resource(state, identifier, self.owner)
                found = True
                resource = {'kind': kind, 'id': identifier}
                if resource not in self.manifest['resources']:
                    self._record(kind, identifier)
            if not found:
                raise EngineError('creation outcome remains unknown; cleanup cannot be certified')
            self.manifest['pending_resources'].remove(intent)
            self._save()

    def _secret(self, name, content):
        path = self.secrets / name
        path.write_text(content)
        path.chmod(0o600)
        return path

    def start(self):
        command(self.engine, 'info')
        image_name = 'prosaic-integration-lab:candidate' if self.candidate else 'prosaic-integration-lab:dev'
        image = json.loads(command(self.engine, 'image', 'inspect', image_name))[0]
        if self.candidate:
            import hashlib
            manifest = ROOT / 'dependencies/accounting-candidate.json'
            expected = hashlib.sha256(manifest.read_bytes()).hexdigest()
            if (image['Config'].get('Labels') or {}).get('io.prosaic.lab.candidate-manifest') != expected:
                raise EngineError('candidate image provenance mismatch')
            self.manifest['candidate_manifest_sha256'] = expected
        self.manifest['images']['consumer'] = image['Id']
        self._save()
        images = json.loads((ROOT / 'dependencies/images.json').read_text())
        pg_image = images[f'postgres{self.major}']
        command(self.engine, 'pull', pg_image)
        name = f'prosaic-lab-{self.owner}'
        network = self._create('network', name, 'network', 'create', '--label',
            f'io.prosaic.lab.owner={self.owner}', name)
        volume = self._create('volume', name, 'volume', 'create', '--label',
            f'io.prosaic.lab.owner={self.owner}', name)
        admin = secrets.token_hex(24)
        password = self._secret('postgres_password', admin)
        db_name = name + '-database'
        db = self._create('container', db_name, 'run', '-d', '--name', db_name, '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', network, '--network-alias', 'database',
            '-p', '127.0.0.1::5432', '-e', 'POSTGRES_PASSWORD_FILE=/run/secrets/password',
            '-v', f'{password}:/run/secrets/password:ro', '-v',
            f'{volume}:/var/lib/postgresql' + ('/data' if self.major == 16 else ''),
            pg_image)
        self.manifest['database_id'] = db
        self.manifest['network_id'] = network
        self.manifest['images']['postgres'] = pg_image
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
            for tenant, actor, account in [(p['tenant_id'], p['actor_id'], p['billing_account_id']) for p in self.identities]}
        container_config['principals'] = principals
        host_config['principals'] = principals
        if self.identity:
            from .keycloak import start
            start(self,container_config,host_config)
        self._secret('service.json', json.dumps(container_config))
        self._secret('host.json', json.dumps(host_config))
        provision_name = name + '-provision'
        provision = self._create('container', provision_name, 'create', '--name', provision_name, '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', network,
            '--user','0','--read-only','--cap-drop','ALL','--cap-add','DAC_OVERRIDE',
            '--security-opt','no-new-privileges','--pids-limit','128','--memory','512m','-v',
            f'{self.secrets / "provision.json"}:/run/secrets/provision.json:ro',
            self.manifest['images']['consumer'], 'python', 'scripts/provision.py')
        command(self.engine, 'start', '-a', provision)
        runtime_name = name+'-runtime-config'
        runtime_volume = self._create('volume',runtime_name,'volume','create','--label',
            f'io.prosaic.lab.owner={self.owner}',runtime_name)
        delivery_name = name+'-deliver-config'
        ca_mount = ['-v',f'{self.secrets / "issuer-ca.pem"}:/run/source/issuer-ca.pem:ro'] if self.identity else []
        delivery = self._create('container',delivery_name,'create','--name',delivery_name,'--label',
            f'io.prosaic.lab.owner={self.owner}','--network','none','--user','0','--read-only',
            '--cap-drop','ALL','--cap-add','CHOWN','--cap-add','DAC_OVERRIDE',
            '--security-opt','no-new-privileges','--memory','128m','--pids-limit','32',
            '-v',f'{self.secrets / "service.json"}:/run/secrets/service.json:ro',
            '-v',f'{runtime_volume}:/run/runtime',*ca_mount,self.manifest['images']['consumer'],
            'python','-m','lab_runner.secret_delivery')
        command(self.engine,'start','-a',delivery)
        self.manifest['runtime_config_volume'] = runtime_volume
        self.manifest['runtime_config_job'] = delivery
        self._save()
        return self.manifest

    def start_replica(self, name):
        replica_name = f'prosaic-lab-{self.owner}-replica-{name}'
        identifier = self._create('container', replica_name, 'run', '-d', '--name', replica_name, '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', self.manifest['network_id'],
            '--user','10001:10001','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--memory','512m','--cpus','2','--pids-limit','128',
            '--tmpfs','/tmp:rw,noexec,nosuid,size=64m,mode=1777',
            '-p', '127.0.0.1::8080', '-v', f'{self.manifest["runtime_config_volume"]}:/run/secrets:ro',
            '-e', 'LAB_CONFIG=/run/secrets/service.json', self.manifest['images']['consumer'],
            'python', '-m', 'uvicorn', 'prosaic_integration_lab.app:create_app', '--factory',
            '--host', '0.0.0.0', '--port', '8080', '--no-access-log',
            '--timeout-keep-alive','5','--h11-max-incomplete-event-size','16384',
            '--limit-concurrency','64','--backlog','64','--limit-max-requests','100000')
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
        model_name = f'prosaic-lab-{self.owner}-model'
        identifier = self._create('container', model_name, 'run', '-d', '--name', model_name, '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', self.manifest['network_id'], '--network-alias', 'model',
            '--user','10001:10001','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--memory','256m','--cpus','2','--pids-limit','128',
            '--tmpfs','/tmp:rw,noexec,nosuid,size=32m,mode=1777',
            '-p', '127.0.0.1::8000', self.manifest['images']['consumer'], 'python', '-m', 'uvicorn',
            'lab_runner.model:app', '--host', '0.0.0.0', '--port', '8000', '--no-access-log')
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
        try:
            self._reconcile_intents()
        except (EngineError, ValueError):
            failures.append({'kind': 'pending', 'id': 'unknown'})
        for resource in reversed(self.manifest['resources']):
            kind, identifier = resource['kind'], resource['id']
            try:
                if identifier not in self._ids(kind):
                    continue
                args = ('inspect', identifier) if kind == 'container' else (kind, 'inspect', identifier)
                state = json.loads(command(self.engine, *args))[0]
                validate_resource(state, identifier, self.owner)
                mutation = ('rm', '-f', identifier) if kind == 'container' else (kind, 'rm', identifier)
                command(self.engine, *mutation)
                # A successful inventory, not a failed inspection, proves
                # absence. Daemon outages/timeouts cannot certify cleanup.
                if identifier in self._ids(kind):
                    raise EngineError('owned resource still exists after cleanup')
            except (EngineError, ValueError):
                failures.append({'kind': kind, 'id': identifier})
        self.manifest['cleanup'] = 'failed' if failures else 'verified'
        self.manifest['cleanup_failures'] = failures
        self._save()
        if failures:
            raise EngineError('owned fixture cleanup failed; inspect ownership manifest')
        if self.secrets.exists():
            for path in self.secrets.iterdir():
                path.unlink()
            self.secrets.rmdir()
