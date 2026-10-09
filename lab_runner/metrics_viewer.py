"""Protected terminal metrics; never print an arbitrary HTTP response body."""
import json
import math
import os
import re
import ssl
import time
from urllib.parse import urlsplit
import httpx

LABELS={'route':{'healthz','readyz','runs_start','run_status','run_resume','run_usage','unknown'},
    'status':{'1xx','2xx','3xx','4xx','5xx','other'},'pool':{'writes','reads'},
    'phase':{'reserved','starting','started'},'le':{'0.01','0.05','0.1','0.5','1','2','5','10','30','+Inf'}}
SCHEMA={name:set() for name in ('lab_readiness','lab_readiness_failures_total',
    'lab_accounting_unknown_observations_total','lab_reservation_snapshot_success')}
SCHEMA.update({'lab_admission_active':{'pool'},'lab_admission_rejections_total':{'pool'},
    'lab_reservation_phase':{'phase'},'lab_http_requests_total':{'route','status'},
    'lab_http_duration_seconds_bucket':{'route','le'},'lab_http_duration_seconds_sum':{'route'},
    'lab_http_duration_seconds_count':{'route'}})

def safe_metrics(text):
    if len(text.encode())>32768: raise ValueError('metrics unavailable')
    lines=text.splitlines()
    if len(lines)>512: raise ValueError('metrics unavailable')
    result=[]
    for line in lines:
        match=re.fullmatch(r'([a-z_]+)(?:\{([^}]{1,256})\})? ([0-9.eE+-]{1,32})',line)
        if not match or match[1] not in SCHEMA: raise ValueError('metrics unavailable')
        number=float(match[3])
        if not math.isfinite(number) or not 0 <= number <= 1e18: raise ValueError('metrics unavailable')
        labels={}
        for pair in (match[2] or '').split(',') if match[2] else []:
            label=re.fullmatch(r'([a-z_]+)="([a-zA-Z0-9_.+]+)"',pair)
            if not label or label[1] in labels or label[1] not in LABELS or label[2] not in LABELS[label[1]]:
                raise ValueError('metrics unavailable')
            labels[label[1]]=label[2]
        if set(labels)!=SCHEMA[match[1]]: raise ValueError('metrics unavailable')
        result.append(line)
    if not result: raise ValueError('metrics unavailable')
    return '\n'.join(result)+'\n'

def cli(args):
    try:
        parsed=urlsplit(args.url or '')
        if (parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password or
            parsed.query or parsed.fragment or parsed.path not in {'','/'} or
            (parsed.scheme=='http' and (not args.lab_http or parsed.hostname not in {'127.0.0.1','localhost','::1'}))):
            raise ValueError('metrics unavailable')
        if not 1 <= args.samples <= 1000 or not math.isfinite(args.interval) or not .1 <= args.interval <= 5:
            raise ValueError('metrics unavailable')
        token=os.environ.get(args.token_env)
        if not token: raise ValueError('metrics unavailable')
        with httpx.Client(verify=ssl.create_default_context(cafile=args.ca_file),trust_env=False,
            follow_redirects=False,timeout=10,headers={'Authorization':'Bearer '+token}) as client:
            for index in range(args.samples):
                with client.stream('GET',args.url.rstrip('/')+'/metrics') as response:
                    if response.status_code!=200:
                        print(json.dumps({'event':'metrics_failed','status':response.status_code})); return 1
                    content=bytearray()
                    for chunk in response.iter_bytes():
                        if len(content)+len(chunk)>32768: raise ValueError('metrics unavailable')
                        content.extend(chunk)
                print(safe_metrics(content.decode()),end='',flush=True)
                if index+1<args.samples: time.sleep(args.interval)
        return 0
    except KeyboardInterrupt: return 0
    except (ValueError,OSError,httpx.HTTPError):
        print(json.dumps({'event':'metrics_failed'})); return 1
