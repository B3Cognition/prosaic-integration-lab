"""The safe public image snapshot must retain usable copy-out examples."""
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import subprocess
import sys


def test_public_container_snapshot_can_copy_and_admit_all_feature_blueprints(tmp_path):
    root=Path(__file__).resolve().parents[2]
    snapshot=tmp_path/'public';snapshot.mkdir()
    for name in json.loads((root/'dependencies/public-build-inputs.json').read_text())['files']:
        target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,target)
    script='''import json,subprocess,sys,runpy
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from lab_runner.blueprints import copy_blueprint
import lab_runner.blueprints as blueprints
assert Path(blueprints.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
destination=Path(sys.argv[2])
for name in ('request-headers','revision-review','conversation-caps','rule-admission','workflow-enforcement','accounting-metadata','sent-effort','tool-evidence','guarded-recovery','nemotron-correction'):
    project=copy_blueprint(name,destination/name)
    assert (project/'README.md').is_file()
    assert (project/'.prosaic/subagents').is_dir()
header=runpy.run_path(str(destination/'request-headers/host.py'))
assert header['load_agent'](destination/'request-headers').type=='subagent'
from prosaic_harness import Workflow
Workflow.load(destination/'revision-review/workflow.yml',executable=str(Path(sys.executable).with_name('prosaic')))
workflow_host=runpy.run_path(str(destination/'workflow-enforcement/host.py'))
for mode in ('yaml','native'):
    workflow_host['workflow'](mode=mode,executable=str(Path(sys.executable).with_name('prosaic')))
metadata=runpy.run_path(str(destination/'accounting-metadata/host.py'))
metadata['workflow'](metadata['build_runtime'](project=destination/'accounting-metadata'),project=destination/'accounting-metadata')
effort=runpy.run_path(str(destination/'sent-effort/host.py'))
effort['workflow'](effort['build_runtime'](project=destination/'sent-effort'),project=destination/'sent-effort')
caps=runpy.run_path(str(destination/'conversation-caps/host.py'))
assert caps['limits'](caps['build_bindings'](project=destination/'conversation-caps'))=={'ordinary':8192,'interpretation':8192}
ontology=copy_blueprint('catalogue-ontology',destination/'catalogue-ontology')
command=[sys.executable,'-I',str(ontology/'host.py'),'discover']
ordinary=subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
assert 'ontology' not in json.loads(ordinary.stdout)
explicit=subprocess.run(command+['--ontology'],capture_output=True,text=True,timeout=15)
if sys.argv[3] == 'released-ontology':
    assert explicit.returncode == 0, explicit.stderr
    enriched=json.loads(explicit.stdout)
    assert enriched.pop('ontology') == json.loads((ontology/'fixtures/visible.json').read_bytes())
    assert enriched == json.loads(ordinary.stdout)
else:
    assert explicit.returncode != 0
    assert 'Core 0.5.1rc1 and Harness 0.9.17rc1' in explicit.stderr
'''
    pair = (version('b3-prosaic'), version('b3-prosaic-harness'))
    profile = 'released-ontology' if pair == ('0.5.1','0.9.18') else 'historical'
    result=subprocess.run([sys.executable,'-I','-c',script,str(snapshot),str(tmp_path/'copied'),profile],
        cwd=tmp_path,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr


def test_public_snapshot_retains_context_pack_history_and_current_freeze(tmp_path):
    root=Path(__file__).resolve().parents[2]
    snapshot=tmp_path/'public';snapshot.mkdir()
    for name in json.loads((root/'dependencies/public-build-inputs.json').read_text())['files']:
        target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,target)
    script='''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from lab_runner.quality.suite import resource
saved=json.loads(resource('sdk-provenance-pre-context-packs.json'))
assert {a['distribution']:a['version'] for a in saved['artifacts']}['b3-prosaic-runtime']=='0.9.18'
saved=json.loads(resource('sdk-provenance-pre-tool-contracts.json'))
assert {a['distribution']:a['version'] for a in saved['artifacts']}['b3-prosaic-runtime']=='0.9.19'
from lab_runner.memory.suite import load_suite
assert len(load_suite()['cases'])==12
'''
    result=subprocess.run([sys.executable,'-I','-c',script,str(snapshot)],cwd=tmp_path,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
