import subprocess
import sys

def test_ingress_lane_cannot_be_used_as_unreviewed_workload_mode():
    result = subprocess.run([sys.executable,'-m','lab_runner','demo','--mode','ingress'],
        capture_output=True,text=True)
    assert result.returncode == 2
    assert 'ingress mode requires test' in result.stderr
