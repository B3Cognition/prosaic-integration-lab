"""Select five original wheels from three successful exact-source SDK runs.

Candidate-only manifest/cache. Released manifests are never edited. Cross-repo
Actions access must actually succeed; no alternate mutable refs or URLs exist.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from prosaic_integration_lab.dependencies import cache_directory,file_digest,sdk_manifest,verified_wheel_paths

EXPECTED={'B3Cognition/prosaic':{'b3-prosaic':'0.4.1'},
    'B3Cognition/prosaic-runtime':{'b3-prosaic-runtime':'0.9.0','b3-prosaic-runtime-postgres':'0.3.0'},
    'B3Cognition/prosaic-harness':{'b3-prosaic-harness':'0.8.0','b3-prosaic-harness-postgres':'0.3.0'}}
CONTEXT_EXPECTED={**EXPECTED,
    'B3Cognition/prosaic-runtime':{'b3-prosaic-runtime':'0.9.4','b3-prosaic-runtime-postgres':'0.3.0'},
    'B3Cognition/prosaic-harness':{'b3-prosaic-harness':'0.9.0','b3-prosaic-harness-postgres':'0.4.0'}}
CONTEXT_PACK_EXPECTED={
    'B3Cognition/prosaic':{'b3-prosaic':'0.5.0'},
    'B3Cognition/prosaic-runtime':{'b3-prosaic-runtime':'0.9.19','b3-prosaic-runtime-postgres':'0.3.0'},
    'B3Cognition/prosaic-harness':{'b3-prosaic-harness':'0.9.13','b3-prosaic-harness-postgres':'0.4.2'}}


def serialized(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def digest(value):return hashlib.sha256(value).hexdigest()


def read(path):
    if path.is_symlink():raise ValueError('unsafe candidate receipt')
    with path.open('rb') as source:content=source.read(262145)
    if len(content)>262144:raise ValueError('candidate receipt too large')
    return json.loads(content),content


def validate_run(run,commit,*,tool_contracts=False):
    name="Tool contract candidate" if tool_contracts else "Publish SDK"
    path=".github/workflows/tool-contract-candidate.yml" if tool_contracts else ".github/workflows/publish.yml"
    if (not re.fullmatch('[0-9a-f]{40}',commit) or run.get('head_sha')!=commit or
        run.get('conclusion')!='success' or run.get('name')!=name or
        run.get('path')!=path or run.get('event') not in {'push','workflow_dispatch'}):
        raise ValueError('candidate requires successful exact-source qualification')


def retained_runtime_postgres(cache_root):
    """Retain the original published adapter, never a rebuilt same-version wheel."""
    from scripts.prepare_dependencies import prepare
    released=ROOT/'dependencies/releases.json'
    data=sdk_manifest(released)
    item=next(item for item in data['artifacts'] if item['distribution']=='b3-prosaic-runtime-postgres')
    if (item['version'],item['filename'],item['sha256'],item['source_commit']) != (
        '0.3.0','b3_prosaic_runtime_postgres-0.3.0-py3-none-any.whl',
        '5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca',
        'a59621c5f30d766d1217b37df777d3876075dc34'):
        raise ValueError('retained Runtime PostgreSQL release differs')
    cache=prepare(released,cache_root)
    return dict(item),cache/item['filename']


def curate(candidates,manifest,cache_root,*,context_assembly=False,context_packs=False,tool_contracts=False,parallel_tools=False):
    if parallel_tools:
        return curate_parallel_tools(candidates[0],candidates[1],manifest,cache_root)
    if tool_contracts:
        if context_assembly or context_packs:raise ValueError("candidate feature modes are mutually exclusive")
        return curate_tool_contracts(candidates,manifest,cache_root)
    if context_assembly and context_packs:raise ValueError('candidate feature modes are mutually exclusive')
    if len(candidates)!=3:raise ValueError('three explicit SDK candidates required')
    expected_train=CONTEXT_PACK_EXPECTED if context_packs else CONTEXT_EXPECTED if context_assembly else EXPECTED
    evidence=[];artifacts=[];sources={};seen=set()
    for repository,run_id,commit,directory in candidates:
        if repository not in EXPECTED or repository in seen or not re.fullmatch('[1-9][0-9]*',run_id):
            raise ValueError('invalid candidate identity')
        seen.add(repository);directory=Path(directory)
        receipt,content=read(directory/'release-receipt.json')
        expected=expected_train[repository]
        distributions=receipt.get('distributions',[])
        if (receipt.get('version')!=1 or not re.fullmatch('[0-9a-f]{40}',commit) or
            receipt.get('source_commit')!=commit or len(distributions)!=len(expected) or
            {item['name']:item['version'] for item in distributions}!=expected or content!=serialized(receipt)):
            raise ValueError('candidate source/distribution mismatch')
        names={name.replace('-','_')+'-'+version+suffix for name,version in expected.items()
               for suffix in ('-py3-none-any.whl','.tar.gz')}
        entries=receipt.get('artifacts',[])
        if (len(entries)!=len(names) or {item.get('filename') for item in entries}!=names or
            {path.name for path in directory.iterdir() if path.name.endswith(('.whl','.tar.gz'))}!=names):
            raise ValueError('candidate artifact inventory mismatch')
        for item in entries:
            path=directory/item['filename']
            if path.is_symlink() or not path.is_file() or not re.fullmatch('[0-9a-f]{64}',item.get('sha256','')) or file_digest(path)!=item['sha256']:
                raise ValueError('candidate artifact bytes differ')
        wheels=[item for item in entries if item['filename'].endswith('.whl')]
        candidate={'repository':repository,'run_id':run_id,'source_commit':commit,
                   'receipt_sha256':digest(content),'receipt':receipt,'wheels':wheels}
        if evidence:
            upstream,upstream_bytes=read(directory/'upstream-receipt.json')
            expected_upstream={'version':1,'candidates':evidence.copy()}
            if upstream!=expected_upstream or upstream_bytes!=serialized(upstream):
                raise ValueError('candidate upstream lineage differs from selected candidates')
            candidate.update(upstream_receipt=upstream,upstream_sha256=digest(upstream_bytes))
        elif repository!='B3Cognition/prosaic':raise ValueError('candidate dependency order differs')
        evidence.append(candidate)
        for name,version in expected.items():
            filename=name.replace('-','_')+'-'+version+'-py3-none-any.whl'
            item=next(item for item in wheels if item['filename']==filename)
            artifacts.append({'distribution':name,'version':version,**item,'source_commit':commit,
                              'qualified_run_id':run_id,'release_receipt_sha256':candidate['receipt_sha256']})
            sources[filename]=directory/filename
    lineage={'version':1,'candidates':evidence}
    if context_assembly or context_packs:
        retained,path=retained_runtime_postgres(cache_root)
        if path.is_symlink() or not path.is_file() or file_digest(path)!=retained['sha256']:
            raise ValueError('retained Runtime PostgreSQL bytes differ')
        artifacts=[retained if item['distribution']==retained['distribution'] else item for item in artifacts]
        sources[retained['filename']]=path
        lineage['retained_artifacts']=[retained]
    data={'artifacts':artifacts,'candidate_lineage':lineage}
    manifest=Path(manifest)
    if manifest.resolve() in {(ROOT/'dependencies/releases.json').resolve(),
                               (ROOT/'dependencies/releases-lab-0.2.0.json').resolve()}:
        raise ValueError('candidate cannot replace a release manifest')
    payload=serialized(data)
    if manifest.exists() and manifest.read_bytes()!=payload:raise ValueError('candidate manifest is immutable')
    manifest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='candidate-manifest-') as temporary:
        selected=Path(temporary)/'manifest.json';selected.write_bytes(payload);sdk_manifest(selected)
        cache=cache_directory(selected,cache_root);cache.mkdir(parents=True,exist_ok=True)
        for item in artifacts:
            destination=cache/item['filename']
            if destination.exists() and file_digest(destination)!=item['sha256']:raise ValueError('candidate cache conflict')
            shutil.copyfile(sources[item['filename']],destination)
        verified_wheel_paths(selected,cache)
    manifest.write_bytes(payload)
    return data



def curate_tool_contracts(candidates,manifest,cache_root):
    from lab_runner.tool_evidence import validate_tool_manifest
    from prosaic_integration_lab.tool_evidence import TRAIN
    manifest=Path(manifest);cache_root=Path(cache_root)
    if manifest.resolve().is_relative_to((ROOT/'dependencies').resolve()):
        raise ValueError('tool candidates must not replace published dependency manifests')
    if len(candidates)!=3:raise ValueError('three explicit original SDK runs required')
    artifacts=[];sources={};paired=[];retained=[]
    released=sdk_manifest(ROOT/'dependencies/releases.json')
    for (repository,run_id,commit,directory),expected_repository in zip(candidates,EXPECTED):
        if repository!=expected_repository or not re.fullmatch('[1-9][0-9]*',run_id):raise ValueError('candidate order or run identity differs')
        directory=Path(directory);receipt,raw=read(directory/'release-receipt.json')
        if receipt.get('source_commit')!=commit or raw!=serialized(receipt):raise ValueError('candidate source differs')
        if repository=='B3Cognition/prosaic':
            original=next(item for item in released['artifacts'] if item['distribution']=='b3-prosaic')
            entry=next(item for item in receipt['artifacts'] if item['filename']==original['filename'])
            if entry['sha256']!=original['sha256'] or commit!=original['source_commit']:raise ValueError('original Core differs')
            artifacts.append(dict(original));retained.append(dict(original));sources[original['filename']]=directory/original['filename']
            continue
        sdk='runtime' if repository.endswith('runtime') else 'harness'
        qualification,_=read(directory/'qualification-tool-contract-consumer.json')
        run,_=read(directory/'tool-contract-run.json');validate_run(run,commit,tool_contracts=True)
        if str(run.get('id'))!=run_id:raise ValueError('candidate run ID differs')
        candidate=dict(sdk=sdk,receipt=receipt,qualification=qualification,run=run)
        paired.append(candidate)
        for distribution in receipt['distributions']:
            name,version=distribution['name'],distribution['version']
            if TRAIN.get(name)!=version:raise ValueError('unexpected tool candidate distribution')
            filename=name.replace('-','_')+'-'+version+'-py3-none-any.whl'
            entry=next(item for item in receipt['artifacts'] if item['filename']==filename)
            artifacts.append(dict(distribution=name,version=version,source_commit=commit,**entry));sources[filename]=directory/filename
    recorder,path=retained_runtime_postgres(cache_root);retained.append(recorder);artifacts.append(recorder);sources[path.name]=path
    if paired[1]['sdk']!='harness' or paired[0]['sdk']!='runtime':raise ValueError('paired candidate order differs')
    harness_directory=Path(candidates[2][3])
    if read(harness_directory/'tool-contract-runtime-receipt.json')[0]!=paired[0]['receipt'] or read(harness_directory/'tool-contract-runtime-qualification.json')[0]!=paired[0]['qualification']:
        raise ValueError('Harness used different Runtime bytes')
    upstream_run=read(harness_directory/'tool-contract-runtime-run.json')[0]
    if upstream_run!=paired[0]['run']:raise ValueError('Harness used a different Runtime candidate run')
    data=dict(artifacts=artifacts,candidate_lineage=dict(version=1,kind='hosted-tool-contract-handoff',candidates=paired,retained_artifacts=retained))
    validate_tool_manifest(data);payload=serialized(data)
    if manifest.exists() and manifest.read_bytes()!=payload:raise ValueError('candidate manifest is immutable')
    with tempfile.TemporaryDirectory() as temporary:
        selected=Path(temporary)/'manifest.json';selected.write_bytes(payload);sdk_manifest(selected)
        cache=cache_directory(selected,cache_root);cache.mkdir(parents=True,exist_ok=True)
        for item in artifacts:
            source=sources[item['filename']]
            if source.is_symlink() or file_digest(source)!=item['sha256']:raise ValueError('candidate payload differs')
            target=cache/item['filename']
            if target.exists() and file_digest(target)!=item['sha256']:raise ValueError('candidate cache conflict')
            shutil.copyfile(source,target)
        verified_wheel_paths(selected,cache)
    manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_bytes(payload)
    return data

def load_profile(path):
    """Host-owned convenience recipe; every selected run is still reverified."""
    value,_=read(Path(path))
    prefixes=('core','runtime','harness')
    if (type(value) is not dict or set(value)!={'version',*prefixes} or
            type(value['version']) is not int or value['version']!=1):
        raise ValueError('invalid candidate profile')
    selected=[]
    for prefix,repository in zip(prefixes,EXPECTED):
        entry=value[prefix]
        if type(entry) is not dict or set(entry)!={'run_id','source_commit'}:
            raise ValueError('invalid candidate profile')
        run_id,commit=entry['run_id'],entry['source_commit']
        if (type(run_id) is not str or not re.fullmatch('[1-9][0-9]*',run_id) or
                type(commit) is not str or not re.fullmatch('[0-9a-f]{40}',commit)):
            raise ValueError('invalid candidate identity')
        selected.append((repository,run_id,commit))
    return selected



def curate_parallel_tools(runtime_directory,harness_directory,manifest,cache_root,*,mcp_client=False):
    """Consume local build-once receipts; never invoke a hosted release workflow."""
    from lab_runner.parallel_tools import validate_parallel_manifest
    from prosaic_integration_lab.parallel_tools import TRAIN
    validate = validate_parallel_manifest
    kind, label, prefix = 'local-parallel-tool-handoff', 'parallel-tool-consumer', 'parallel'
    retained_names = ['b3-prosaic', 'b3-prosaic-runtime-postgres']
    harness_names = {'b3-prosaic-harness', 'b3-prosaic-harness-postgres'}
    if mcp_client:
        from lab_runner.mcp_client import validate_mcp_manifest
        from prosaic_integration_lab.mcp_client import TRAIN
        validate = validate_mcp_manifest
        kind, label, prefix = 'local-mcp-client-handoff', 'mcp-client-consumer', 'mcp'
        retained_names.append('b3-prosaic-harness-postgres')
        harness_names.remove('b3-prosaic-harness-postgres')
    manifest=Path(manifest);cache_root=Path(cache_root)
    if manifest.resolve().is_relative_to((ROOT/'dependencies').resolve()):raise ValueError('candidate cannot replace public manifests')
    released=sdk_manifest(ROOT/'dependencies/releases.json');artifacts=[];sources={};paired=[];retained=[]
    for sdk,directory,names in [('runtime',Path(runtime_directory),{'b3-prosaic-runtime'}),('harness',Path(harness_directory),harness_names)]:
        receipt,_=read(directory/'release-receipt.json');qualification,_=read(directory/f'qualification-{label}.json')
        candidate=dict(sdk=sdk,receipt=receipt,qualification=qualification)
        if sdk=='harness':
            candidate.update(runtime_receipt=read(directory/f'{prefix}-runtime-receipt.json')[0],runtime_qualification=read(directory/f'{prefix}-runtime-qualification.json')[0])
        paired.append(candidate)
        for name in sorted(names):
            filename=name.replace('-','_')+'-'+TRAIN[name]+'-py3-none-any.whl'
            item=next(item for item in receipt['artifacts'] if item['filename']==filename)
            artifacts.append(dict(distribution=name,version=TRAIN[name],source_commit=receipt['source_commit'],**item));sources[filename]=directory/filename
    # Retain the original audited Core/recorder payloads and provenance.
    for name in retained_names:
        item=next(item for item in released['artifacts'] if item['distribution']==name)
        source=cache_directory(ROOT/'dependencies/releases.json',cache_root)/item['filename']
        if not source.is_file():raise ValueError('original released wheel cache required')
        artifacts.append(dict(item));retained.append(dict(item));sources[item['filename']]=source
    data=dict(artifacts=artifacts,candidate_lineage=dict(version=1,kind=kind,candidates=paired,retained_artifacts=retained))
    validate(data);payload=serialized(data)
    if manifest.exists() and manifest.read_bytes()!=payload:raise ValueError('candidate manifest is immutable')
    with tempfile.TemporaryDirectory() as temporary:
        probe=Path(temporary)/'manifest.json';probe.write_bytes(payload);sdk_manifest(probe)
        cache=cache_directory(probe,cache_root);cache.mkdir(parents=True,exist_ok=True)
        for item in artifacts:
            source=sources[item['filename']];target=cache/item['filename']
            if source.is_symlink() or file_digest(source)!=item['sha256']:raise ValueError('candidate payload differs')
            if target.exists() and file_digest(target)!=item['sha256']:raise ValueError('candidate cache conflict')
            shutil.copyfile(source,target)
        verified_wheel_paths(probe,cache)
    manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_bytes(payload)
    return data

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,help='pinned Core/Runtime/Harness run and source recipe')
    for prefix in ('core','runtime','harness'):
        parser.add_argument('--'+prefix+'-run-id')
        parser.add_argument('--'+prefix+'-source')
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--cache-root',type=Path,default=ROOT/'.cache/wheels')
    features=parser.add_mutually_exclusive_group()
    features.add_argument('--context-assembly',action='store_true',help='qualify the context SDK train and retain original Runtime PostgreSQL bytes')
    features.add_argument('--parallel-tools',action='store_true',help='curate explicit local parallel candidate archives without publication')
    features.add_argument('--mcp-client',action='store_true',help='curate exact qualified local MCP candidate wheels')
    parser.add_argument('--runtime-artifacts',type=Path)
    parser.add_argument('--harness-artifacts',type=Path)
    features.add_argument('--tool-contracts',action='store_true',help='curate only qualified safe-event/citation candidate workflows')
    features.add_argument('--context-packs',action='store_true',help='qualify the exact context-pack SDK train and retain original Runtime PostgreSQL bytes')
    args=parser.parse_args(argv)
    if args.parallel_tools or args.mcp_client:
        if args.runtime_artifacts is None or args.harness_artifacts is None:parser.error("local handoff requires both artifact directories")
        result=curate_parallel_tools(args.runtime_artifacts,args.harness_artifacts,args.manifest,args.cache_root,
                                     mcp_client=args.mcp_client)
        print(json.dumps({"manifest":str(args.manifest),"kind":result["candidate_lineage"]["kind"]}))
        return 0
    manual=[getattr(args,prefix+'_'+field) for prefix in ('core','runtime','harness')
            for field in ('run_id','source')]
    if args.profile is not None and any(value is not None for value in manual):
        parser.error('--profile cannot be combined with manual SDK identities')
    if args.profile is None and any(value is None for value in manual):
        parser.error('supply --profile or all three SDK run/source pairs')
    try:
        selected=load_profile(args.profile) if args.profile is not None else [
            (repository,getattr(args,prefix+'_run_id'),getattr(args,prefix+'_source'))
            for prefix,repository in zip(('core','runtime','harness'),EXPECTED)]
        for _,run_id,commit in selected:
            if not re.fullmatch('[1-9][0-9]*',run_id) or not re.fullmatch('[0-9a-f]{40}',commit):
                raise ValueError('invalid candidate identity')
        with tempfile.TemporaryDirectory(prefix='lab-sdk-candidates-') as temporary:
            candidates=[]
            for prefix,(repository,run_id,commit) in zip(('core','runtime','harness'),selected):
                result=subprocess.run(['gh','api','repos/'+repository+'/actions/runs/'+run_id],
                    capture_output=True,text=True,check=True,timeout=60)
                validate_run(json.loads(result.stdout),commit,tool_contracts=args.tool_contracts and repository!='B3Cognition/prosaic')
                directory=Path(temporary)/prefix
                subprocess.run(['gh','run','download',run_id,'--repo',repository,'--name','qualified-release',
                    '--dir',str(directory)],capture_output=True,check=True,timeout=120)
                if args.tool_contracts and repository!='B3Cognition/prosaic':
                    (directory/'tool-contract-run.json').write_bytes(serialized(json.loads(result.stdout)))
                candidates.append((repository,run_id,commit,directory))
            data=curate(candidates,args.manifest,args.cache_root,context_assembly=args.context_assembly,context_packs=args.context_packs,tool_contracts=args.tool_contracts)
        print(json.dumps({'event':'candidate_sdk_bytes_verified','candidate_manifest_sha256':digest(args.manifest.read_bytes()),
            'candidate_lineage_sha256':digest(serialized(data['candidate_lineage'])),'wheel_count':5}))
        return 0
    except Exception as error:
        print(json.dumps({'event':'candidate_sdk_not_qualified','category':type(error).__name__}))
        return 1


if __name__=='__main__':raise SystemExit(main())
