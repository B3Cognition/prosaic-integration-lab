import os
import subprocess
import sys
from pathlib import Path

def test_missing_operator_dsn_fails_without_secret_echo():
    environment = {key:value for key,value in os.environ.items() if key != 'LAB_OPERATOR_DSN'}
    environment['PYTHONPATH'] = str(Path(__file__).resolve().parents[2]/'src')
    response = subprocess.run([sys.executable,'-m','prosaic_integration_lab.migrations',
        '--dsn-env','LAB_OPERATOR_DSN'],env=environment,capture_output=True,text=True)
    assert response.returncode != 0
    assert response.stdout.strip() == '{"event": "migration_failed", "category": "ValueError"}'
    assert response.stderr == ''
