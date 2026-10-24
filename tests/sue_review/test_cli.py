import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

from tests.sue_review.test_execution import CLAIM, SOURCE, fixture, script


ROOT = Path(__file__).resolve().parents[2]


def cli(*args):
    env = dict(os.environ, PYTHONPATH=str(ROOT/'src')+os.pathsep+str(ROOT),
        HTTP_PROXY='http://192.0.2.1:1', http_proxy='http://192.0.2.1:1', NO_PROXY='', no_proxy='')
    return subprocess.run([sys.executable,'-m','lab_runner.sue_review',*map(str,args)],
        cwd=ROOT,env=env,capture_output=True,text=True,timeout=30)


def host(tmp_path, url='http://127.0.0.1:1/v1', enabled=True):
    value = dict(namespace='sue-cli',principal=dict(tenant_id='tenant',actor_id='alice',billing_account_id='payer'),
        store=dict(kind='file',path=str(tmp_path/'runs')),runtime=dict(base_url=url,model='sue-fixture'),review=dict(enabled=enabled))
    path=tmp_path/'host.json';path.write_text(json.dumps(value));path.chmod(0o600)
    return path,value


def request(tmp_path):
    source=tmp_path/'source.md';source.write_bytes(SOURCE.encode())
    path=tmp_path/'request.json';path.write_text(json.dumps(dict(seed=CLAIM,
        sources=[dict(sourceId='spec',path=str(source),revision='r1')],max_turns=1)))
    return path,source


def test_cli_new_process_pause_resume_frozen_sources_and_disabled_reporting(tmp_path):
    values,_=script(max_turns=1)
    with fixture(values) as (url,calls):
        config,value=host(tmp_path,url);req,source=request(tmp_path);run=uuid.uuid4().hex
        started=cli('start','--config',config,'--request',req,'--run-id',run)
        assert started.returncode==0,started.stderr+started.stdout
        waiting=json.loads(started.stdout)
        assert waiting['status']=='waiting' and calls==[]
        source.write_text('Changed after freezing.');source.unlink()
        resumed=cli('resume','--config',config,'--run-id',run,'--expected-revision',waiting['revision'],'--choice','continue')
        assert resumed.returncode==0,resumed.stderr+resumed.stdout
        completed=json.loads(resumed.stdout)
        assert completed['terminal']=='BOUNDED_STOP' and len(calls)==1
        value['review']={'enabled':False};config.write_text(json.dumps(value))
        for action in ('status','report'):
            result=cli(action,'--config',config,'--run-id',run)
            assert result.returncode==0,result.stderr+result.stdout
            assert json.loads(result.stdout)['status']=='completed'
        report=json.loads(cli('report','--config',config,'--run-id',run).stdout)
        assert report['citations'][0]['quote']==SOURCE.splitlines()[0]
        assert report['sources'][0]['textSha256']==hashlib.sha256(SOURCE.encode()).hexdigest()
        assert report['usageComplete'] is True and report['reportedTokens']==15
        markdown=cli('report','--config',config,'--run-id',run,'--format','markdown')
        assert markdown.returncode==0 and 'Advisory SUE review' in markdown.stdout
        rejected=cli('resume','--config',config,'--run-id',run,'--expected-revision',completed['revision'])
        assert rejected.returncode==2 and json.loads(rejected.stdout)['error']=='review_disabled'
        assert len(calls)==1


@pytest.mark.parametrize('mutation',['public_mode','symlink','unknown','principal','remote','credential','model','duplicate','directory','url_type'])
def test_cli_invalid_host_config_fails_closed(tmp_path,mutation):
    config,value=host(tmp_path);req,_=request(tmp_path)
    if mutation=='public_mode':config.chmod(0o644)
    elif mutation=='symlink':
        other=tmp_path/'other.json';config.rename(other);config.symlink_to(other)
    elif mutation=='directory':config.unlink();config.mkdir()
    elif mutation=='duplicate':config.write_text('{"namespace":"a","namespace":"b"}')
    else:
        if mutation=='unknown':value['secret']='MUST-NOT-LEAK'
        elif mutation=='principal':value['principal']['actor_id']=''
        elif mutation=='remote':value['runtime']['base_url']='https://external.example/v1'
        elif mutation=='credential':value['runtime']['api_key_env']='SECRET'
        elif mutation=='model':value['runtime']['model']='paid-model'
        elif mutation=='url_type':value['runtime']['base_url']=True
        config.write_text(json.dumps(value))
    result=cli('start','--config',config,'--request',req)
    assert result.returncode==2
    assert 'MUST-NOT-LEAK' not in result.stdout+result.stderr
    assert str(tmp_path) not in result.stdout+result.stderr


@pytest.mark.parametrize('mutation',['symlink','directory','invalid_utf8','oversize','relative','inline','duplicate'])
def test_cli_document_admission_rejects_unsafe_or_unbounded_input(tmp_path,mutation):
    config,_=host(tmp_path);req,source=request(tmp_path)
    if mutation=='symlink':
        other=tmp_path/'other.md';source.rename(other);source.symlink_to(other)
    elif mutation=='directory':source.unlink();source.mkdir()
    elif mutation=='invalid_utf8':source.write_bytes(b'\xff')
    elif mutation=='oversize':source.write_bytes(b'a'*65537)
    else:
        value=json.loads(req.read_text())
        if mutation=='relative':value['sources'][0]['path']='source.md'
        elif mutation=='inline':value['sources'][0]={'sourceId':'spec','text':'unapproved inline'}
        else:value['sources']*=2
        req.write_text(json.dumps(value))
    result=cli('start','--config',config,'--request',req)
    assert result.returncode==2 and str(tmp_path) not in result.stdout+result.stderr


@pytest.mark.parametrize('args',[[],['status'],['report'],['resume'],['start']])
def test_cli_missing_arguments_exit_nonzero_without_traceback(tmp_path,args):
    config,_=host(tmp_path)
    result=cli(*args,'--config',config)
    assert result.returncode==2 and 'Traceback' not in result.stderr


def test_cli_review_defaults_disabled_and_unknown_run_is_nonzero(tmp_path):
    config,value=host(tmp_path);req,_=request(tmp_path)
    del value['review'];config.write_text(json.dumps(value))
    disabled=cli('start','--config',config,'--request',req)
    assert disabled.returncode==2 and json.loads(disabled.stdout)['error']=='review_disabled'
    missing=cli('status','--config',config,'--run-id',uuid.uuid4().hex)
    assert missing.returncode!=0 and 'Traceback' not in missing.stderr
