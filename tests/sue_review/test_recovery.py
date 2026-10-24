import json
from pathlib import Path
import os
import subprocess
import sys
import uuid

import pytest
from prosaic_harness import FileRunStore, RevisionConflict

from tests.sue_review.test_execution import CLAIM, SOURCE, fixture, script, session


CRASH = r'''
import json,os,sys
from prosaic_harness import FileRunStore
from prosaic_runtime import EndpointConfig,RuntimeConfig
from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.sue_review.session import SueReviewSession
root,url,run,revision,boundary=sys.argv[1:]
base=FileRunStore(root,namespace='sue-test')
class CrashStore:
 def __getattr__(self,n):return getattr(base,n)
 def save_receipt(self,*args,**kw):
  if boundary=='before-receipt':os._exit(51)
  result=base.save_receipt(*args,**kw)
  if boundary=='after-receipt':os._exit(52)
  return result
 def save_run(self,*args,**kw):
  result=base.save_run(*args,**kw)
  if boundary=='after-accept' and args[1]['outputs']:os._exit(53)
  return result
config=RuntimeConfig({'fixture':EndpointConfig(url,'sue-fixture',features={'streaming':False})},{},'fixture',allowed_tools=frozenset())
flow=SueReviewSession(settings={'enabled':True},store=CrashStore(),config=config,principal=Principal('tenant','alice','payer'),namespace='sue-test')
flow.resume(run,expected_revision=revision,choice='continue')
raise SystemExit(99)
'''


@pytest.mark.parametrize(('boundary','exit_code'),[('before-receipt',51),('after-receipt',52),('after-accept',53)])
def test_fresh_process_loss_boundaries_do_not_repeat_provider_call(tmp_path,boundary,exit_code):
    values,_=script(max_turns=1)
    root=tmp_path/'runs'
    with fixture(values) as (url,requests), FileRunStore(root,namespace='sue-test') as store:
        flow=session(store,url)
        run=uuid.uuid4().hex
        waiting=flow.start(run,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],max_turns=1)
        env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[2]/'src')}
        result=subprocess.run([sys.executable,'-c',CRASH,str(root),url,run,waiting['revision'],boundary],env=env,capture_output=True,text=True,timeout=30)
        assert result.returncode==exit_code,result.stderr
        current=flow.status(run)
        recovered=flow.resume(run,expected_revision=current['revision'])
        assert len(requests)==1
        if boundary=='before-receipt':
            assert recovered['status']=='blocked' and recovered['reason']=='interrupted_call'
            assert flow.report(run)['usageComplete'] is False
        else:
            assert recovered['status']=='completed' and recovered['acceptedTurns']==1
        assert flow.report(run)['sources'][0]['textSha256']


def test_lifetime_is_configurable_and_never_reset_or_extended(tmp_path):
    values,_=script(max_turns=1)
    now=[1000.0]
    with fixture(values) as (url,requests),FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
        flow=session(store,url,clock=lambda:now[0])
        run=uuid.uuid4().hex
        waiting=flow.start(run,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],max_turns=1)
        assert waiting['deadline']==87400
        now[0]+=3600
        done=flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        assert done['status']=='completed' and done['deadline']==waiting['deadline']
        second=uuid.uuid4().hex
        waiting=flow.start(second,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],max_turns=1)
        before=len(requests)
        now[0]=waiting['deadline']+1
        stopped=flow.resume(second,expected_revision=waiting['revision'],choice='continue')
        assert stopped['reason']=='run_deadline' and stopped['deadline']==waiting['deadline']
        assert len(requests)==before
        assert flow.report(second)['acceptedTurns']==0


def test_unknown_usage_cannot_advance_and_stale_revision_cannot_dispatch(tmp_path):
    values,_=script(max_turns=1)
    with fixture(values,usage=False) as (url,requests),FileRunStore(tmp_path/'runs',namespace='sue-test') as store:
        flow=session(store,url)
        run=uuid.uuid4().hex
        waiting=flow.start(run,seed=CLAIM,sources=[{'sourceId':'spec','text':SOURCE}],max_turns=1)
        with pytest.raises(RevisionConflict):flow.resume(run,expected_revision='0'*64,choice='continue')
        assert requests==[]
        stopped=flow.resume(run,expected_revision=waiting['revision'],choice='continue')
        assert stopped['status']=='blocked' and stopped['acceptedTurns']==0 and len(requests)==1
        assert flow.report(run)['usageComplete'] is False
