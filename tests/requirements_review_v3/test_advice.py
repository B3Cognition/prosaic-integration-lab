from copy import deepcopy

def test_compact_advice_preserves_distinct_content_and_all_provenance():
    from prosaic_integration_lab.sue_review.reporting import compact_advice
    citation={'sourceId':'spec','sourceLine':2,'quote':'No retry behavior.'}
    premise={'statement':'No retry behavior.','kind':'stated','evidence_lines':[2]}
    question={'questions':['What happens on failure?'],'status':'open','addressed_by':None}
    report={'advisory':True,'terminal':'BOUNDED_STOP','claim':'Usable?',
        'acceptedTurns':5,'meaning':'Advisory, not approval.',
        'sourcesSha256':'a'*64,'sources':[{'sourceId':'spec','textSha256':'b'*64,'revision':'r1'}],
        'coverage':{'missing':['DISTINGUISH'],'dimensions':[{'operator':'DEFINE','turn':1,'status':'examined'}],
                    'issues':[{**question,'turn':2},{**question,'turn':4}],
                    'open_issues':[{**question,'turn':2},{**question,'turn':4}]},
        'citations':[{**citation,'turn':1},{**citation,'turn':3},
                     {**citation,'turn':4,'sourceId':'other'}],
        'premises':[premise,premise,{**premise,'kind':'inferred'}],
        'openQuestions':['What happens on failure?']*2,'witnesses':[],
        'runId':'private-bookkeeping','reportedTokens':3000}
    before=deepcopy(report)
    result=compact_advice(report)
    assert result['citations']==[{**citation,'turns':[1,3]},
                                {**citation,'sourceId':'other','turns':[4]}]
    assert result['premises']==[premise,{**premise,'kind':'inferred'}]
    assert result['coverage']['issues']==[{**question,'turns':[2,4]}]
    assert 'open_issues' not in result['coverage']
    assert result['openQuestions']==['What happens on failure?']
    assert result['coverage']['missing']==['DISTINGUISH']
    assert result['sources']==report['sources'] and result['terminal']=='BOUNDED_STOP'
    assert 'runId' not in result and 'reportedTokens' not in result
    assert report==before and compact_advice(None) is None


def test_final_wire_projection_compacts_advice_without_mutating_saved_arguments():
    import json
    from types import SimpleNamespace
    from prosaic_runtime import Result
    from lab_runner.requirements_review_v3 import project_stage_arguments
    report={'advisory':True,'terminal':'BOUNDED_STOP','claim':'A claim',
        'acceptedTurns':2,'meaning':'Not approval','sourcesSha256':'a'*64,'sources':[],
        'coverage':{'missing':['DEFINE'],'issues':[]},'citations':[],
        'premises':[],'witnesses':[],'openQuestions':['Unknown?','Unknown?'],
        'turnEvidence':[{'turn':1,'premises':[],'witnesses':[],'openQuestions':['Unknown?']},
                        {'turn':2,'premises':[],'witnesses':[],'openQuestions':['Unknown?']}]}
    original={'request':{'strategyAdvice':report},'artifacts':{}};before=deepcopy(original);seen=[]
    def execute(raw,**options):
        seen.append((json.loads(raw),options));return Result(0,'{}','')
    project_stage_arguments(SimpleNamespace(id='requirements-v1/final'),json.dumps(original),execute=execute)
    advice=seen[0][0]['request']['strategyAdvice']
    assert advice['openQuestions']==['Unknown?']
    assert advice['questionOrigins']==[{'value':'Unknown?','turns':[1,2]}]
    assert seen[0][1]['allowed_tools']==frozenset() and original==before
