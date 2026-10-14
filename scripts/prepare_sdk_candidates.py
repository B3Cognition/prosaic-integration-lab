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
sys.path.insert(0,str(ROOT/'src'))
from prosaic_integration_lab.dependencies import cache_directory,file_digest,sdk_manifest,verified_wheel_paths

EXPECTED={'B3Cognition/prosaic':{'b3-prosaic':'0.4.1'},
    'B3Cognition/prosaic-runtime':{'b3-prosaic-runtime':'0.9.0','b3-prosaic-runtime-postgres':'0.3.0'},
    'B3Cognition/prosaic-harness':{'b3-prosaic-harness':'0.8.0','b3-prosaic-harness-postgres':'0.3.0'}}
CONTEXT_EXPECTED={**EXPECTED,
    'B3Cognition/prosaic-runtime':{'b3-prosaic-runtime':'0.9.4','b3-prosaic-runtime-postgres':'0.3.0'},
    'B3Cognition/prosaic-harness':{'b3-prosaic-harness':'0.9.0','b3-prosaic-harness-postgres':'0.4.0'}}


def serialized(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def digest(value):return hashlib.sha256(value).hexdigest()


def read(path):
    if path.is_symlink():raise ValueError('unsafe candidate receipt')
    with path.open('rb') as source:content=source.read(262145)
    if len(content)>262144:raise ValueError('candidate receipt too large')
    return json.loads(content),content


def validate_run(run,commit):
    if (not re.fullmatch('[0-9a-f]{40}',commit) or run.get('head_sha')!=commit or
        run.get('conclusion')!='success' or run.get('name')!='Publish SDK' or
        run.get('path')!='.github/workflows/publish.yml' or run.get('event') not in {'push','workflow_dispatch'}):
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


def curate(candidates,manifest,cache_root,*,context_assembly=False):
    if len(candidates)!=3:raise ValueError('three explicit SDK candidates required')
    expected_train=CONTEXT_EXPECTED if context_assembly else EXPECTED
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
    if context_assembly:
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


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,help='pinned Core/Runtime/Harness run and source recipe')
    for prefix in ('core','runtime','harness'):
        parser.add_argument('--'+prefix+'-run-id')
        parser.add_argument('--'+prefix+'-source')
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--cache-root',type=Path,default=ROOT/'.cache/wheels')
    parser.add_argument('--context-assembly',action='store_true',help='qualify the context SDK train and retain original Runtime PostgreSQL bytes')
    args=parser.parse_args(argv)
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
                validate_run(json.loads(result.stdout),commit)
                directory=Path(temporary)/prefix
                subprocess.run(['gh','run','download',run_id,'--repo',repository,'--name','qualified-release',
                    '--dir',str(directory)],capture_output=True,check=True,timeout=120)
                candidates.append((repository,run_id,commit,directory))
            data=curate(candidates,args.manifest,args.cache_root,context_assembly=args.context_assembly)
        print(json.dumps({'event':'candidate_sdk_bytes_verified','candidate_manifest_sha256':digest(args.manifest.read_bytes()),
            'candidate_lineage_sha256':digest(serialized(data['candidate_lineage'])),'wheel_count':5}))
        return 0
    except Exception as error:
        print(json.dumps({'event':'candidate_sdk_not_qualified','category':type(error).__name__}))
        return 1


if __name__=='__main__':raise SystemExit(main())
