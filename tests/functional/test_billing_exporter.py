import json
import os
import subprocess
import sys


def test_exporter_reports_only_sanitized_failure(tmp_path):
    config = tmp_path/'config.json'
    config.write_text(json.dumps({'billing_dsn':'private-dsn-sentinel','lago':{'key':'private-key-sentinel'}}))
    r = subprocess.run([sys.executable,'-m','prosaic_integration_lab.billing_exporter','--config',str(config)],
        env={**os.environ,'PYTHONPATH':'src'},capture_output=True,text=True)
    assert r.returncode == 1
    assert r.stdout.strip() == '{"event": "billing_export_failed"}'
    assert 'private-' not in r.stdout+r.stderr
