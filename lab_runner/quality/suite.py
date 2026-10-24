"""Versioned, packaged synthetic cases. Private assertions never enter prompts."""
from copy import deepcopy
from importlib.resources import files
from jsonschema import Draft202012Validator
from .contracts import decode, encode, identifier, integer

AGENT_NAMES=('reviewer','critic','author','review-corrector')


def resource(name):
    if name not in {'evidence-review-v1.json','answer.schema.json','review.schema.json',
                    'reviewer.md','critic.md','author.md','review-corrector.md','sdk-provenance.json','sdk-provenance-public.json',
                    'sdk-provenance-pre-unified.json'}:
        raise ValueError('unknown benchmark resource')
    return files(__package__).joinpath('data', name).read_text(encoding='utf-8')


def agent_prose(name):
    if name not in AGENT_NAMES:
        raise ValueError('unknown benchmark agent')
    schema='review' if name in {'critic','review-corrector'} else 'answer'
    return resource(name+'.md')+'\nOutput JSON schema:\n'+encode(decode(resource(schema+'.schema.json'))).decode('utf-8')+'\n'


def load_suite():
    suite = decode(resource('evidence-review-v1.json'), 262144)
    if set(suite) != {'version','suiteId','cases'} or suite['version'] != 1 or suite['suiteId'] != 'evidence-review-v1':
        raise ValueError('invalid benchmark suite')
    if len(suite['cases']) != 10: raise ValueError('invalid benchmark cases')
    seen = set()
    for case in suite['cases']:
        if set(case) != {'caseId','task','records','recordIndex','draft','expected',
                         'requiredRecords','relevantRecords','minimumCalls','kind'}:
            raise ValueError('invalid benchmark case')
        identifier(case['caseId'])
        if case['caseId'] in seen: raise ValueError('duplicate benchmark case')
        seen.add(case['caseId'])
        integer(case['minimumCalls'],1,16)
        if case['kind'] not in {'ordinary','repair'}: raise ValueError('invalid case kind')
        if not set(case['requiredRecords']) <= set(case['relevantRecords']) <= set(case['records']):
            raise ValueError('invalid benchmark records')
        if len(case['records']) > 16: raise ValueError('benchmark record limit')
        for key in case['records']: identifier(key)
        Draft202012Validator(decode(resource('answer.schema.json'))).validate(case['expected'])
    return suite


def public_case(case):
    return deepcopy({key:case[key] for key in ('caseId','task','recordIndex','draft')})
