from types import SimpleNamespace
import pytest
from lab_runner import stack

def test_failed_engine_command_keeps_phase_code_and_category_without_raw_stderr(monkeypatch):
    monkeypatch.setattr(stack.subprocess,'run',lambda *args,**kwargs:SimpleNamespace(
        returncode=1,stdout='',stderr='PRIVATE password=PRIVATE rate limit exceeded'))
    with pytest.raises(stack.EngineError) as caught:
        stack.command('docker','pull','PRIVATE')
    assert caught.value.diagnostic == {'operation':'pull','return_code':1,'category':'rate_limited','outcome':'unknown'}
    assert 'PRIVATE' not in str(caught.value) and 'PRIVATE' not in str(caught.value.diagnostic)
