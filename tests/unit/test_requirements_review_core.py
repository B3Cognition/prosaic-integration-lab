from copy import deepcopy
import hashlib

import pytest


def suite():
    from lab_runner.requirements_review_v1.cases import load_cases, public_task
    from lab_runner.requirements_review_v1.host_keys import load_keys, fixture_answer
    from lab_runner.requirements_review_v1.scoring import grade
    return load_cases(),public_task,load_keys(),fixture_answer,grade


def test_eight_frozen_cases_have_independent_known_issue_keys():
    cases,task,keys,answer,grade=suite()
    assert len(cases)==len(keys)==8
    assert [keys[k]['issues'] for k in sorted(keys)]==[
        ['contradiction'],['undefined_term'],['untestable_acceptance'],
        ['missing_failure_behavior'],['unsupported_assumption'],['missing_context'],[],['contradiction']]
    for case_id,case in cases.items():
        assert grade(case,keys[case_id],answer(case,keys[case_id]))['passed']
        request=task(case)
        assert 'expected' not in request and 'key' not in request
        source=request['evidence']['sources'][0]
        assert source['textSha256']==hashlib.sha256(source['text'].encode()).hexdigest()


@pytest.mark.parametrize('mutation',['issue','extra_issue','assessment','hash','range','source','missing_citation','duplicate','case'])
def test_strict_grader_rejects_wrong_known_issues_and_support(mutation):
    cases,_,keys,answer,grade=suite();case=cases['requirements-01'];key=keys[case['caseId']]
    response=answer(case,key)
    if mutation=='issue':response['issues']=[]
    elif mutation=='extra_issue':response['issues'].append('missing_context')
    elif mutation=='assessment':response['assessment']='NO_KNOWN_ISSUES'
    elif mutation=='hash':response['citations'][0]['textSha256']='0'*64
    elif mutation=='range':response['citations'][0]['endLine']=1
    elif mutation=='source':response['citations'][0]['sourceId']='foreign'
    elif mutation=='missing_citation':response['citations']=[]
    elif mutation=='duplicate':response['issues']*=2
    else:response['caseId']='foreign'
    assert not grade(case,key,response)['passed']


def test_resolved_diagnostic_cannot_rescue_a_wrong_final_answer():
    cases,_,keys,answer,grade=suite();case=cases['requirements-01'];key=keys[case['caseId']]
    response=answer(case,key);response['issues']=[];response['assessment']='NO_KNOWN_ISSUES'
    result=grade(case,key,response)
    assert not result['passed'] and 'terminal' not in result


def test_case_key_digest_and_line_ranges_bind_exact_frozen_source():
    cases,_,keys,answer,grade=suite();case=cases['requirements-01'];key=keys[case['caseId']]
    response=answer(case,key);changed=deepcopy(case);changed['sources'][0]['text']+='Changed.\n'
    with pytest.raises(ValueError):grade(changed,key,response)


def test_public_execution_modules_do_not_import_host_keys_or_scorer():
    import json
    import os
    from pathlib import Path
    import subprocess
    import sys
    root=Path(__file__).resolve().parents[2]/'lab_runner'/'requirements_review_v1'
    result=subprocess.run([sys.executable,'-c',
        'import sys,json; import lab_runner.requirements_review_v1.execution; '
        'print(json.dumps([m for m in sys.modules if m.endswith(("host_keys","scoring"))]))'],
        cwd=root.parents[1],env=dict(os.environ,PYTHONPATH=str(root.parents[1]/'src')+os.pathsep+str(root.parents[1])),
        capture_output=True,text=True,check=True)
    assert json.loads(result.stdout)==[]
