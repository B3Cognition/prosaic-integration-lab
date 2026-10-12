"""Retain useful owned synthetic metrics without exporting private driver data."""
import json
import sys
from types import SimpleNamespace

import pytest


def evaluated(*,qualified=False):
    return {
        'qualified':qualified,'fixture_passed':True,'correctness_passed':True,
        'fairness_passed':qualified,'accounting_reconciled':True,
        'counts':{'offered':18,'accepted':18,'completed':18,'errors':0,'rejected':0,
            'approval_deferred':0,'client_shed':0,'independent_model_calls':18,
            'ledger_calls':18,'unknown_usage':0,'starved_windows':0 if qualified else 1,
            'read_failures':0,'read_samples':18,'window_samples':2,'tool_samples':18,
            'allowance_rejected':0},
        'p95_seconds':.75,'tool_latency_p95_s':.01,
        'growth':{'records_before':7,'records_after':25,'bytes_before':1000,'bytes_after':3000},
        'elapsed_s':6.25,'stop_bound':'duration',
        'tenant_completion_ratios':{'PRIVATE_TENANT':1},'profile_sha256':'PRIVATE_HASH',
        'config':'PRIVATE_DSN','prompt':'PRIVATE_PROMPT',
    }


@pytest.mark.parametrize('qualified',[False,True])
def test_owned_projection_retains_pass_and_failure_metrics_without_private_fields(tmp_path,qualified):
    from lab_runner.capacity_diagnostics import write,read
    write(tmp_path,evaluated(qualified=qualified))
    diagnostic=read(tmp_path)
    assert diagnostic['status']=='available' and diagnostic['version']==1
    assert diagnostic['flags']['qualified'] is qualified
    assert diagnostic['flags']['fairness_passed'] is qualified
    assert diagnostic['counts']['offered']==18 and diagnostic['counts']['starved_windows']==(0 if qualified else 1)
    assert diagnostic['growth']=={'records_delta':18,'bytes_delta':2000}
    assert diagnostic['p95_seconds']==.75 and diagnostic['elapsed_s']==6.25
    assert 'PRIVATE' not in json.dumps(diagnostic)
    assert 'PRIVATE' not in (tmp_path/'report/capacity-diagnostic.json').read_text()


@pytest.mark.parametrize('mutation',[
    lambda d:d.update(extra='PRIVATE_SECRET'),
    lambda d:d['flags'].update(extra='PRIVATE_SECRET'),
    lambda d:d['counts'].update(extra='PRIVATE_SECRET'),
    lambda d:d['counts'].update(errors=True),
    lambda d:d['counts'].update(errors=10001),
    lambda d:d.update(p95_seconds=float('nan')),
    lambda d:d.update(tool_latency_p95_s=float('inf')),
    lambda d:d.update(elapsed_s=-1),
    lambda d:d.update(stop_bound='PRIVATE_STOP'),
    lambda d:d['growth'].update(records_delta=-(2**63)),
    lambda d:d.update(status='PRIVATE_STATUS'),
    lambda d:d.update(stop_bound=['PRIVATE_STOP']),
    lambda d:d.update(p95_seconds=False),
])
def test_malformed_or_extended_on_disk_diagnostic_is_closed_and_does_not_leak(tmp_path,mutation):
    from lab_runner.capacity_diagnostics import write,read
    write(tmp_path,evaluated())
    path=tmp_path/'report/capacity-diagnostic.json'
    value=json.loads(path.read_text());mutation(value);path.write_text(json.dumps(value))
    assert read(tmp_path)=={'status':'unavailable','reason':'invalid'}


def test_missing_oversized_and_symlinked_reports_never_read_external_private_data(tmp_path):
    from lab_runner.capacity_diagnostics import read
    assert read(tmp_path)=={'status':'unavailable','reason':'missing'}
    report=tmp_path/'report';report.mkdir();path=report/'capacity-diagnostic.json'
    path.write_text('PRIVATE_SECRET'*1000)
    assert read(tmp_path)=={'status':'unavailable','reason':'invalid'}
    path.unlink();outside=tmp_path/'private.json';outside.write_text('PRIVATE_SECRET');path.symlink_to(outside)
    assert read(tmp_path)=={'status':'unavailable','reason':'invalid'}
    path.unlink();path.write_text('['*2000+']'*2000)
    assert read(tmp_path)=={'status':'unavailable','reason':'invalid'}
    path.unlink();__import__('os').mkfifo(path)
    assert read(tmp_path)=={'status':'unavailable','reason':'invalid'}


