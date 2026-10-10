"""Disposable resources identified by exact engine IDs and ownership labels."""
import json
import ipaddress
import os
from pathlib import Path
import secrets
import subprocess
import time
import uuid

from .manifest import validate_resource

ROOT = Path(__file__).resolve().parents[1]


class EngineError(RuntimeError):
    def __init__(self,message,*,diagnostic=None):
        super().__init__(message)
        self.diagnostic=diagnostic


def choose_subnet(networks,owner):
    """Select an explicit fixture subnet without touching existing networks."""
    occupied = [ipaddress.ip_network(c['Subnet'],strict=False) for n in networks
                for c in ((n.get('IPAM') or {}).get('Config') or []) if c.get('Subnet')]
    occupied.extend(ipaddress.ip_network(c['subnet'],strict=False) for n in networks
                    for c in (n.get('subnets') or []) if c.get('subnet'))
    initial = int(owner[:2],16)
    for offset in range(256):
        candidate = ipaddress.ip_network(f'10.250.{(initial+offset)%256}.0/24')
        if all(candidate.version != old.version or not candidate.overlaps(old) for old in occupied):
            return str(candidate)
    raise ValueError('no free owned fixture subnet')


def command(engine, *args):
    operation=args[0] if args and args[0] in {'info','image','pull','run','create','start','stop','kill',
        'exec','inspect','logs','ps','rm','network','volume'} else 'unknown'
    if operation in {'network','volume','image'} and len(args)>1 and args[1] in {'create','inspect','rm','ls'}:
        operation+='_'+args[1]
    try:
        result = subprocess.run([engine, *args], capture_output=True, text=True,
            timeout=15 if operation=='info' else 180)
    except subprocess.TimeoutExpired:
        raise EngineError('engine unavailable or command timed out',diagnostic={
            'operation':operation,'return_code':None,'category':'command_timeout','outcome':'unknown'}) from None
    except OSError:
        raise EngineError('engine unavailable or command timed out',diagnostic={
            'operation':operation,'return_code':None,'category':'engine_unavailable','outcome':'unknown'}) from None
    if result.returncode:
        # Engine stderr may include command configuration; keep it private.
        stderr=result.stderr.lower()
        categories=(('rate_limited',('rate limit','too many requests')),
            ('image_missing',('no such image',)),('engine_unavailable',('cannot connect','connection refused','daemon not running')),
            ('network_timeout',('i/o timeout','context deadline exceeded')),
            ('permission_denied',('permission denied','unauthorized')))
        category=next((name for name,markers in categories if any(marker in stderr for marker in markers)),'engine_failed')
        code=result.returncode if type(result.returncode) is int and -128 <= result.returncode <= 255 else None
        raise EngineError('engine operation failed: '+operation,diagnostic={
            'operation':operation,'return_code':code,'category':category,'outcome':'unknown'})
    return result.stdout.strip()


