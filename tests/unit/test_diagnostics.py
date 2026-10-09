import pytest
from prosaic_integration_lab.diagnostics import stage


def test_stage_failure_logs_class_without_private_exception_text(caplog):
    with pytest.raises(ValueError):
        with stage('reserve'):
            raise ValueError('PRIVATE_PROMPT_AND_PASSWORD')
    assert 'reserve' in caplog.text and 'ValueError' in caplog.text
    assert 'PRIVATE_PROMPT_AND_PASSWORD' not in caplog.text


def test_arbitrary_exception_attributes_are_not_trusted_log_fields(caplog):
    error = ValueError('private message')
    error.code = 'private_access_token'
    error.sqlstate = 'TOKEN'
    with pytest.raises(ValueError):
        with stage('reserve'):
            raise error
    assert 'private_access_token' not in caplog.text
    assert 'TOKEN' not in caplog.text
