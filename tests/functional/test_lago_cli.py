import subprocess
import sys


def test_lago_mode_is_explicit_and_requires_test():
    result = subprocess.run([sys.executable,'-m','lab_runner','demo','--mode','lago'],capture_output=True,text=True)
    assert result.returncode == 2
    assert 'lago mode requires test' in result.stderr


def test_lago_host_loading_without_editable_consumer():
    result = subprocess.run([sys.executable,'-c',
        'from lab_runner.__main__ import load_lago; assert callable(load_lago())'],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
