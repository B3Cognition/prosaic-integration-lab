import os
from pathlib import Path
import subprocess
import sys


def test_default_disabled_constructor_never_imports_engine_or_sdk():
    code = '''
import importlib.abc,sys
class Deny(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0] in {'castle_sue','cognitive_castle','prosaic_runtime','prosaic_harness'}:raise AssertionError(name)
sys.meta_path.insert(0,Deny())
from prosaic_integration_lab.sue_review.session import SueReviewSession
from prosaic_integration_lab.identity import Principal
session=SueReviewSession(None,None,None,Principal('tenant','alice','payer'),'review')
try:session.start('a'*32,seed='claim',sources=[])
except ValueError as e:assert str(e)=='review_disabled'
else:raise AssertionError('disabled start admitted')
'''
    env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[2]/'src')}
    result=subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
