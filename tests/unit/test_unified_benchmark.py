import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest


def test_repeated_plan_has_exact_rotated_coverage_and_bounded_authority():
    from lab_runner.native_eval.unified_benchmark import plan, schedule
    p = plan(3)
    assert p['assignments'] == 27 and p['maximumDispatchUnits'] == 243
    jobs = schedule(3)
    assert len(jobs) == len(set(jobs)) == 27
    assert jobs[0] == (1, 'release-brief', 'all-eligible')
    assert {j[2] for j in jobs} == {'all-eligible', 'claude-cooling', 'native-cooling'}
    assert jobs[9][1:] == ('incident-handoff', 'claude-cooling')
    for bad in (0, 4, True):
        with pytest.raises(ValueError): plan(bad)


def test_explicit_live_opt_in_precedes_files_or_dispatch(tmp_path):
    from lab_runner.native_eval.unified_benchmark import run_unified_benchmark
    with pytest.raises(ValueError, match='opt-in'):
        run_unified_benchmark(native_config=None, local_config=None,
            output=tmp_path/'run', provenance={})
    assert not (tmp_path/'run').exists()


@pytest.mark.parametrize('flags',[['--max-native-attempts','0'],['--selector','claude']])
def test_benchmark_cli_rejects_pilot_flags_instead_of_ignoring_authority(flags,capsys,monkeypatch):
    from lab_runner.native_eval.__main__ import main
    from lab_runner.native_eval import provenance
    def forbidden_audit(*args):raise AssertionError('incompatible authority reached candidate audit')
    monkeypatch.setattr(provenance,'audit_candidate',forbidden_audit)
    assert main(['unified-benchmark','--live','--manifest','unused','--wheel-dir','unused']+flags)==2
    assert json.loads(capsys.readouterr().err)=={'error':'native_eval_setup_failed'}


def test_summary_counts_fallback_attempts_and_skips_separately():
    from lab_runner.native_eval.unified_benchmark import summarize
    rows=[{'selector':'all-eligible','case':'invoice-sql','trial':1,'completed':True,
        'passed':True,'durationMs':1000,'selectedProfile':'codex','events':[
            {'event':'profile_fallback','profile':'claude'},
            {'event':'profile_skipped','profile':'local'}],
        'attempts':[{'profile':'claude'},{'profile':'codex'}]},
        {'selector':'all-eligible','case':'invoice-sql','trial':2,'completed':False,
        'passed':False,'durationMs':180000,'selectedProfile':'local','events':[],
        'attempts':[{'profile':'local'}],'failureReason':'timeout'}]
    r=summarize(rows)
    group=r['byAvailability'][0]
    assert group['successRate']==.5 and group['allLatencyMs']['median']==90500
    assert group['successfulLatencyMs']['median']==1000
    assert group['fallbackAssignments']==1 and group['profileSkips']==1
    assert group['selectedProfiles']=={'codex':1,'local':1}


def test_cli_failure_with_valid_file_is_not_success(tmp_path):
    from lab_runner.native_eval.unified_benchmark import evaluate
    from lab_runner.native_eval.realistic_cases import prepare
    prepare('invoice-sql',tmp_path)
    (tmp_path/'report.sql').write_text('WITH p AS (SELECT invoice_id,SUM(amount_cents) paid FROM payments GROUP BY invoice_id), '
        'b AS (SELECT i.customer_id,MAX(0,i.total_cents-COALESCE(p.paid,0)) balance FROM invoices i '
        "LEFT JOIN p ON p.invoice_id=i.id WHERE i.status='OPEN' AND i.due_date<'2026-10-23') "
        'SELECT customer_id,COUNT(*) overdue_count,SUM(balance) outstanding_cents FROM b '
        'WHERE balance>0 GROUP BY customer_id ORDER BY customer_id;')
    result={'exit_code':1,'timed_out':True,'metadata':{'failure_reason':'timeout'}}
    row=evaluate('invoice-sql',tmp_path,result)
    assert row['grade']['factualContract'] and not row['passed'] and not row['completed']
    assert row['failureReason']=='timeout'


def test_cli_command_preserves_deadlines_and_exact_output_grant(tmp_path):
    from lab_runner.native_eval.unified_benchmark import cli_command
    command=cli_command(tmp_path/'unified.json','invoice-sql',tmp_path)
    for flag,value in [('--timeout','300'),('--native-timeout','60'),('--api-timeout','180'),
                       ('--max-api-requests','8'),('--max-api-tool-calls','7'),
                       ('--write-path',str(tmp_path/'report.sql'))]:
        assert command[command.index(flag)+1]==value
    assert command.count('--write-path')==1 and '--enable-api' in command
    assert command[1:4]==['-I','-m','prosaic_runtime.cli']


def test_actual_cli_transport_filters_events_and_requires_terminal_exit_agreement():
    from lab_runner.native_eval.unified_benchmark import _invoke
    events=[{'event':'profile_selected','profile':'codex','command':'private command'},
            {'event':'result','exit_code':0,'metadata':{},'stdout':'done'}]
    command=[sys.executable,'-I','-c','import json;print('+repr('\n'.join(json.dumps(e) for e in events))+')']
    result,safe=_invoke(command)
    assert result['exit_code']==0 and safe==[{'event':'profile_selected','profile':'codex'}]
    with pytest.raises(RuntimeError,match='exit codes disagree'):
        _invoke(command[:-1]+[command[-1]+';raise SystemExit(1)'])
    with pytest.raises(RuntimeError,match='terminal result absent'):
        _invoke([sys.executable,'-I','-c','print("{}")'])


def test_exceptional_assignment_latency_is_measured():
    from lab_runner.native_eval.unified_benchmark import assignment_latency
    row={}
    with pytest.raises(RuntimeError):
        with assignment_latency(row):
            time.sleep(.02)
            raise RuntimeError('fixture terminal result absent')
    assert row['durationMs']>=20


def test_interrupt_cleans_owned_cli_before_returning(tmp_path):
    fixture=tmp_path/'fixture.py'; pidfile=tmp_path/'pid'; marker=tmp_path/'interrupted'
    fixture.write_text('import os,signal,time,sys\nfrom pathlib import Path\n'
        'def stop(*args):\n Path(sys.argv[2]).write_text("interrupted");raise SystemExit(130)\n'
        'signal.signal(signal.SIGINT,stop)\nPath(sys.argv[1]).write_text(str(os.getpid()))\ntime.sleep(30)\n')
    root=Path(__file__).resolve().parents[2]
    code=('import sys;sys.path[:0]='+repr([str(root),str(root/'src')])+'\n'
        'from lab_runner.native_eval.unified_benchmark import _invoke\n'
        'try:_invoke('+repr([sys.executable,'-I',str(fixture),str(pidfile),str(marker)])+')\n'
        'except KeyboardInterrupt:pass\n')
    parent=subprocess.Popen([sys.executable,'-I','-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        until=time.monotonic()+5
        while not pidfile.exists() and time.monotonic()<until:time.sleep(.01)
        assert pidfile.exists()
        parent.send_signal(signal.SIGINT)
        parent.communicate(timeout=5)
        assert marker.exists(), 'owned CLI was left running after benchmark interruption'
    finally:
        if parent.poll() is None:parent.kill();parent.communicate()
        if pidfile.exists():
            try:os.killpg(int(pidfile.read_text()),signal.SIGKILL)
            except ProcessLookupError:pass
