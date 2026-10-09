"""Private archive copies; never delete idempotency, uncertainty or SDK evidence."""
import hashlib
import json
import os
from pathlib import Path
import stat
import logging
from prosaic_harness import RunNotFound
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime_postgres import PostgresRecorder
from .metadata import Metadata

def classification(reservation,state,report):
    if reservation['phase']!='started' or state is None: return 'retain_uncertain'
    if (state.get('status') not in {'completed','rejected'} or any(report.get(name,0)>0 for name in (
        'unresolved_calls','quarantined_calls','unsupported_calls','partial_calls','unavailable_assessment_calls'))):
        return 'retain_unresolved'
    return 'terminal_copy'

def read_config(path):
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(descriptor,'r') as source:
        info=os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_mode & 0o077 or info.st_size>1048576:
            raise ValueError('private operator config required')
        config=json.load(source)
    if not {'app_dsn','harness_dsn','accounting_dsn','namespace','environment'} <= set(config):
        raise ValueError('operator config incomplete')
    return config

def scan(config,destination=None):
    metadata=Metadata(config['app_dsn'])
    store=PostgresRunStore(config['harness_dsn'],namespace=config['namespace'],max_active_leases=1,
        operation_timeout_s=5,pool_timeout_s=2,connect_timeout_s=3,lock_timeout_s=1,statement_timeout_s=3)
    recorder=PostgresRecorder(config['accounting_dsn'],namespace=config['namespace'],environment=config['environment'])
    result={'rows':0,'retain_uncertain':0,'retain_unresolved':0,'terminal_copy':0,
        'deletion_allowed':False,'point_in_time_backup':False,'archive_complete':False}
    output=None; target=None; digest=hashlib.sha256()
    try:
        if destination is not None:
            target=Path(destination)
            target.mkdir(mode=0o700,parents=False,exist_ok=False)
            output=os.fdopen(os.open(target/'records.jsonl.partial',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb')
        after=''
        while True:
            page=metadata.retention_page(config['namespace'],config['environment'],after)
            if not page: break
            for reservation in page:
                if result['rows']>=10000: raise ValueError('archive exceeds qualified pilot capacity')
                try:
                    snapshot=store.load_run(reservation['run_id'])
                    state=snapshot.state
                    revision=snapshot.revision
                except RunNotFound:
                    state=revision=None
                calls=recorder.calls(run_id=reservation['run_id'])
                report=recorder.report(run_id=reservation['run_id'])
                category=classification(reservation,state,report)
                record={'reservation':reservation,'state':state,'revision':revision,'calls':calls,
                    'usage':report,'classification':category}
                content=(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
                digest.update(content)
                if output is not None: output.write(content)
                result['rows']+=1; result[category]+=1
                after=reservation['run_id']
        if output is not None:
            output.flush(); os.fsync(output.fileno()); output.close(); output=None
            (target/'records.jsonl.partial').rename(target/'records.jsonl')
            result['archive_complete']=True
            result['records_sha256']=digest.hexdigest()
            descriptor=os.open(target/'summary.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(descriptor,'w') as summary:
                json.dump(result,summary,sort_keys=True); summary.write('\n'); summary.flush(); os.fsync(summary.fileno())
            descriptor=os.open(target,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try: os.fsync(descriptor)
            finally: os.close(descriptor)
        return result
    finally:
        if output is not None: output.close()
        store.close()

def cli(args):
    previous=logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        if not args.config or bool(args.archive)!=bool(args.destination): raise ValueError('invalid retention request')
        config=read_config(args.config)
        print(json.dumps(scan(config,args.destination if args.archive else None)))
        return 0
    except Exception:
        print(json.dumps({'event':'retention_failed','deletion_allowed':False}))
        return 1
    finally: logging.disable(previous)
