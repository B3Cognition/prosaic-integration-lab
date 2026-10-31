"""Opt-in memory benchmark CLI. Default invocation enables and executes nothing."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

from . import VERSION
from .dataset import freeze, load_frozen
from .storage import exclusive, read, require
from .retrieval_policy import LEGACY_POLICY, POLICIES
from . import execution


def initialize(directory,questions=3):
    directory=Path(directory)
    require(directory.is_absolute() and not directory.exists(),'fresh absolute example directory required')
    require(type(questions) is int and 1<=questions<=1000,'question count must be 1..1000')
    directory.mkdir(mode=0o700,parents=True);source=directory/'sources';source.mkdir(mode=0o700)
    text='Memory stays disabled by default.\n\nRuntime executes models. Harness owns workflow state.\n'
    (source/'example.md').write_bytes(text.encode());(source/'example.md').chmod(0o600)
    cases=[]
    for index in range(questions):
        question,query=(('What is the memory default?','Memory') if index%3==0 else
                        ('Who executes models?','Runtime') if index%3==1 else
                        ('Which component owns workflow state?','Harness'))
        cases.append(dict(id=f'q{index+1:04d}',question=question,queries=[query],sourceIds=['example']))
    exclusive(directory/'dataset.json',dict(version=1,sources=[dict(id='example',path='example.md',wing='notes')],cases=cases))
    exclusive(directory/'policy.json',dict(version=1,namespace='example-owner',root=str(source),allowedWings=['notes']))
    exclusive(directory/'live.example.json',dict(version=1,enabled=False,review=False,
        runtime=dict(base_url='http://127.0.0.1:8000/v1',model='REPLACE',api_key_file='/absolute/private/key'),
        castle=dict(worker_command=['/absolute/worker/bin/python','-I','-m','prosaic_castle.provider_worker'],
            palace_path='/absolute/private/frozen-palace',config_path='/absolute/private/castle-config.json'),
        limits=dict(providerRequests=questions*3,reportedTokens=questions*3*32768,timeoutSeconds=3600)))
    return dict(templateOnly=True,questions=questions,distinctSyntheticQuestions=min(3,questions),
                warning='Repeated synthetic examples test mechanics, not review quality. Replace with independent questions and sources.')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command')
    p=sub.add_parser('audit-fixture',help='explicit synthetic answer-span audit; no real model or memory provider')
    p.add_argument('--output',required=True)
    p.add_argument('--case',choices=('omitted','complete','unavailable','unknown-usage'),default='omitted')
    init=sub.add_parser('init');init.add_argument('--directory',required=True);init.add_argument('--questions',type=int,default=3)
    for command in ('validate','freeze'):
        p=sub.add_parser(command);p.add_argument('--dataset');p.add_argument('--policy');p.add_argument('--key');p.add_argument('--castle-map')
        p.add_argument('--retrieval-policy',choices=POLICIES)
        from .generation import PROFILES
        p.add_argument('--generation-profile',choices=PROFILES)
        p.add_argument('--execution-profile',choices=execution.PROFILES)
        if command=='freeze':p.add_argument('--output',required=True)
        else:p.add_argument('--frozen')
    p=sub.add_parser('run');p.add_argument('--frozen',required=True);p.add_argument('--output',required=True)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--fixture',action='store_true');mode.add_argument('--live',action='store_true')
    p.add_argument('--config');p.add_argument('--review',action='store_true')
    for command in ('status','replay','report','grade-template'):
        p=sub.add_parser(command);p.add_argument('--frozen',required=True);p.add_argument('--run',required=True)
        if command in ('report','grade-template'):p.add_argument('--output')
        if command=='report':p.add_argument('--verdict')
    args=parser.parse_args(argv)
    try:
        if args.command is None:result=dict(enabled=False,executed=False,version=VERSION)
        elif args.command=='audit-fixture':
            from .span_audit_fixture import run_fixture
            result=run_fixture(args.output,case=args.case)
        elif args.command=='init':result=initialize(args.directory,args.questions)
        elif args.command in ('freeze','validate'):
            if args.command=='validate' and args.frozen:
                require(not any((args.dataset,args.policy,args.key,args.castle_map,args.retrieval_policy,args.generation_profile,args.execution_profile)),'mixed validation modes')
                bundle=load_frozen(args.frozen);result=dict(valid=True,caseCount=len(bundle['cases']),modelCalls=0)
            else:
                require(args.dataset and args.policy,'dataset and trusted policy required')
                if args.command=='freeze':
                    result=freeze(args.dataset,args.policy,args.output,key_path=args.key,castle_map_path=args.castle_map,
                                  retrieval_policy=args.retrieval_policy or LEGACY_POLICY,
                                  generation_profile=args.generation_profile or 'canonical-v1',
                                  execution_profile=args.execution_profile or execution.LEGACY)
                else:
                    with tempfile.TemporaryDirectory(prefix='memory-benchmark-validate-') as tmp:
                        result=freeze(args.dataset,args.policy,Path(tmp).resolve()/'frozen',key_path=args.key,castle_map_path=args.castle_map,
                                      retrieval_policy=args.retrieval_policy or LEGACY_POLICY,
                                      generation_profile=args.generation_profile or 'canonical-v1',
                                      execution_profile=args.execution_profile or execution.LEGACY)
                    result.update(valid=True,modelCalls=0)
        elif args.command=='run':
            require(args.fixture or args.live,'explicit --fixture or --live required')
            require(not args.fixture or args.config is None,'fixture refuses live configuration')
            from .runner import run
            result=run(args.frozen,args.output,fixture=args.fixture,review=args.review,config_path=args.config)
        elif args.command in ('replay','status'):
            from .runner import replay
            if args.command=='status' and not (Path(args.run)/'results-seal.json').exists():
                bundle=load_frozen(args.frozen);manifest=read(Path(args.run)/'run.json')
                result=dict(sealed=False,scheduled=len(manifest['schedule']),semanticQuality='unmeasured',
                    allowance=read(Path(args.run)/'allowance.json'),caseCount=len(bundle['cases']))
            else:result=replay(args.frozen,args.run)
        else:
            from .scoring import report,grade_template
            result=grade_template(args.frozen,args.run) if args.command=='grade-template' else report(args.frozen,args.run,verdict_path=args.verdict)
        output=getattr(args,'output',None) if args.command in ('report','grade-template') else None
        if output:
            path=Path(output).resolve()
            require(not path.is_relative_to(Path(args.run).resolve()) and not path.is_relative_to(Path(args.frozen).resolve()),
                    'reports/adjudications must be additive outside sealed input/result trees')
            exclusive(path,result)
        print(json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False))
        return 0
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        print(f'memory benchmark refused: {error}',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
