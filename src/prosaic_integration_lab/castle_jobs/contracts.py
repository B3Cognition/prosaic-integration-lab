"""Bounded frozen text and strict advisory classifier contracts."""

from dataclasses import dataclass, fields
import math

# These JSON helpers have no SDK or optional-engine imports. Reuse the Lab's
# strict duplicate-key/nonfinite/depth/byte limits rather than weakening them.
from ..sue_review.contracts import ReviewError as CastleJobError, decode, digest, encoded, own, reference, text_digest

KINDS = {'judge', 'entity_refinement', 'corpus_origin'}
LABELS = {'PERSON', 'PROJECT', 'TOPIC', 'COMMON_WORD', 'AMBIGUOUS'}


@dataclass(frozen=True)
class JobSettings:
    enabled: bool = False
    lifetime_s: int = 86400
    max_tokens: int = 4096
    timeout_s: int = 60

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise CastleJobError('invalid_job_settings')
        for name, ceiling in (('lifetime_s',604800),('max_tokens',16384),('timeout_s',60)):
            if type(getattr(self,name)) is not int or not 1 <= getattr(self,name) <= ceiling:
                raise CastleJobError('invalid_job_limit')

    @classmethod
    def from_mapping(cls, value):
        if value is None:
            return cls()
        if type(value) is not dict or type(value.get('enabled')) is not bool or set(value)-{f.name for f in fields(cls)}:
            raise CastleJobError('invalid_job_settings')
        if not value['enabled'] and set(value) != {'enabled'}:
            raise CastleJobError('disabled_job_settings')
        return cls(**value)


def _text(value, maximum, *, empty=False):
    if type(value) is not str or (not empty and not value.strip()) or len(value.encode('utf-8')) > maximum:
        raise CastleJobError('invalid_job_text')
    return value


def freeze_candidates(candidates):
    candidates = own(candidates)
    if type(candidates) is not list or not 1 <= len(candidates) <= 100:
        raise CastleJobError('candidate_count')
    frozen, seen, total = [], set(), 0
    for item in candidates:
        required = {'sourceId','text','revision','reference'}
        if type(item) is not dict or not required <= set(item) or set(item)-required-{'textSha256','provenance'}:
            raise CastleJobError('invalid_candidate')
        if not reference(item['sourceId']) or item['sourceId'] in seen:
            raise CastleJobError('invalid_candidate')
        seen.add(item['sourceId'])
        _text(item['text'],65536)
        total += len(item['text'].encode('utf-8'))
        if total > 65536:
            raise CastleJobError('candidate_text_limit')
        for key in ('revision','reference'):
            if item[key] is not None:
                _text(item[key],256)
        sha = text_digest(item['text'])
        if 'textSha256' in item and item['textSha256'] != sha:
            raise CastleJobError('candidate_identity_mismatch')
        provenance = item.get('provenance')
        if provenance is not None and type(provenance) is not dict:
            raise CastleJobError('invalid_candidate_provenance')
        frozen.append({**item,'textSha256':sha,'provenance':provenance})
    return own(frozen)


def freeze_entities(entities, candidates):
    entities = own(entities)
    if type(entities) is not list or not 1 <= len(entities) <= 25:
        raise CastleJobError('entity_count')
    sources = {s['sourceId']:s['text'].splitlines() for s in candidates}
    seen = set()
    for entity in entities:
        if type(entity) is not dict or set(entity) != {'name','currentType','contexts'}:
            raise CastleJobError('invalid_entity')
        _text(entity['name'],128)
        if entity['name'] in seen or type(entity['currentType']) is not str or entity['currentType'] not in {'person','project','topic','uncertain'}:
            raise CastleJobError('invalid_entity')
        seen.add(entity['name'])
        contexts = entity['contexts']
        if type(contexts) is not list or len(contexts) > 3:
            raise CastleJobError('invalid_entity_context')
        for context in contexts:
            if type(context) is not dict or set(context) != {'sourceId','line','quote'}:
                raise CastleJobError('invalid_entity_context')
            _text(context['quote'],960)
            if not reference(context['sourceId']):
                raise CastleJobError('invalid_entity_context')
            lines = sources.get(context['sourceId'],[])
            line = context['line']
            if (len(context['quote']) > 240 or type(line) is not int or not 1 <= line <= len(lines)
                    or context['quote'] not in lines[line-1]):
                raise CastleJobError('entity_context_mismatch')
    return entities


