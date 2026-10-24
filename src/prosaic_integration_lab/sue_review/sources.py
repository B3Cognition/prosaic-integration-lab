"""Owned verbatim evidence and source-local line mappings; no retrieval here."""

import hashlib
import re

from .contracts import ReviewError, digest, own, reference, text_digest


def _freeze(records, capture=None, snapshot_digest=None):
    total, line_map = 0, []
    if not 1 <= len(records) <= 16:
        raise ReviewError('source_count')
    seen = set()
    for source in records:
        source_id, text = source['sourceId'], source['text']
        if not reference(source_id) or source_id in seen or type(text) is not str or not text.strip():
            raise ReviewError('invalid_source')
        seen.add(source_id)
        try:
            total += len(text.encode('utf-8'))
        except UnicodeError:
            raise ReviewError('invalid_source') from None
        if total > 65536:
            raise ReviewError('source_limit')
        for key in ('revision','reference'):
            value = source[key]
            if value is not None and (type(value) is not str or not value or len(value.encode('utf-8')) > 256):
                raise ReviewError('invalid_source_metadata')
        source['textSha256'] = text_digest(text)
        line_map.extend({'sourceId':source_id,'sourceLine':n} for n in range(1,len(text.splitlines())+1))
    value = own({'schemaVersion':1,'sources':records,'lineMap':line_map,'capture':capture,'snapshotDigest':snapshot_digest})
    return own({**value,'sourcesSha256':digest(value)})


def freeze_documents(sources):
    if type(sources) is not list:
        raise ReviewError('invalid_sources')
    records = []
    for source in own(sources):
        if type(source) is not dict or not {'sourceId','text'} <= set(source) or set(source)-{'sourceId','text','revision','reference'}:
            raise ReviewError('invalid_source')
        records.append({**source,'revision':source.get('revision'),'reference':source.get('reference'),'provenance':None})
    return _freeze(records)


def source_lines(frozen):
    return [line for source in frozen['sources'] for line in source['text'].splitlines()]


def verify_frozen(frozen):
    candidate = own(frozen)
    required = {'schemaVersion','sources','lineMap','capture','snapshotDigest','sourcesSha256'}
    if type(candidate) is not dict or set(candidate) != required or type(candidate['schemaVersion']) is not int or candidate['schemaVersion'] != 1 or type(candidate['sources']) is not list:
        raise ReviewError('invalid_sources')
    identity = candidate.pop('sourcesSha256',None)
    if identity != digest(candidate):
        raise ReviewError('source_identity_mismatch')
    records = candidate['sources']
    if any(type(s) is not dict or set(s) != {'sourceId','text','revision','reference','provenance','textSha256'} for s in records):
        raise ReviewError('invalid_source')
    if candidate['capture'] is None:
        if candidate['snapshotDigest'] is not None or any(s['provenance'] is not None for s in records):
            raise ReviewError('invalid_sources')
        rebuilt = freeze_documents([{k:s[k] for k in ('sourceId','text','revision','reference')} for s in records])
    else:
        bundle = {'schema_version':1,'sources':[s['provenance'] for s in records],
                  'texts':[s['text'] for s in records],'digest':candidate['snapshotDigest']}
        rebuilt = freeze_castle_snapshot({'scope':candidate['capture'],'bundle':bundle},expected_scope=candidate['capture'])
    if rebuilt != frozen:
        raise ReviewError('source_identity_mismatch')
    return rebuilt


def freeze_castle_snapshot(capture, *, expected_scope):
    capture = own(capture)
    if type(capture) is not dict or set(capture) != {'bundle','scope'} or capture['scope'] != expected_scope:
        raise ReviewError('source_scope_mismatch')
    scope, bundle = capture['scope'], capture['bundle']
    required_scope = {'tenant_id','actor_id','billing_account_id','namespace','binding_sha256','allowed_wings'}
    if type(scope) is not dict or set(scope) != required_scope or any(not reference(scope.get(k)) for k in ('tenant_id','actor_id','billing_account_id','namespace')):
        raise ReviewError('invalid_source_scope')
    if type(scope['binding_sha256']) is not str or re.fullmatch('[0-9a-f]{64}',scope['binding_sha256']) is None or type(scope['allowed_wings']) is not list or not scope['allowed_wings']:
        raise ReviewError('invalid_source_scope')
    if type(bundle) is not dict or set(bundle) != {'sources','texts','schema_version','digest'} or type(bundle['schema_version']) is not int or bundle['schema_version'] != 1:
        raise ReviewError('invalid_snapshot')
    payload = {k:v for k,v in bundle.items() if k != 'digest'}
    if bundle['digest'] != digest(payload) or type(bundle['sources']) is not list or type(bundle['texts']) is not list or len(bundle['sources']) != len(bundle['texts']):
        raise ReviewError('snapshot_identity_mismatch')
    records = []
    source_keys = {'record_id','text_sha256','revision','representation','wing','captured_at','source_id'}
    for source,text in zip(bundle['sources'],bundle['texts'],strict=True):
        if type(source) is not dict or set(source) != source_keys or type(source['record_id']) is not str or not source['record_id'] or source['wing'] not in scope['allowed_wings'] or source['text_sha256'] != text_digest(text):
            raise ReviewError('invalid_snapshot_source')
        records.append({'sourceId':'castle:'+hashlib.sha256(source['record_id'].encode()).hexdigest()[:32],
                        'text':text,'revision':source['revision'],'reference':None,'provenance':source})
    return _freeze(records, scope, bundle['digest'])
