"""Trusted document-review CLI; inference is limited to a synthetic loopback fixture.

Copy configs/sue-review.example.json to an owned mode-600 file and explicitly
enable review. A start request contains seed, sources (sourceId plus an absolute
path, optional revision/reference), optional lens and max_turns. Start freezes
the exact UTF-8 files and pauses with zero calls. Inspect status, then resume
with its expected revision and --choice continue or reject. Reports are advisory.

Request example (paths are chosen by the operator, never the model):
{"seed":"What does this requirement imply?","sources":[{"sourceId":"spec",
 "path":"/absolute/spec.md","revision":"r1"}],"lens":"euthyphro","max_turns":14}

python -m lab_runner.sue_review start --config /private/host.json --request /private/request.json
python -m lab_runner.sue_review status --config /private/host.json --run-id RUN_ID
python -m lab_runner.sue_review resume --config /private/host.json --run-id RUN_ID --expected-revision REVISION --choice continue
python -m lab_runner.sue_review report --config /private/host.json --run-id RUN_ID --format markdown

Sources remain frozen after start; subsequent actions do not reopen the files.
Remove review enablement to prohibit inference while retaining status/report.
Only the host API supports selected Castle captures in this version.
"""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import stat
from urllib.parse import urlsplit
import uuid


def _read(path, maximum, *, private=False):
    """Open once without following a final symlink; inspect that same descriptor."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_size > maximum
                or private and (stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.getuid())):
            raise ValueError('invalid input file')
        with os.fdopen(fd, 'rb', closefd=False) as handle:
            data = handle.read(maximum+1)
        if len(data) > maximum:
            raise ValueError('input limit')
        return data.decode('utf-8')
    finally:
        os.close(fd)


def load_host(path):
    from prosaic_integration_lab.sue_review.contracts import decode, reference, ReviewSettings

    value = decode(_read(path, 65536, private=True), maximum=65536)
    required = {'namespace','principal','store','runtime'}
    if type(value) is not dict or not required <= set(value) or set(value)-required-{'review','accounting'}:
        raise ValueError('invalid host configuration')
    if not reference(value['namespace']):
        raise ValueError('invalid namespace')
    principal = value['principal']
    names = {'tenant_id','actor_id','billing_account_id'}
    if type(principal) is not dict or set(principal) != names or any(not reference(principal[n]) for n in names):
        raise ValueError('invalid principal')
    runtime = value['runtime']
    if (type(runtime) is not dict or set(runtime) != {'base_url','model'}
            or type(runtime['base_url']) is not str or runtime['model'] != 'sue-fixture'):
        raise ValueError('synthetic runtime required')
    url = urlsplit(runtime['base_url'])
    if (url.scheme != 'http' or url.hostname not in {'127.0.0.1','::1'} or not url.port
            or url.path != '/v1' or url.username or url.password or url.query or url.fragment):
        raise ValueError('synthetic loopback required')
    ReviewSettings.from_mapping(value.get('review'))
    if 'accounting' in value:
        spec = value['accounting']
        if type(spec) is not dict or set(spec) != {'dsn_env'} or not reference(spec['dsn_env']):
            raise ValueError('invalid accounting binding')
    return value


def load_request(path):
    from prosaic_integration_lab.sue_review.contracts import decode
    from prosaic_integration_lab.sue_review.sources import freeze_documents

    value = decode(_read(path, 65536), maximum=65536)
    if (type(value) is not dict or not {'seed','sources'} <= set(value)
            or set(value)-{'seed','sources','lens','max_turns'}
            or type(value['sources']) is not list or not 1 <= len(value['sources']) <= 16):
        raise ValueError('invalid request')
    documents, remaining = [], 65536
    for source in value['sources']:
        if (type(source) is not dict or not {'sourceId','path'} <= set(source)
                or set(source)-{'sourceId','path','revision','reference'}
                or type(source['path']) is not str or not Path(source['path']).is_absolute()):
            raise ValueError('explicit document paths required')
        text = _read(source['path'], remaining)
        remaining -= len(text.encode('utf-8'))
        documents.append({k:v for k,v in source.items() if k != 'path'} | {'text':text})
    value['sources'] = freeze_documents(documents)
    return value


@contextmanager
def _without_proxies():
    saved = {key:value for key,value in os.environ.items() if key.lower().endswith('_proxy')}
    try:
        for key in saved:
            del os.environ[key]
        os.environ['no_proxy'] = '*'
        yield
    finally:
        os.environ.pop('no_proxy',None)
        os.environ.update(saved)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('start','status','resume','report'))
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--run-id')
    parser.add_argument('--request',type=Path)
    parser.add_argument('--expected-revision')
    parser.add_argument('--choice',choices=('continue','reject'))
    parser.add_argument('--format',choices=('json','markdown'),default='json')
    args = parser.parse_args(argv)
    if args.action != 'start' and not args.run_id:
        parser.error('this action requires --run-id')
    if args.action == 'start' and args.request is None:
        parser.error('start requires --request')
    if args.action == 'resume' and not args.expected_revision:
        parser.error('resume requires --expected-revision')
    if args.action != 'start' and args.request is not None:
        parser.error('--request is only valid for start')
    if args.action != 'resume' and (args.choice is not None or args.expected_revision is not None):
        parser.error('resume arguments require resume')
    if args.action != 'report' and args.format != 'json':
        parser.error('Markdown is available for report')
    from prosaic_harness import StoreError
    from prosaic_runtime import EndpointConfig, RuntimeConfig
    from prosaic_integration_lab.identity import Principal
    from prosaic_integration_lab.sue_review.contracts import ReviewError
    from prosaic_integration_lab.sue_review.session import SueReviewSession
    from lab_runner.memory_workflow import store_for

    store = None
    try:
        host = load_host(args.config)
        config = RuntimeConfig({'fixture':EndpointConfig(host['runtime']['base_url'],'sue-fixture',
            features={'streaming':False})},{},'fixture',allowed_tools=frozenset())
        store = store_for(host)
        accounting = None
        if 'accounting' in host:
            from prosaic_runtime import RateCard
            from prosaic_runtime_postgres import PostgresRecorder
            accounting = PostgresRecorder(os.environ[host['accounting']['dsn_env']],
                namespace=host['namespace'],environment='sandbox',
                rate_card=RateCard('sue-fixture-v1','sue-fixture','2','8','0.5'))
        session = SueReviewSession(settings=host.get('review'),store=store,config=config,
            principal=Principal(**host['principal']),namespace=host['namespace'],accounting=accounting)
        run_id = args.run_id or uuid.uuid4().hex
        with _without_proxies():
            if args.action == 'start':
                result = session.start(run_id,**load_request(args.request))
            elif args.action == 'resume':
                result = session.resume(run_id,expected_revision=args.expected_revision,choice=args.choice)
            else:
                result = getattr(session,args.action)(run_id)
        if args.format == 'markdown':
            from prosaic_integration_lab.sue_review.reporting import render_markdown
            print(render_markdown(result),end='')
        else:
            print(json.dumps(result,ensure_ascii=False,allow_nan=False))
        return 0
    except ReviewError as error:
        print(json.dumps({'error':error.code}))
        return 2
    except PermissionError:
        print(json.dumps({'error':'not_found'}))
        return 4
    except StoreError as error:
        print(json.dumps({'error':error.code}))
        return 5
    except (ValueError,TypeError,KeyError,OSError,ImportError):
        print(json.dumps({'error':'invalid_configuration_or_request'}))
        return 2
    finally:
        if store is not None:
            store.close()


if __name__ == '__main__':
    raise SystemExit(main())
