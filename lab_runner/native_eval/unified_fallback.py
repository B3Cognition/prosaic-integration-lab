"""Provider-shaped rejection fixtures through the installed unified CLI."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from . import fixture_cli
from .cases import SOURCE, prepare_case, grade
from .unified import api_fixture, require_unified
from .unified_benchmark import _invoke


def prepare_operator(root, url, *, claude='quota', codex='quota',
                     order=('claude', 'codex', 'local'), api_config=None):
    """Operator files live outside the strictly graded assignment workspace."""
    sdk=require_unified()
    profiles={}
    for name,backend,scenario in [('claude','claude-code',claude),('codex','codex-cli',codex)]:
        script=root/(name+'-fixture')
        # This trace is host instrumentation outside the workspace, not agent work.
        wrapper=('\nif "--version" not in sys.argv:\n'
            '    with Path(__file__).with_suffix(".calls").open("a") as trace:\n'
            '        trace.write(json.dumps({"backend":'+repr(name)+',"input":Path("calculator.py").read_text()})+"\\n")\n')
        if scenario=='text-quota':
            event=({'type':'assistant','message':{'content':[{'type':'text','text':'partial fixture answer'}]}}
                   if backend=='claude-code' else {'type':'item.completed','item':{'type':'agent_message','text':'partial fixture answer'}})
            wrapper+='    print('+repr(json.dumps(event))+',flush=True)\n'
        actual='quota' if scenario=='text-quota' else scenario
        script.write_text(f'#!{sys.executable}\n'+Path(fixture_cli.__file__).read_text()+wrapper+
                          f'\nraise SystemExit(main({backend!r},{actual!r}))\n')
        script.chmod(0o700)
        profiles[name]=sdk.NativeProfile(backend,'synthetic',name,str(script),permission_mode='workspace-write')
    (root/'native.yml').write_text(json.dumps({'kind':'native','profiles':{n:asdict(p) for n,p in profiles.items()},
                                              'default_profile':'claude'}))
    if api_config is None:
        api=sdk.RuntimeConfig({'local':sdk.EndpointConfig(url,'synthetic-local',features={'streaming':False})},
                              {},'local',allowed_tools=frozenset({'write_file'}))
        api_config=root/'api.yml'
        api_config.write_text(json.dumps({'profiles':{'local':asdict(api.profiles['local'])},
                                          'default_profile':'local','allowed_tools':['write_file']}))
        local='local'
    else:
        api_config=Path(api_config).resolve()
        local=sdk.RuntimeConfig.load(api_config).default_profile
    path=root/'unified.yml'
    path.write_text(json.dumps({'kind':'unified','native_config':str(root/'native.yml'),
        'api_config':str(api_config),'api_quota_keys':{local:'local-service'},
        'pools':{'agents':{'profiles':[local if name=='local' else name for name in order],'cooldown_s':60}},
        'default_pool':'agents','capacity_file':str(root/'capacity.json')}))
    return path


def invoke_case(operator, workspace, *, local_timeout=5, requests=3, tools=1):
    prepare_case('repair',workspace)
    command=[sys.executable,'-I','-m','prosaic_runtime.cli','subagents/repair.md',
        '--source',str(SOURCE),'--config',str(operator/'unified.yml'),'--cwd',str(workspace),'--events','--quiet',
        '--timeout',str(local_timeout+15),'--max-attempts','3','--max-native-attempts','2',
        '--native-permissions','workspace-write','--native-timeout','5','--enable-api',
        '--api-timeout',str(local_timeout),'--max-api-requests',str(requests),'--max-api-tool-calls',str(tools),
        '--max-tool-rounds','8','--max-api-reported-tokens','65536',
        '--allow-tool','read_file','--allow-tool','write_file','--allow-tool','edit_file',
        '--read-root',str(workspace),'--write-path',str(workspace/'calculator.py')]
    return _invoke(command)


def run_fallback_acceptance(*,provenance=None):
    sdk=require_unified()
    checks={};rows=[]
    with tempfile.TemporaryDirectory(prefix='lab-provider-fallback-') as temporary:
        root=Path(temporary)

        def run(name, *, claude='quota',codex='quota',mode='pass',order=('claude','codex','local'),operator=None):
            workspace=root/(name+'-workspace');workspace.mkdir()
            with api_fixture(mode) as (url,requests):
                if operator is None:
                    operator=root/name;operator.mkdir()
                    prepare_operator(operator,url,claude=claude,codex=codex,order=order)
                else:
                    # Keep learned capacity/native executables; refresh only the owned fixture URL.
                    document=json.loads((operator/'api.yml').read_text())
                    document['profiles']['local']['base_url']=url
                    (operator/'api.yml').write_text(json.dumps(document))
                before={n:len((operator/(n+'-fixture.calls')).read_text().splitlines())
                        if (operator/(n+'-fixture.calls')).exists() else 0 for n in ('claude','codex')}
                result,events=invoke_case(operator,workspace)
                info=result['metadata']['unified_execution_v1']
                calls={n:len((operator/(n+'-fixture.calls')).read_text().splitlines())-before[n]
                       if (operator/(n+'-fixture.calls')).exists() else 0 for n in ('claude','codex')}
                row={'scenario':name,'completed':result['exit_code']==0,
                    'taskPassed':grade('repair',workspace,''),'attempts':[a['profile'] for a in info['attempts']],
                    'attemptFailureReasons':[a['failure_reason'] for a in info['attempts']],
                    'safeToFallback':[a['safe_to_fallback'] for a in info['attempts']],
                    'fallbacks':[e['profile'] for e in events if e['event']=='profile_fallback'],
                    'skips':[e['profile'] for e in events if e['event']=='profile_skipped'],
                    'events':events,'nativeCalls':calls,'apiRequests':len(requests),
                    'nativeAttempts':info['native_attempts'],'countedApiRequests':info['api_provider_requests'],
                    'apiToolCalls':info['api_tool_calls'],'recoveryRequired':bool(result['metadata'].get('recovery_required')),
                    'partialFile':(workspace/'partial.txt').exists(),
                    'originalTaskOutput':(workspace/'calculator.py').read_text()=='def add(a, b):\n    return a - b\n',
                    'failureReason':result['metadata'].get('failure_reason')}
                checks[name+'-dispatch-counts']=info['native_attempts']==sum(calls.values()) and info['api_provider_requests']==len(requests)
                rows.append(row)
                return row,operator

        clean,operator=run('double-quota')
        checks['prework-double-quota']=(clean['completed'] and clean['taskPassed'] and clean['attempts']==['claude','codex','local']
            and clean['safeToFallback']==[True,True,False] and clean['fallbacks']==['claude','codex']
            and clean['nativeCalls']=={'claude':1,'codex':1} and clean['apiRequests']==2
            and clean['apiToolCalls']==1 and not clean['partialFile'])
        events=[(e['event'],e.get('profile')) for e in clean['events']]
        checks['selection-event-order']=events.index(('profile_fallback','claude'))<events.index(('profile_selected','codex'))<events.index(('profile_fallback','codex'))<events.index(('profile_selected','local'))
        checks['native-quota-before-work']=not clean['skips'] and all(
            json.loads((operator/(name+'-fixture.calls')).read_text())['input']=='def add(a, b):\n    return a - b\n'
            for name in ('claude','codex'))
        checks['provider-cooldowns-learned']=all(sdk.CapacityStore(operator/'capacity.json').status(n)['state']=='cooling_down' for n in ('claude','codex'))
        again,_=run('persisted-cooldown',operator=operator)
        checks['persisted-rejection-cooldown']=(again['completed'] and again['attempts']==['local'] and again['skips']==['claude','codex'] and again['nativeCalls']=={'claude':0,'codex':0})
        for name,kwargs,attempts,calls,fallbacks,partial in [
            ('claude-tool-partial',{'claude':'effect-quota'},['claude'],{'claude':1,'codex':0},[],True),
            ('codex-tool-partial',{'codex':'effect-quota'},['claude','codex'],{'claude':1,'codex':1},['claude'],True),
            ('claude-text-partial',{'claude':'text-quota'},['claude'],{'claude':1,'codex':0},[],False),
            ('codex-text-partial',{'codex':'text-quota'},['claude','codex'],{'claude':1,'codex':1},['claude'],False)]:
            row,_=run(name,**kwargs)
            checks[name+'-no-replay']=(not row['completed'] and row['recoveryRequired'] and row['attempts']==attempts
                and row['safeToFallback'][-1] is False and row['nativeCalls']==calls and row['fallbacks']==fallbacks
                and row['apiRequests']==0 and row['partialFile']==partial and row['originalTaskOutput'])
        row,_=run('api-tool-partial',mode='effect-reject',order=('local','claude','codex'))
        checks['api-partial-no-replay']=(not row['completed'] and row['recoveryRequired'] and row['taskPassed']
            and row['attempts']==['local'] and row['nativeCalls']=={'claude':0,'codex':0} and row['apiRequests']==2 and not row['fallbacks'])
    checks['temporary-workspace-cleanup']=not root.exists()
    return {'suiteVersion':'unified-provider-fallback-v1','origin':'simulated_provider_rejections',
        'passed':all(checks.values()),'caseCount':len(checks),'checks':checks,'scenarios':rows,
        'liveInvocations':0,'cleanup':'verified' if not root.exists() else 'failed',
        'markdownSha256':hashlib.sha256((SOURCE/'subagents/repair.md').read_bytes()).hexdigest(),
        'provenance':provenance or {}}
