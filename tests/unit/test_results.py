import pytest
from lab_runner.results import sanitize_junit


def test_junit_exports_status_without_driver_errors_or_captured_logs(tmp_path):
    path = tmp_path / 'junit.xml'
    path.write_text('''<testsuites><testsuite><system-out>PRIVATE_KEY</system-out>
        <testcase name="passed" classname="tests" time="1"/>
        <testcase name="failed"><failure message="PRIVATE_KEY">PRIVATE_DSN</failure>
          <system-err>PRIVATE_PROMPT</system-err></testcase>
        <testcase name="skipped"><skipped message="PRIVATE_KEY"/></testcase>
        </testsuite></testsuites>''')
    result = sanitize_junit(path)
    assert result == {'test_count': 3, 'skipped': 1, 'failed_tests': ['failed']}
    assert 'PRIVATE_' not in path.read_text()
    assert 'failed' in path.read_text()


def test_incomplete_junit_is_removed_instead_of_exporting_raw_partial_text(tmp_path):
    path = tmp_path / 'junit.xml'
    path.write_text('<testsuite>PRIVATE_KEY')
    with pytest.raises(ValueError, match='incomplete'):
        sanitize_junit(path)
    assert not path.exists()
