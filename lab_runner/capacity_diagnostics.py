"""Closed synthetic observations for diagnosis; never qualification authority."""
import errno
import json
import math
import os
from pathlib import Path
import stat
import tempfile

MAX_BYTES=8192
FLAGS={'qualified','fixture_passed','correctness_passed','fairness_passed','accounting_reconciled'}
COUNTS={'offered','accepted','completed','errors','rejected','approval_deferred','client_shed',
    'independent_model_calls','ledger_calls','unknown_usage','starved_windows','read_failures',
    'read_samples','window_samples','tool_samples','allowance_rejected'}
FIELDS={'status','version','flags','counts','p95_seconds','tool_latency_p95_s','growth','elapsed_s','stop_bound'}


def unavailable(reason):
    return {'status':'unavailable','reason':reason}


def bounded_number(value,maximum):
    return type(value) in {int,float} and 0<=value<=maximum and math.isfinite(value)


def sanitize(value):
    """Reject extended/malformed documents rather than copying arbitrary values."""
    if type(value) is not dict:return unavailable('invalid')
    if (set(value)=={'status','reason'} and value.get('status')=='unavailable' and
        type(value.get('reason')) is str and value['reason'] in {'missing','invalid','unreadable'}):
        return dict(value)
    if (set(value)!=FIELDS or value.get('status')!='available' or type(value.get('version')) is not int or value['version']!=1 or
        type(value.get('flags')) is not dict or set(value['flags'])!=FLAGS or
        any(type(v) is not bool for v in value['flags'].values()) or
        type(value.get('counts')) is not dict or set(value['counts'])!=COUNTS or
        any(type(v) is not int or not 0<=v<=10000 for v in value['counts'].values()) or
        type(value.get('growth')) is not dict or set(value['growth'])!={'records_delta','bytes_delta'} or
        any(type(v) is not int or not -(2**63-1)<=v<=2**63-1 for v in value['growth'].values()) or
        type(value.get('stop_bound')) is not str or value['stop_bound'] not in {'duration','calls','records','unknown'} or
        value.get('elapsed_s') is not None and not bounded_number(value['elapsed_s'],7200) or
        any(value.get(key) is not None and not bounded_number(value[key],maximum)
            for key,maximum in (('p95_seconds',7200),('tool_latency_p95_s',30)))):
        return unavailable('invalid')
    return json.loads(json.dumps(value,allow_nan=False))


def project(result):
    """Select measured public scalars; discard identities and arbitrary context."""
    try:
        value={'status':'available','version':1,
            'flags':{key:result[key] for key in FLAGS},'counts':dict(result['counts']),
            'growth':{name+'_delta':result['growth'][name+'_after']-result['growth'][name+'_before']
                for name in ('records','bytes')},
            **{key:result[key] for key in ('p95_seconds','tool_latency_p95_s','elapsed_s','stop_bound')}}
        return sanitize(value)
    except (KeyError,TypeError,ValueError,OverflowError):return unavailable('invalid')


def write(directory,result):
    """Write only the closed projection inside this run's owned report directory."""
    report=Path(directory)/'report'
    temporary=None
    try:
        if report.is_symlink():return
        report.mkdir(mode=0o700,parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=report,
                prefix='.capacity-',delete=False) as output:
            temporary=Path(output.name)
            json.dump(project(result),output,allow_nan=False)
            output.write('\n')
        temporary.replace(report/'capacity-diagnostic.json')
    except (OSError,ValueError,TypeError,OverflowError,RecursionError):
        # Diagnostic persistence is best-effort; the original assertions decide.
        return
    finally:
        if temporary is not None:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass


def read(directory):
    """Read one bounded regular owned report; every failure returns a closed code."""
    report=Path(directory)/'report'
    try:
        if report.is_symlink():return unavailable('invalid')
        descriptor=os.open(report/'capacity-diagnostic.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    except FileNotFoundError:return unavailable('missing')
    except OSError as error:return unavailable('invalid' if error.errno==errno.ELOOP else 'unreadable')
    try:
        with os.fdopen(descriptor,'rb') as source:
            info=os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size>MAX_BYTES:return unavailable('invalid')
            document=source.read(MAX_BYTES+1)
        if len(document)>MAX_BYTES:return unavailable('invalid')
        return sanitize(json.loads(document))
    except (ValueError,TypeError,OverflowError,UnicodeError,RecursionError):return unavailable('invalid')
    except OSError:return unavailable('unreadable')
