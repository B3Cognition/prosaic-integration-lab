"""Case-neutral model contracts. No host answer-key or scoring imports."""

from copy import deepcopy

from prosaic_integration_lab.sue_review.contracts import decode, digest, encoded

ISSUES = {
    'contradiction':'Two requirements cannot both hold for the same situation.',
    'undefined_term':'A decision depends on a term with no supplied definition.',
    'untestable_acceptance':'An acceptance statement lacks an observable measurable criterion.',
    'missing_failure_behavior':'A required operation lacks specified failure, timeout or recovery behavior.',
    'unsupported_assumption':'A stated design assumption has no supplied establishing rule or evidence.',
    'missing_context':'An explicitly required external source or policy is absent.',
}
CITATION = {'type':'object','additionalProperties':False,
    'required':['sourceId','textSha256','startLine','endLine'],'properties':{
        'sourceId':{'type':'string','minLength':1,'maxLength':128},
        'textSha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},
        'startLine':{'type':'integer','minimum':1},'endLine':{'type':'integer','minimum':1}}}
FINAL_SCHEMA = {'type':'object','additionalProperties':False,
    'required':['caseId','assessment','issues','citations'],'properties':{
        'caseId':{'type':'string','minLength':1,'maxLength':64},
        'assessment':{'enum':['ISSUES_FOUND','INSUFFICIENT_CONTEXT','NO_KNOWN_ISSUES']},
        'issues':{'type':'array','uniqueItems':True,'maxItems':6,'items':{'enum':list(ISSUES)}},
        'citations':{'type':'array','minItems':1,'maxItems':16,'uniqueItems':True,'items':CITATION}}}
CRITIC_SCHEMA = {'type':'object','additionalProperties':False,'required':['feedback'],
    'properties':{'feedback':{'type':'string','minLength':1,'maxLength':2048}}}
LIMITS = {'calls':30,'tokens':65536,'elapsedSeconds':120}
STRATEGIES = ('direct','critic_author','sue')
SDK_VERSIONS = {'b3-prosaic':'0.4.1','b3-prosaic-runtime':'0.9.8','b3-prosaic-harness':'0.9.4'}
ENGINE_IDENTITY = 'bbde4669d1eb069dcb8c72e121cd08be4ca953b349f9243b9e650e0d1b596f0b'


def schema():
    return deepcopy(FINAL_SCHEMA)
