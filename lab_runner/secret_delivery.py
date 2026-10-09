"""One-shot root provisioning into an owned, private runtime credential volume."""
import json
import os
from pathlib import Path

def read_runtime_config(source):
    data = json.loads(Path(source).read_text())
    required = {'namespace','environment','assets','harness_dsn','accounting_dsn','app_dsn'}
    if not isinstance(data,dict) or not required <= set(data) or set(data)-required-{'principals','fixture_events_url','http_bounds','authentication','deployment_mode'}:
        raise ValueError('invalid runtime config')
    return data

def install(source,target):
    data = read_runtime_config(source)
    target = Path(target)
    parent = target.parent.stat()
    initial = parent.st_uid == 0
    if not initial and (parent.st_uid != 10001 or parent.st_gid != 10001 or parent.st_mode & 0o777 != 0o700):
        raise ValueError('invalid runtime credential directory')
    if data.get('authentication',{}).get('ca_file') == '/run/secrets/issuer-ca.pem':
        certificate = Path('/run/source/issuer-ca.pem').read_text()
        pending_ca = target.parent/'issuer-ca.next'
        descriptor = os.open(pending_ca,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
        try:
            with os.fdopen(descriptor,'w') as output:
                output.write(certificate)
                output.flush()
                os.fchmod(output.fileno(),0o400)
                os.fchown(output.fileno(),10001,10001)
            os.replace(pending_ca,target.parent/'issuer-ca.pem')
        finally:
            pending_ca.unlink(missing_ok=True)
    temporary = target.with_suffix('.next')
    descriptor = os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
    try:
        with os.fdopen(descriptor,'w') as output:
            json.dump(data,output)
            output.flush()
            os.fsync(output.fileno())
            os.fchmod(output.fileno(),0o400)
            os.fchown(output.fileno(),10001,10001)
        os.replace(temporary,target)
        if initial:
            os.chmod(target.parent,0o700)
            os.chown(target.parent,10001,10001)
    finally:
        temporary.unlink(missing_ok=True)

if __name__ == '__main__':
    install('/run/secrets/service.json','/run/runtime/service.json')
