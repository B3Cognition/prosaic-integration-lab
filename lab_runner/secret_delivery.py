"""One-shot root provisioning into an owned, private runtime credential volume."""
import json
import os
from pathlib import Path
import uuid
import stat

RUNTIME_UID = 10001
RUNTIME_GID = 10001
MAX_GENERATIONS = 64

def read_runtime_config(source):
    data = json.loads(Path(source).read_text())
    required = {'namespace','environment','assets','harness_dsn','accounting_dsn','app_dsn'}
    if not isinstance(data,dict) or not required <= set(data) or set(data)-required-{'principals','fixture_events_url','http_bounds','authentication','deployment_mode','metrics_token','capacity','native','legacy_bundles'}:
        raise ValueError('invalid runtime config')
    return data

def private_file(path,content):
    descriptor = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
    with os.fdopen(descriptor,'w') as output:
        output.write(content)
        output.flush()
        os.fchmod(output.fileno(),0o400)
        os.fchown(output.fileno(),RUNTIME_UID,RUNTIME_GID)
        os.fsync(output.fileno())

def sync_directory(path):
    descriptor = os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)

def install(source,target,*,checkpoint=lambda stage:None):
    data = read_runtime_config(source)
    target = Path(target)
    parent = target.parent.stat()
    initial = parent.st_uid == 0
    if not initial and (parent.st_uid != RUNTIME_UID or parent.st_gid != RUNTIME_GID or parent.st_mode & 0o777 != 0o700):
        raise ValueError('invalid runtime credential directory')
    generations = target.parent/'generations'
    if not generations.exists():
        generations.mkdir(mode=0o700)
        os.chown(generations,RUNTIME_UID,RUNTIME_GID)
    state = generations.lstat()
    if not stat.S_ISDIR(state.st_mode) or state.st_uid != RUNTIME_UID or state.st_mode & 0o777 != 0o700:
        raise ValueError('invalid runtime generation directory')
    for count,_ in enumerate(generations.iterdir(),1):
        if count>=MAX_GENERATIONS:
            raise ValueError('runtime generation capacity requires reviewed retirement')
    generation = uuid.uuid4().hex
    directory = generations/generation
    directory.mkdir(mode=0o700)
    if data.get('authentication',{}).get('ca_file') == '/run/secrets/issuer-ca.pem':
        certificate = Path('/run/source/issuer-ca.pem').read_text()
        private_file(directory/'issuer-ca.pem',certificate)
        data['authentication'] = {**data['authentication'],
            'ca_file':f'/run/secrets/generations/{generation}/issuer-ca.pem'}
        checkpoint('after_ca')
    private_file(directory/'service.json',json.dumps(data))
    os.chown(directory,RUNTIME_UID,RUNTIME_GID)
    sync_directory(directory)
    sync_directory(generations)
    if initial:
        os.chmod(target.parent,0o700)
        os.chown(target.parent,RUNTIME_UID,RUNTIME_GID)
    checkpoint('before_publish')
    temporary = target.parent/('current-next-'+generation)
    try:
        os.symlink(f'generations/{generation}/service.json',temporary)
        os.replace(temporary,target)
        sync_directory(target.parent)
    finally:
        temporary.unlink(missing_ok=True)
    return generation

def fixture_checkpoint(stage):
    path = os.environ.get('LAB_TEST_DELIVERY_CONTROLS')
    if path:
        controls = json.loads(Path(path).read_text())
        if controls.get('failpoint') == stage:
            os._exit(17)  # Owned test-only abrupt process loss before publication.

if __name__ == '__main__':
    install('/run/secrets/service.json','/run/runtime/service.json',checkpoint=fixture_checkpoint)