class OwnedStack:
    def __init__(self, engine='docker', postgres_major=16, users=3, *, candidate=False, identity=False, billing=False, consumer_image=None, observability=False,capacity_policy=None, candidate_manifest=None,native=False,baseline_image=None):
        from .workload import identities
        self.identities = identities(users)
        if engine not in {'docker', 'podman'} or postgres_major not in {16, 18}:
            raise ValueError('unsupported engine/PostgreSQL major')
        self.engine, self.major = engine, postgres_major
        self.candidate = candidate
        self.candidate_manifest = Path(candidate_manifest) if candidate_manifest is not None else ROOT / 'dependencies/accounting-candidate.json'
        self.identity = identity
        self.billing = billing
        self.observability=observability
        self.capacity_policy=capacity_policy
        if consumer_image is not None:
            import re
            if not re.fullmatch('sha256:[0-9a-f]{64}',consumer_image): raise ValueError('immutable consumer image required')
        self.consumer_image = consumer_image
        self.native_fixture=native
        self.baseline_image=baseline_image
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

    def verify_owned(self):
        """Verify every exact container identity before operational fault work."""
        if not self.manifest.get('database_id') or self.manifest.get('payload_audit')!='verified':
            raise ValueError('verified owned stack required')
        recorded={r['id'] for r in self.manifest['resources'] if r['kind']=='container'}
        if self.manifest['database_id'] not in recorded:raise ValueError('unrecorded database')
        for identifier in recorded:
            validate_resource(json.loads(command(self.engine,'inspect',identifier))[0],identifier,self.owner)
        return True

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

    def network_inventory(self):
        for _ in range(3):
            identifiers = self._ids('network')
            if not identifiers:
                return []
            try:
                return json.loads(command(self.engine,'network','inspect',*identifiers))
            except EngineError:
                if not set(identifiers) - set(self._ids('network')):
                    raise
        raise EngineError('network inventory changed repeatedly',diagnostic={
            'operation':'network_inspect','return_code':None,
            'category':'engine_failed','outcome':'unknown'})

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
        image_name = self.consumer_image or ('prosaic-integration-lab:candidate' if self.candidate else 'prosaic-integration-lab:dev')
        image = json.loads(command(self.engine, 'image', 'inspect', image_name))[0]
        labels = image['Config'].get('Labels') or {}
        import hashlib
        manifest = self.candidate_manifest if self.candidate else ROOT / 'dependencies/releases.json'
        expected = hashlib.sha256(manifest.read_bytes()).hexdigest()
        mode = 'candidate' if self.candidate else 'released'
        label = 'io.prosaic.lab.candidate-manifest' if self.candidate else 'io.prosaic.lab.release-manifest'
        if (labels.get(label) != expected or labels.get('io.prosaic.lab.sdk-manifest') != expected or
                labels.get('io.prosaic.lab.dependency-mode') != mode or
                (not self.candidate and 'io.prosaic.lab.candidate-manifest' in labels)):
            raise EngineError(f'{mode} image provenance mismatch')
        if self.baseline_image is not None:
            from .legacy_upgrade import BASELINE_MANIFEST,validate_baseline
            validate_baseline(json.loads(command(self.engine,'image','inspect',self.baseline_image))[0],BASELINE_MANIFEST)
        self.manifest['candidate_manifest_sha256' if self.candidate else 'released_manifest_sha256'] = expected
        self.manifest['sdk_manifest_sha256'] = expected
        if self.candidate:
            self.manifest['released_manifest_sha256']=hashlib.sha256((ROOT/'dependencies/releases.json').read_bytes()).hexdigest()
            selected=json.loads(manifest.read_text())
            lineage=selected.get('candidate_lineage')
            if lineage is not None:
                self.manifest['candidate_lineage_sha256']=hashlib.sha256(
                    (json.dumps(lineage,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
        self.manifest['images']['consumer'] = image['Id']
        self._save()
        audit_name = f'prosaic-lab-{self.owner}-payload-audit'
        audit_manifest = 'dependencies/releases.json'
        audit_wheels = '/srv/wheels'
        audit_job = self._create('container',audit_name,'create','--name',audit_name,
            '--label',f'io.prosaic.lab.owner={self.owner}','--network','none','--read-only',
            '--cap-drop','ALL','--security-opt','no-new-privileges','--memory','128m','--pids-limit','32',
            image['Id'],'python','scripts/audit_install.py',audit_manifest,audit_wheels,
            expected)
        command(self.engine,'start','-a',audit_job)
        self.manifest['payload_audit'] = 'verified'
        self._save()
        if self.baseline_image is not None:
            from .legacy_upgrade import BASELINE_SHA256,BASELINE_COMMIT
            name=f'prosaic-lab-{self.owner}-baseline-audit'
            job=self._create('container',name,'create','--name',name,'--label',
                f'io.prosaic.lab.owner={self.owner}','--network','none','--read-only','--cap-drop','ALL',
                '--security-opt','no-new-privileges',self.baseline_image,'python','scripts/audit_install.py',
                'dependencies/releases.json','/srv/wheels',BASELINE_SHA256)
            command(self.engine,'start','-a',job)
            self.manifest.update(baseline_payload_audit='verified',baseline_manifest_sha256=BASELINE_SHA256,
                                 baseline_source=BASELINE_COMMIT)
            self.manifest['images']['baseline']=self.baseline_image;self._save()
        images = json.loads((ROOT / 'dependencies/images.json').read_text())
        pg_image = images[f'postgres{self.major}']
        command(self.engine, 'pull', pg_image)
        name = f'prosaic-lab-{self.owner}'
        networks = self.network_inventory()
        network_options = ['--subnet',choose_subnet(networks,self.owner)]
        network = self._create('network', name, 'network', 'create', '--label',
            f'io.prosaic.lab.owner={self.owner}', *network_options, name)
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
        if self.billing:
            credentials['billing_exporter'] = secrets.token_hex(24)
        self._secret('provision.json', json.dumps({'admin_password': admin, 'roles': credentials}))
        container_config = {'namespace': f'lab-{self.owner}', 'environment': 'sandbox', 'assets': '/srv/lab/assets',
                            'fixture_events_url': 'http://model:8000/events'}
        if self.native_fixture:
            from .native_scenarios import native_configuration
            container_config['native']=native_configuration('effects-'+self.owner)
        host_config = dict(container_config)
        host_config['dependency_mode']='candidate' if self.candidate else 'released'
        if self.candidate:host_config['candidate_manifest']=str(self.candidate_manifest.resolve())
        if self.capacity_policy is not None:
            container_config['capacity']=host_config['capacity']=self.capacity_policy
        if self.observability:
            container_config['metrics_token']=host_config['metrics_token']=secrets.token_hex(32)
        host_config['migration_dsn'] = f'host=127.0.0.1 port={port} dbname=lab user=lab_migration password={credentials["lab_migration"]}'
        host_config['fixture_manifest'] = str(self.directory / 'ownership.json')
        if self.billing:
            host_config['billing_dsn'] = f'host=127.0.0.1 port={port} dbname=lab user=billing_exporter password={credentials["billing_exporter"]}'
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
            self.baseline_image or self.manifest['images']['consumer'], 'python', 'scripts/provision.py')
        command(self.engine, 'start', '-a', provision)
        if self.native_fixture:
            from .native_scenarios import provision_effects
            provision_effects(host_config['migration_dsn'])
        runtime_name = name+'-runtime-config'
        runtime_volume = self._create('volume',runtime_name,'volume','create','--label',
            f'io.prosaic.lab.owner={self.owner}',runtime_name)
        delivery_name = name+'-deliver-config'
        self._secret('delivery-controls.json','{}')
        ca_mount = ['-v',f'{self.secrets / "issuer-ca.pem"}:/run/source/issuer-ca.pem:ro'] if self.identity else []
        delivery = self._create('container',delivery_name,'create','--name',delivery_name,'--label',
            f'io.prosaic.lab.owner={self.owner}','--network','none','--user','0','--read-only',
            '--cap-drop','ALL','--cap-add','CHOWN','--cap-add','DAC_OVERRIDE',
            '--security-opt','no-new-privileges','--memory','128m','--pids-limit','32',
            '-e','LAB_TEST_DELIVERY_CONTROLS=/run/source/delivery-controls.json',
            '-v',f'{self.secrets / "delivery-controls.json"}:/run/source/delivery-controls.json:ro',
            '-v',f'{self.secrets / "service.json"}:/run/secrets/service.json:ro',
            '-v',f'{runtime_volume}:/run/runtime',*ca_mount,self.manifest['images']['consumer'],
            'python','-m','lab_runner.secret_delivery')
        command(self.engine,'start','-a',delivery)
        self.manifest['runtime_config_volume'] = runtime_volume
        self.manifest['runtime_config_job'] = delivery
        self._save()
        return self.manifest

    def start_replica(self, name,*,image=None):
        if image is not None and image not in {self.manifest['images']['consumer'],self.manifest['images'].get('baseline')}:
            raise ValueError('unverified replica image')
        replica_name = f'prosaic-lab-{self.owner}-replica-{name}'
        identifier = self._create('container', replica_name, 'run', '-d', '--name', replica_name, '--label',
            f'io.prosaic.lab.owner={self.owner}', '--network', self.manifest['network_id'],
            '--user','10001:10001','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--memory','512m','--cpus','2','--pids-limit','128',
            '--tmpfs','/tmp:rw,noexec,nosuid,size=64m,mode=1777',
            '-p', '127.0.0.1::8080', '-v', f'{self.manifest["runtime_config_volume"]}:/run/secrets:ro',
            '-e', 'LAB_CONFIG=/run/secrets/service.json', image or self.manifest['images']['consumer'],
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
        # Acceptance and recovery subprocesses can register fresh workers. The
        # durable inventory is authoritative; never overwrite it with this
        # process's older snapshot or omit its still-attached resources.
        current=json.loads((self.directory/'ownership.json').read_text())
        resources=current.get('resources') if type(current) is dict else None
        if (type(current) is not dict or current.get('owner')!=self.owner or
            current.get('engine')!=self.engine or type(resources) is not list or
            any(type(item) is not dict or set(item)!={'kind','id'} or
                item['kind'] not in {'container','volume','network'} or
                type(item['id']) is not str or not item['id'] for item in resources) or
            any(item not in resources for item in self.manifest['resources'])):
            raise ValueError('durable resource ownership mismatch; refusing mutation')
        pending=current.get('pending_resources',[])
        if (type(pending) is not list or any(type(item) is not dict or set(item)!={'kind','name'} or
            item['kind'] not in {'container','volume','network'} or
            type(item['name']) is not str or not item['name'] for item in pending)):
            raise ValueError('invalid durable resource intention; refusing mutation')
        self.manifest=current
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
