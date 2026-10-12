"""Isolated Lab wheel/sdist consumption; candidate bytes never claim public adoption."""
import argparse
from email.parser import BytesParser
import hashlib
import importlib.util
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from prosaic_integration_lab.dependencies import (cache_directory,manifest_bytes,
    manifest_digest,sdk_manifest,verified_wheel_paths)


def _helper(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(''+name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class DistributionCommandError(ValueError):
    def __init__(self,output):
        super().__init__('isolated distribution command failed')
        self.output=output


def run(argv,*,directory,environment,timeout=300):
    with tempfile.TemporaryFile(dir=directory) as out,tempfile.TemporaryFile(dir=directory) as err:
        result=subprocess.run([str(arg) for arg in argv],cwd=directory,env=environment,
            stdout=out,stderr=err,timeout=timeout,check=False)
        out.seek(0,os.SEEK_END);size=out.tell()
        out.seek(max(0,size-65536));output=out.read(65536)
        if result.returncode:raise DistributionCommandError(output)
        return output


def safe_stack_failure(raw):
    """Preserve only the existing sanitized owned receipt on command failure."""
    try:
        records=[json.loads(line) for line in raw.decode().splitlines() if line.startswith('{')]
    except (UnicodeError,ValueError):return {}
    matches=[row for row in records if type(row) is dict and type(row.get('mode')) is str
        and row['mode'] in {'demo','conversation'}
        and type(row.get('owner')) is str and re.fullmatch('[0-9a-f]{32}',row['owner'])]
    if len(matches)!=1:return {}
    from lab_runner.gates import export
    result={'stack_receipt':export(matches[0])}
    error=matches[0].get('error')
    if type(error) is str and error in {'EngineError','RuntimeError','ValueError','KeyError','AssertionError','TimeoutExpired'}:
        result['stack_error']=error
    return result


def validate_mode(data,*,candidate):
    if ('candidate_lineage' in data)!=candidate:
        raise ValueError('candidate flag must match the original SDK manifest')


def verify_cli_versions(raw,data):
    expected={item['distribution']:item['version'] for item in data['artifacts']}
    if json.loads(raw)!=expected:raise ValueError('installed SDK CLI versions mismatch')


def execution_receipt(raw,*,command):
    """Select the owned execution result; the demo also prints a separate report."""
    expected='demo' if command=='demo' else 'conversation'
    records=[json.loads(line) for line in raw.decode().splitlines() if line.startswith('{')]
    matches=[row for row in records if type(row) is dict and row.get('mode')==expected]
    if len(matches)!=1:raise ValueError('missing or ambiguous stack execution receipt')
    result=matches[0]
    if (type(result.get('owner')) is not str or not re.fullmatch('[0-9a-f]{32}',result['owner'])
        or result.get('passed') is not True or result.get('cleanup')!='verified'
        or command=='demo' and result.get('fixture')!='conversation-demonstration'):
        raise ValueError('source stack qualification or cleanup failed')
    return result


def extract_sdist(archive,destination):
    """Validate the complete bounded archive before writing any of its paths."""
    archive=Path(archive);destination=Path(destination)
    if archive.is_symlink() or archive.stat().st_size>32*1024*1024:
        raise ValueError('invalid source archive')
    with tarfile.open(archive,'r:gz') as source:
        members=source.getmembers()
        if not 1<=len(members)<=10000 or sum(member.size for member in members)>64*1024*1024:
            raise ValueError('source archive exceeds bounds')
        roots=set();names=set()
        for member in members:
            path=PurePosixPath(member.name)
            if (path.is_absolute() or not path.parts or '..' in path.parts or '\\' in member.name
                or member.name in names or not (member.isfile() or member.isdir())):
                raise ValueError('unsafe source archive')
            roots.add(path.parts[0]);names.add(member.name)
        if len(roots)!=1:raise ValueError('source archive must have one root')
        destination.mkdir(mode=0o700)
        for member in members:
            target=destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with source.extractfile(member) as incoming,target.open('xb') as outgoing:
                    shutil.copyfileobj(incoming,outgoing)
        return destination/next(iter(roots))


def wheel_identity(path):
    path=Path(path)
    if path.is_symlink() or path.stat().st_size>32*1024*1024:raise ValueError('invalid Lab wheel')
    with zipfile.ZipFile(path) as wheel:
        entries=wheel.infolist();names=[entry.filename for entry in entries]
        if (len(names)!=len(set(names)) or len(names)>10000 or
            sum(entry.file_size for entry in entries)>64*1024*1024 or
            any('..' in PurePosixPath(name).parts or name.startswith('/') or '\\' in name for name in names)):
            raise ValueError('invalid Lab wheel payload')
        metadata=[name for name in names if name.endswith('.dist-info/METADATA')]
        if len(metadata)!=1:raise ValueError('invalid Lab wheel metadata')
        info=BytesParser().parsebytes(wheel.read(metadata[0]))
        if info.get('Name')!='prosaic-integration-lab' or info.get('Version')!='0.5.0':
            raise ValueError('unexpected Lab distribution')
        files={name:hashlib.sha256(wheel.read(name)).hexdigest() for name in names
               if not name.endswith(('/','/RECORD'))}
        return {'name':info['Name'],'version':info['Version'],'files':files}


PUBLIC_CONVERSATION='''
from prosaic_harness import Conversation, ConversationBindings, ConversationPolicy, ConversationScope, MemorySessionStore
from prosaic_runtime import RunPolicy, ProsaicRuntime
assert 'conversation_turn_v1' in ProsaicRuntime.capabilities
binding=ConversationBindings(agent,version='installed-adoption-v1',config=config,policy=ConversationPolicy(),
    run_policy=RunPolicy(max_provider_requests=1,max_tool_calls=0,timeout_s=1))
store=MemorySessionStore(namespace='installed-adoption');store.initialize()
controller=Conversation(binding,store=store,scope=ConversationScope('installed-adoption','test','lab','tenant','actor'))
session=controller.create()
assert controller.status(session.session_id).document['status']=='ready'
assert controller.history(session.session_id)==()
from importlib.metadata import distribution, packages_distributions
import prosaic_integration_lab, lab_runner
lab=distribution('prosaic-integration-lab')
assert lab.version=='0.5.0'
for module in (prosaic_integration_lab,lab_runner):
    assert set(packages_distributions()[module.__name__])=={'prosaic-integration-lab'}
    assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
'''
LAB_AUDIT='''import hashlib,json,sys
from pathlib import Path
from importlib.metadata import distribution
expected=json.loads(Path(sys.argv[1]).read_text())
dist=distribution(expected['name'])
assert dist.version==expected['version']
for name,digest in expected['files'].items():
    path=Path(dist.locate_file(name)).resolve()
    assert path.is_relative_to(Path(sys.prefix).resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
'''


def consume(wheel,*,directory,manifest,wheels,lock,environment):
    public=_helper('verify_public_adoption')
    venv=directory/'venv'
    run([sys.executable,'-I','-m','venv',venv],directory=directory,environment=environment)
    python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    pip=[python,'-I','-m','pip','--isolated','--no-input','--keyring-provider','disabled']
    run([*pip,'install','--index-url',public.INDEX,'--require-hashes','-r',lock],
        directory=directory,environment=environment)
    run([*pip,'install','--no-deps',*verified_wheel_paths(manifest,wheels),wheel],
        directory=directory,environment=environment)
    expected=directory/'lab-wheel.json';expected.write_text(json.dumps(wheel_identity(wheel)))
    helper=directory/'audit-helper'
    (helper/'scripts').mkdir(parents=True);(helper/'src/prosaic_integration_lab').mkdir(parents=True)
    shutil.copyfile(ROOT/'scripts/audit_install.py',helper/'scripts/audit_install.py')
    shutil.copyfile(ROOT/'src/prosaic_integration_lab/dependencies.py',helper/'src/prosaic_integration_lab/dependencies.py')
    (helper/'src/prosaic_integration_lab/__init__.py').write_text('')
    def audit():
        run([python,'-I','-B','-c',public.AUDIT_LAUNCH,helper/'scripts/audit_install.py',
            '--manifest',manifest,'--wheel-dir',wheels],directory=directory,environment=environment)
        run([python,'-I','-B','-c',LAB_AUDIT,expected],directory=directory,environment=environment)
    audit()
    run([*pip,'check'],directory=directory,environment=environment)
    example=directory/'example.py';example.write_text(public.PUBLIC_EXAMPLE+PUBLIC_CONVERSATION)
    run([python,'-I','-B',example,manifest],directory=directory,environment=environment)
    version=run([python,'-I','-B','-m','prosaic_integration_lab','--version'],directory=directory,environment=environment)
    verify_cli_versions(version,json.loads(manifest.read_bytes()))
    run([python,'-I','-B','-m','lab_runner','--help'],directory=directory,environment=environment)
    audit()
    return python


def verify(wheel,sdist,manifest,*,wheel_dir=None,candidate=False,run_stack=False,postgres_version=16):
    result={'event':'conversation_distribution','passed':False,'candidate':candidate,
        'public_index_verified':False,'owned_temporary_cleanup':True,'stack_executed':False}
    stage='inputs';temporary=None;raw=None
    try:
        wheel=Path(wheel).resolve();sdist=Path(sdist).resolve();manifest=Path(manifest).resolve()
        data=sdk_manifest(manifest);validate_mode(data,candidate=candidate)
        before=manifest_digest(manifest);identity=wheel_identity(wheel)
        wheel_dir=Path(wheel_dir) if wheel_dir else cache_directory(manifest,ROOT/'.cache/wheels')
        selected=verified_wheel_paths(manifest,wheel_dir)
        public=_helper('verify_public_adoption');environment=public.isolated_environment()
        if not candidate:
            stage='public_index'
            if not public.verify(manifest)['passed']:raise ValueError('public-index verification failed')
            result['public_index_verified']=True
        temporary=tempfile.TemporaryDirectory(prefix='lab-conversation-distribution-')
        directory=Path(temporary.name).resolve()
        snapshot=directory/'manifest.json';snapshot.write_bytes(manifest_bytes(manifest))
        wheels=directory/'wheels';wheels.mkdir()
        for path in selected:shutil.copyfile(path,wheels/path.name)
        verified_wheel_paths(snapshot,wheels)
        original_wheel=directory/wheel.name;original_sdist=directory/sdist.name
        shutil.copyfile(wheel,original_wheel);shutil.copyfile(sdist,original_sdist)
        lock=directory/'requirements.lock';shutil.copyfile(ROOT/'dependencies/requirements.lock',lock)
        stage='wheel_consumer';consumer=directory/'wheel';consumer.mkdir()
        python=consume(original_wheel,directory=consumer,manifest=snapshot,wheels=wheels,lock=lock,environment=environment)
        stage='sdist_inventory';source=extract_sdist(original_sdist,directory/'source')
        for name in ('configs/conversation-conformance.example.json','docs/conversations.md',
                     'assets/conversation/agents/assistant.md','scripts/conversation_conformance.py',
                     'tests/acceptance/test_conversation_journey.py','dependencies/public-build-inputs.json'):
            if not (source/name).is_file():raise ValueError('incomplete conversation source distribution')
        stage='sdist_build';built=directory/'rebuilt';built.mkdir()
        run([python,'-I','-m','build','--wheel','--outdir',built,source],directory=directory,environment=environment)
        choices=list(built.glob('*.whl'))
        if len(choices)!=1 or wheel_identity(choices[0])['version']!=identity['version']:
            raise ValueError('source build differs from Lab version')
        stage='sdist_consumer';second=directory/'sdist-consumer';second.mkdir()
        source_python=consume(choices[0],directory=second,manifest=snapshot,wheels=wheels,lock=lock,environment=environment)
        if run_stack:
            stage='sdist_image_build'
            image=run([source_python,source/'scripts/build_consumer.py','--manifest',snapshot,
                '--wheel-dir',wheels,'--dependency-mode','candidate' if candidate else 'released',
                '--tag','prosaic-integration-lab:conversation-sdist'],directory=source,environment=environment,timeout=900)
            lines=image.decode().splitlines();image_id=next((line for line in reversed(lines) if line.startswith('sha256:')),None)
            if image_id is None:raise ValueError('source consumer did not return immutable image')
            flags=['--candidate','--candidate-manifest',snapshot] if candidate else []
            for command in ('demo','test'):
                stage='sdist_demo' if command=='demo' else 'sdist_acceptance'
                raw=None
                raw=run([source_python,'-m','lab_runner',command,'--mode','conversation','--postgres-version',str(postgres_version),
                    '--consumer-image',image_id,*flags],directory=source,environment=environment,timeout=900)
                receipt=execution_receipt(raw,command=command)
                if receipt.get('images',{}).get('consumer')!=image_id:
                    raise ValueError('source consumer image changed between build and qualification')
                if command=='test':
                    from lab_runner.gates import validate
                    lineage=data.get('candidate_lineage')
                    lineage_sha=(hashlib.sha256((json.dumps(lineage,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
                                 if lineage is not None else None)
                    validate(receipt,'conversation',postgres_version,candidate=candidate,
                             manifest_sha=before if candidate else None,lineage_sha=lineage_sha)
            result['stack_executed']=True
        stage='final_inputs'
        if manifest_digest(manifest)!=before or manifest_digest(snapshot)!=before:raise ValueError('manifest changed')
        result.update(passed=True,manifest_sha256=before,version=identity['version'],
            wheel_sha256=hashlib.sha256(original_wheel.read_bytes()).hexdigest(),
            sdist_sha256=hashlib.sha256(original_sdist.read_bytes()).hexdigest(),
            installed_payloads_verified=True,isolated_imports_verified=True,pip_check_passed=True,
            public_construction_verified=True,sdist_assets_verified=True)
    except Exception as error:
        result.update(failure='distribution_failed',failure_stage=stage)
        if stage in {'sdist_demo','sdist_acceptance'}:
            output=error.output if isinstance(error,DistributionCommandError) else raw
            if output is not None:result.update(safe_stack_failure(output))
    finally:
        if temporary is not None:
            try:temporary.cleanup()
            except Exception:result.update(passed=False,owned_temporary_cleanup=False,failure='cleanup_failed')
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('wheel','sdist','manifest'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--wheel-dir',type=Path);parser.add_argument('--candidate',action='store_true')
    parser.add_argument('--run-stack',action='store_true');parser.add_argument('--postgres-version',type=int,choices=(16,18),default=16)
    parser.add_argument('--export',type=Path);args=parser.parse_args(argv)
    result=verify(args.wheel,args.sdist,args.manifest,wheel_dir=args.wheel_dir,candidate=args.candidate,
                  run_stack=args.run_stack,postgres_version=args.postgres_version)
    encoded=json.dumps(result,sort_keys=True)
    if args.export:
        try:
            args.export.parent.mkdir(parents=True,exist_ok=True)
            args.export.write_text(encoded+'\n')
        except OSError:result.update(passed=False,failure='export_failed');encoded=json.dumps(result,sort_keys=True)
    print(encoded);return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
