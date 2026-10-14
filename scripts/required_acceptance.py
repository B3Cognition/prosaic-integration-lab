"""Run every required cell lane; export only whitelisted receipt summaries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab_runner.gates import COUNTS,export,validate,required_modes,supports_context_assembly
from lab_runner.stack import EngineError

def resolve_image(candidate):
    from lab_runner.stack import command
    command('docker','info')
    name = 'prosaic-integration-lab:candidate' if candidate else 'prosaic-integration-lab:dev'
    return json.loads(command('docker','image','inspect',name))[0]['Id']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--postgres-version',type=int,choices=(16,18),required=True)
    parser.add_argument('--candidate',action='store_true')
    parser.add_argument('--consumer-image',help='immutable image ID for an isolated local build')
    parser.add_argument('--candidate-manifest',type=Path)
    parser.add_argument('--baseline-image')
    parser.add_argument('--export',type=Path,required=True)
    args = parser.parse_args()
    if args.candidate and args.candidate_manifest is None:parser.error('--candidate requires complete --candidate-manifest')
    if args.candidate_manifest is not None and not args.candidate:parser.error('candidate manifest requires --candidate')
    try:
        image_id = args.consumer_image or resolve_image(args.candidate)
    except (EngineError,OSError,ValueError,KeyError,IndexError):
        summary = {'passed':False,'postgres_major':args.postgres_version,'lanes':[],
            'event':'required_image_unavailable'}
        args.export.parent.mkdir(parents=True,exist_ok=True)
        args.export.write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary))
        return 1
    manifest_sha = hashlib.sha256(args.candidate_manifest.read_bytes()).hexdigest() if args.candidate else None
    lineage=json.loads(args.candidate_manifest.read_text()).get('candidate_lineage') if args.candidate else None
    lineage_sha=hashlib.sha256((json.dumps(lineage,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()).hexdigest() if lineage is not None else None
    summary = {'passed':True,'postgres_major':args.postgres_version,'lanes':[]}
    released=json.loads((ROOT/'dependencies/releases.json').read_text())
    selected=json.loads(args.candidate_manifest.read_text()) if args.candidate else released
    context_enabled=supports_context_assembly(selected)
    for mode in required_modes(candidate=args.candidate,manifest=released):
        command = [sys.executable,'-m','lab_runner','test','--mode',mode,'--postgres-version',str(args.postgres_version),
            '--consumer-image',image_id]
        if args.candidate: command+=['--candidate','--candidate-manifest',str(args.candidate_manifest.resolve())]
        if mode=='conversation' and context_enabled:command+=['--context-assembly']
        if mode=='legacy-upgrade' and args.baseline_image:command+=['--baseline-image',args.baseline_image]
        item = {}
        try:
            process = subprocess.run(command,cwd=ROOT,capture_output=True,text=True,
                timeout=1200 if mode=='legacy-upgrade' else 900 if mode in {'lago','native','qualification','conversation'} else 300)
            for line in process.stdout.splitlines():
                if line.startswith('{'): item = json.loads(line)
            validate(item,mode,args.postgres_version,candidate=args.candidate,manifest_sha=manifest_sha,lineage_sha=lineage_sha,
                context_assembly=context_enabled)
            if item['images']['consumer'] != image_id: raise ValueError('image changed between gates')
            if process.returncode != 0: raise ValueError('lane process failed')
            passed = True
        except (OSError,subprocess.TimeoutExpired,ValueError,TypeError):
            passed = False
        safe = export(item)
        safe['required_mode'] = mode
        safe['gate_passed'] = passed
        summary['lanes'].append(safe)
        summary['passed'] = summary['passed'] and passed
        print(json.dumps(safe),flush=True)
    args.export.parent.mkdir(parents=True,exist_ok=True)
    args.export.write_text(json.dumps(summary,indent=2)+'\n')
    return 0 if summary['passed'] else 1

if __name__ == '__main__': raise SystemExit(main())
