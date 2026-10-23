"""Strict loading for the separate memory experiment and frozen evaluation assets."""
from importlib.resources import files
from jsonschema import Draft202012Validator
from lab_runner.quality.contracts import decode,encode,identifier
from lab_runner.quality.checks import assess_evidence,compare_fields
from lab_runner.quality.suite import resource
from .corpus import Corpus,fields,timestamp,text
from .context import current_index,current_sources


def validate_bundle(bundle):
    bundle=decode(encode(bundle,1048576),1048576)
    fields(bundle,('version','suiteId','cases','corpus','historicalSources'))
    if type(bundle['version']) is not int or bundle['version']!=1:raise ValueError('invalid memory suite')
    identifier(bundle['suiteId']);Corpus(bundle['corpus'],bundle['historicalSources'])
    cases=bundle['cases'];seen=set()
    if type(cases) is not list or not 1<=len(cases)<=12:raise ValueError('memory case limit')
    for c in cases:
        fields(c,('caseId','task','records','recordIndex','draft','expected','requiredRecords','relevantRecords',
                  'minimumCalls','kind','tenantId','asOf','entity','topics','goldEpisodes','family'))
        identifier(c['caseId']);identifier(c['tenantId']);identifier(c['family']);timestamp(c['asOf'])
        if len(c['caseId'])>64 or c['caseId'] in seen or c['kind']!='ordinary' or c['draft'] is not None or c['minimumCalls']!=1:
            raise ValueError('invalid memory case')
        seen.add(c['caseId']);text(c['entity'],64);text(c['task'],4096)
        if type(c['topics']) is not list or len(c['topics'])>8:raise ValueError('invalid task topics')
        for topic in c['topics']:text(topic,64)
        if type(c['goldEpisodes']) is not list or len(c['goldEpisodes'])>128:raise ValueError('invalid memory gold')
        for eid in c['goldEpisodes']:identifier(eid)
        if len(set(c['goldEpisodes']))!=len(c['goldEpisodes']):raise ValueError('duplicate memory gold')
        if type(c['records']) is not dict or not 1<=len(c['records'])<=16:raise ValueError('current source limit')
        current_index(c['recordIndex']);current_sources(c['records'])
        if type(c['recordIndex']) is not list or len(c['recordIndex'])!=len(c['records']):raise ValueError('current index limit')
        for key,record in c['records'].items():
            identifier(key)
            if record['recordId']!=key:raise ValueError('source ID')
        if not set(c['requiredRecords'])<=set(c['relevantRecords'])<=set(c['records']) or not 1<=len(c['requiredRecords'])<=4:
            raise ValueError('required source limit')
        clean=assess_evidence(c,list(c['records'].values()))
        if clean['missingRecords'] or compare_fields(clean['answer'],c['expected']):raise ValueError('inconsistent current assertions')
        Draft202012Validator(decode(resource('answer.schema.json'))).validate(c['expected'])
    return bundle


def load_suite():
    root=files(__package__).joinpath('data')
    suite=decode(root.joinpath('retrieval-memory-v1.json').read_bytes(),262144)
    suite.update(corpus=decode(root.joinpath('corpus.json').read_bytes(),262144),
                 historicalSources=decode(root.joinpath('historical-sources.json').read_bytes(),262144))
    result=validate_bundle(suite)
    if result['suiteId']!='retrieval-memory-v1' or len(result['cases'])!=12:raise ValueError('invalid evaluation suite')
    from .freeze import verify
    verify(result,decode(root.joinpath('development-freeze.json').read_bytes()),
           decode(root.joinpath('evaluation-freeze.json').read_bytes()))
    return result
