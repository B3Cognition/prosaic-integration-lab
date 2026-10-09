import subprocess
import sys

def test_stress_rejects_unbounded_arrival_profile_before_engine_operations():
    result=subprocess.run([sys.executable,'-m','lab_runner','stress','--duration','300','--rate','100'],capture_output=True,text=True)
    assert result.returncode==2
    assert 'bounded qualification policy' in result.stderr
