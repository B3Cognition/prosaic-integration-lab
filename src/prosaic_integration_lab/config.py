import hashlib
import json
import os
from pathlib import Path

def load_config():
    config = json.loads(Path(os.environ['LAB_CONFIG']).read_text())
    required = {'namespace', 'environment', 'assets', 'principals', 'harness_dsn', 'accounting_dsn', 'app_dsn'}
    if not required <= set(config) or set(config) - required - {'fixture_events_url'} or config['environment'] != 'sandbox':
        raise ValueError('invalid lab configuration')
    return config

def assets_hash(directory):
    digest = hashlib.sha256()
    for path in sorted(Path(directory).rglob('*')):
        if path.is_file():
            digest.update(str(path.relative_to(directory)).encode())
            digest.update(b'\0')
            digest.update(path.read_bytes())
    return digest.hexdigest()
