import os
import subprocess
import sys

def test_terminal_recovery_rejects_plaintext_external_origin_without_echoing_token():
    response = subprocess.run([sys.executable,'-m','lab_runner','recover','--url','http://untrusted.example',
        '--run-id','a'*32,'--action','inspect','--token-env','LAB_FIXTURE_TOKEN'],
        env={**os.environ,'LAB_FIXTURE_TOKEN':'PRIVATE_FIXTURE_TOKEN'},capture_output=True,text=True)
    assert response.returncode != 0
    assert 'PRIVATE_FIXTURE_TOKEN' not in response.stdout+response.stderr
    assert response.stdout.strip() == '{"event": "recovery_failed", "reason": "https_required"}'