def validate_request(request):
    if type(request) is not dict or set(request) != {'kind','candidates','query','topN','entities','policy','owner','requestSignature'}:
        raise CastleJobError('invalid_job_request')
    check = dict(request)
    signature = check.pop('requestSignature')
    if signature != digest(check) or freeze_candidates(request['candidates']) != request['candidates']:
        raise CastleJobError('request_identity_mismatch')
    if request['kind'] not in KINDS:
        raise CastleJobError('invalid_job_kind')
    JobSettings.from_mapping({'enabled':True,**request['policy']})
    if request['kind'] == 'judge':
        _text(request['query'],2048)
        if type(request['topN']) is not int or not 1 <= request['topN'] <= min(50,len(request['candidates'])) or request['entities'] is not None:
            raise CastleJobError('invalid_judge_request')
    elif request['query'] is not None or request['topN'] is not None:
        raise CastleJobError('invalid_classifier_request')
    elif request['kind'] == 'entity_refinement':
        freeze_entities(request['entities'],request['candidates'])
    elif request['entities'] is not None:
        raise CastleJobError('invalid_origin_request')


def _classification(request, value):
    if type(value) is not dict:
        raise CastleJobError('invalid_classification')
    kind = request['kind']
    if kind == 'judge':
        n = request['topN']
        indices = value.get('ranked_indices')
        if (set(value) != {'ranked_indices'} or type(indices) is not list or len(indices) != n
                or any(type(i) is not int for i in indices) or set(indices) != set(range(n))):
            raise CastleJobError('invalid_ranking_permutation')
    elif kind == 'entity_refinement':
        entries = value.get('classifications')
        if set(value) != {'classifications'} or type(entries) is not list or len(entries) != len(request['entities']):
            raise CastleJobError('invalid_classifications')
        for entry, expected in zip(entries,request['entities'],strict=True):
            if (type(entry) is not dict or set(entry) != {'name','label','reason'} or entry['name'] != expected['name']
                    or type(entry['label']) is not str or entry['label'] not in LABELS):
                raise CastleJobError('invalid_classification')
            _text(entry['reason'],480,empty=True)
            if len(entry['reason']) > 120:
                raise CastleJobError('invalid_classification_reason')
    else:
        required = {'is_ai_dialogue_corpus','confidence','primary_platform','user_name','agent_persona_names','evidence'}
        if set(value) != required or type(value['is_ai_dialogue_corpus']) is not bool:
            raise CastleJobError('invalid_origin')
        confidence = value['confidence']
        if type(confidence) not in (int,float) or not 0 <= confidence <= 1 or not math.isfinite(confidence):
            raise CastleJobError('invalid_origin_confidence')
        for key in ('primary_platform','user_name'):
            if value[key] is not None:
                _text(value[key],256)
        for key in ('agent_persona_names','evidence'):
            if type(value[key]) is not list or len(value[key]) > 20:
                raise CastleJobError('invalid_origin_list')
            for text in value[key]:
                _text(text,256 if key == 'agent_persona_names' else 512)
        # Preserve the legacy user/persona distinction without changing corpora.
        if value['user_name']:
            value['agent_persona_names'] = [p for p in value['agent_persona_names'] if p.casefold() != value['user_name'].casefold()]
    return value


def interpret(request, raw, *, failure=None):
    value, reason = None, failure
    if reason is None:
        try:
            value = _classification(request,decode(raw))
        except CastleJobError as error:
            reason = error.code
    result = {'advisory':True,'kind':request['kind'],'result':value,
              'audit':{'fallback':reason is not None,'reason':reason,
                       'responseSha256':text_digest(raw) if raw is not None else None}}
    if request['kind'] == 'judge':
        ordering = (value['ranked_indices'] + list(range(request['topN'],len(request['candidates'])))) if value is not None else range(len(request['candidates']))
        result['rankedSourceIds'] = [request['candidates'][i]['sourceId'] for i in ordering]
    return result
