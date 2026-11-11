"""Host-only synthetic ground truth and fixture answers. Never import in execution."""

from copy import deepcopy

from prosaic_integration_lab.sue_review.sources import freeze_documents

from .cases import load_cases
from .contracts import digest

_ASSERTIONS = (
    ('ISSUES_FOUND',['contradiction'],1,2),
    ('ISSUES_FOUND',['undefined_term'],1,2),
    ('ISSUES_FOUND',['untestable_acceptance'],1,2),
    ('ISSUES_FOUND',['missing_failure_behavior'],1,2),
    ('ISSUES_FOUND',['unsupported_assumption'],1,2),
    ('INSUFFICIENT_CONTEXT',['missing_context'],1,2),
    ('NO_KNOWN_ISSUES',[],1,4),
    ('ISSUES_FOUND',['contradiction'],1,2),
)


def load_keys():
    cases = load_cases()
    return {case_id:{'caseSha256':digest(cases[case_id]),'assessment':assessment,
        'issues':deepcopy(issues),'support':[{'sourceId':'spec','startLine':start,'endLine':end}]}
        for case_id,(assessment,issues,start,end) in zip(sorted(cases),_ASSERTIONS,strict=True)}


def fixture_answer(case, key):
    frozen = freeze_documents(case['sources'])
    hashes = {source['sourceId']:source['textSha256'] for source in frozen['sources']}
    return {'caseId':case['caseId'],'assessment':key['assessment'],'issues':deepcopy(key['issues']),
        'citations':[{**item,'textSha256':hashes[item['sourceId']]} for item in key['support']]}