def test_failed_measurements_retain_null_latencies_unknown_stop_and_signed_growth(tmp_path):
    from lab_runner.capacity_diagnostics import write,read
    value=evaluated();value.update(p95_seconds=None,tool_latency_p95_s=None,elapsed_s=None,stop_bound='unknown')
    value['growth'].update(records_after=6,bytes_after=900)
    write(tmp_path,value)
    diagnostic=read(tmp_path)
    assert diagnostic['status']=='available' and diagnostic['stop_bound']=='unknown'
    assert diagnostic['p95_seconds'] is None and diagnostic['tool_latency_p95_s'] is None
    assert diagnostic['growth']=={'records_delta':-1,'bytes_delta':-100}


def test_diagnostic_io_failure_is_best_effort_and_never_exposes_exception_text(tmp_path,monkeypatch):
    import os
    from lab_runner.capacity_diagnostics import write,read
    (tmp_path/'report').write_text('PRIVATE_SECRET')
    write(tmp_path,evaluated())
    def denied(*args,**kwargs):raise PermissionError('PRIVATE_DSN')
    monkeypatch.setattr(os,'open',denied)
    assert read(tmp_path)=={'status':'unavailable','reason':'unreadable'}


def test_gate_exports_diagnostic_only_for_qualification_and_does_not_admit_success(tmp_path):
    from lab_runner.capacity_diagnostics import write,read
    from lab_runner.gates import export,validate
    from test_release_gates import receipt
    write(tmp_path,evaluated(qualified=True));diagnostic=read(tmp_path)
    item=receipt();item.update(mode='qualification',test_count=3,passed=False,test_returncode=1,
        failed_tests=['test_real_fairness_reads_growth_and_usage_are_measured'],capacity_diagnostic=diagnostic)
    safe=export(item)
    assert safe['capacity_diagnostic']['flags']['qualified'] is True
    assert safe['passed'] is False
    with pytest.raises(ValueError):validate(item,'qualification',16)
    item['capacity_diagnostic']['config']='PRIVATE_DSN'
    assert export(item)['capacity_diagnostic']=={'status':'unavailable','reason':'invalid'}
    item['mode']='audit'
    assert 'capacity_diagnostic' not in export(item)
    assert 'PRIVATE' not in json.dumps(export(item))


@pytest.mark.parametrize('passed,malformed',[(False,False),(True,True)])
def test_runner_reads_before_cleanup_and_report_never_changes_test_result(tmp_path,monkeypatch,passed,malformed):
    from lab_runner import __main__ as cli
    from lab_runner.capacity_diagnostics import write
    class Stack:
        def __init__(self,*args,**kwargs):
            self.owner='a'*32;self.directory=tmp_path;self.secrets=tmp_path/'secrets';self.secrets.mkdir()
            (self.secrets/'host.json').write_text('{}')
            self.baseline_image=None;self.manifest={'endpoints':{},'images':{},'payload_audit':'verified'}
        def start(self):pass
        def start_model(self):pass
        def start_replica(self,*args,**kwargs):pass
        def stop(self):(tmp_path/'report/capacity-diagnostic.json').unlink()
    def external_pytest(arguments,**kwargs):
        assert arguments[1:3]==['-m','pytest']
        write(tmp_path,evaluated(qualified=True))
        if malformed:(tmp_path/'report/capacity-diagnostic.json').write_text('PRIVATE_DSN')
        failure='' if passed else '<failure>PRIVATE_DSN</failure>'
        (tmp_path/'junit.xml').write_text('<testsuites><testsuite><testcase name="test_real_fairness_reads_growth_and_usage_are_measured">'+
            failure+'</testcase><testcase name="restore_legacy"/><testcase name="restore_native"/></testsuite></testsuites>')
        return SimpleNamespace(returncode=0 if passed else 1)
    monkeypatch.setattr(cli,'OwnedStack',Stack)
    monkeypatch.setattr(cli.subprocess,'run',external_pytest)
    monkeypatch.setattr(sys,'argv',['lab_runner','test','--mode','qualification'])
    assert cli.main()==(0 if passed else 1)
    result=json.loads((tmp_path/'result.json').read_text())
    assert result['passed'] is passed and result['cleanup']=='verified' and result['test_count']==3
    if malformed:assert result['capacity_diagnostic']=={'status':'unavailable','reason':'invalid'}
    else:assert result['capacity_diagnostic']['status']=='available'
    assert 'PRIVATE' not in json.dumps(result)
