"""Consumer-owned safe trajectory projection; observations confer no authority."""
from copy import deepcopy
import hashlib
import hmac
import os
from pathlib import Path
import stat
from threading import RLock

from jsonschema import Draft202012Validator

from .quality.allowance import private_write
from .quality.contracts import decode, digest, encode, sha

EVENTS = {
    'runtime': ('invocation_started','invocation_completed','provider_request_started',
                'provider_request_completed','tool_started','tool_completed'),
    'harness': ('run_started','transition_committed','waiting_committed',
                'recovery_committed','blocked_committed','run_completed'),
}
OUTCOMES = {'runtime': ('completed','cancelled','timed_out','admission_failure',
    'critical_hook_error','budget_failure','execution_failure'),
    'harness': ('running','waiting','blocked','completed','rejected')}
REASONS = ('tool_effect_uncertain','tool_journal_failed','tool_identity_conflict','unknown',
    'cancelled','invocation_timeout','inspection_timeout','budget_exceeded','provider_request_limit',
    'tool_call_limit','token_limit','usage_unknown','accounting_failed','incomplete_response',
    'admission_failure','tool_recovery_blocked','critical_hook_error','execution_failure')
CATEGORIES = ('model_output','evidence','provider','tool','budget','accounting','host_policy')
HOST = {'evidence': ('verified','missing','conflicting'), 'validation': ('passed','failed','incomplete'),
        'approval': ('pending','approved','denied','revoked','spent'),
        'recovery': ('inspected',), 'host_policy': ('allowed','denied')}
TOOL_CODES = ('ok','invalid_arguments','not_granted','authorization_denied','controlled_failure',
    'handler_error','invalid_result','result_limit','execution_failed','tool_identity_conflict',
    'tool_journal_failed','tool_effect_uncertain','unclassified')


def _closed(properties, required=None):
    return dict(type='object', properties=properties, required=list(properties) if required is None else required,
                additionalProperties=False)


COUNT = dict(type='integer', minimum=0, maximum=2**63-1)
REF = dict(type='string', pattern='^[0-9a-f]{64}$')
USAGE = _closed({k: dict(anyOf=[COUNT, {'type':'null'}])
                 for k in ('providerRequests','toolCalls','reportedTokens')})
ASSESSMENT = _closed(dict(bindingDigest=REF, status=dict(enum=['passed','failed','incomplete']),
    categories=dict(type='array', items=dict(enum=list(CATEGORIES)), maxItems=len(CATEGORIES), uniqueItems=True),
    evidenceDigest=REF, usage=USAGE))
OBSERVATION = _closed(dict(ordinal=COUNT, sequence=COUNT, source=dict(enum=list(EVENTS)),
    event=dict(enum=[e for values in EVENTS.values() for e in values]), streamRef=REF, stepRef=REF,
    outcome=dict(enum=[o for values in OUTCOMES.values() for o in values]),
    reason=dict(enum=list(REASONS)), toolCode=dict(enum=list(TOOL_CODES))),
    ['ordinal','sequence','source','event','streamRef'])
ANNOTATION = _closed(dict(ordinal=COUNT, stepRef=REF, kind=dict(enum=list(HOST)),
    status=dict(enum=[s for values in HOST.values() for s in values]), evidenceRef=REF))
PROJECTED_ASSESSMENT = deepcopy(ASSESSMENT)
PROJECTED_ASSESSMENT['properties']['evidenceRef'] = PROJECTED_ASSESSMENT['properties'].pop('evidenceDigest')
PROJECTED_ASSESSMENT['required'] = [k if k!='evidenceDigest' else 'evidenceRef'
                                  for k in PROJECTED_ASSESSMENT['required']]
REPORT = _closed(dict(version=dict(type='integer',const=1), bindingDigest=REF, runRef=REF,
    observations=dict(type='array',maxItems=512,items=OBSERVATION),
    hostAnnotations=dict(type='array',maxItems=128,items=ANNOTATION),
    monitoring=_closed(dict(rejectedRecords=COUNT,droppedRecords=COUNT,sequenceIssues=COUNT,
        openStreams=COUNT,streams=COUNT,noRecords=dict(type='boolean'))),
    assessment=PROJECTED_ASSESSMENT, sha256=REF))


def _valid(schema, value):
    try:
        if not Draft202012Validator(schema).is_valid(value):
            raise ValueError('invalid trajectory data')
    except (TypeError, RecursionError):
        raise ValueError('invalid trajectory data') from None


def _reference(value):
    if type(value) is not str or not 1 <= len(value.encode('utf-8')) <= 512:
        raise ValueError('invalid host reference')
    return value


def _assessment(value, binding, *, projected=False):
    _valid(PROJECTED_ASSESSMENT if projected else ASSESSMENT, value)
    if value['bindingDigest'] != binding:
        raise ValueError('trajectory binding mismatch')
    if value['status']=='passed' and (value['categories'] or any(v is None for v in value['usage'].values())):
        raise ValueError('passing assessment needs known usage and no verified failures')
    if value['status']!='passed' and not value['categories']:
        raise ValueError('failed or incomplete assessment needs diagnostics')


class Trajectory:
    """One trusted run; attach observe to public SDK observer callbacks.

    Hosts authenticate run scope and assessment inputs. HMAC references reduce
    accidental disclosure; they are not access controls or evidence signatures.
    """
    def __init__(self, run_id, *, binding_digest, key):
        self._run = _reference(run_id)
        self._binding = sha(binding_digest)
        if type(key) is not bytes or not 32 <= len(key) <= 64:
            raise ValueError('independent private pseudonym key required')
        self._key = key
        self._lock = RLock()
        self._observations = []
        self._annotations = []
        self._streams = {}
        self._rejected = self._dropped = self._sequence_issues = self._ordinal = 0

    def _ref(self, kind, value):
        return hmac.new(self._key, encode([self._binding,self._run,kind,value]), hashlib.sha256).hexdigest()

    def observe(self, record):
        """Drop malformed monitoring records without disrupting SDK execution."""
        with self._lock:
            try:
                self._observe(record)
            except (ValueError, TypeError, KeyError, UnicodeError, OverflowError):
                self._rejected += 1

    def _observe(self, record):
        if type(record) is not dict or type(record.get('version')) is not int or record['version']!=1:
            raise ValueError('invalid observer record')
        source = record['source']
        if source not in EVENTS or record['event'] not in EVENTS[source] or record.get('run_id')!=self._run:
            raise ValueError('foreign or unknown observation')
        invocation = _reference(record['invocation_id'])
        sequence = record['sequence']
        if type(sequence) is not int or not 1<=sequence<=2**63-1:
            raise ValueError('invalid observer sequence')
        stream = self._ref('stream',[source,invocation])
        value = dict(source=source,event=record['event'],sequence=sequence,streamRef=stream)
        if 'step_id' in record:
            value['stepRef'] = self._ref('step',_reference(record['step_id']))
        for name, allowed in (('outcome',OUTCOMES[source]),('reason',REASONS)):
            if name in record:
                if type(record[name]) is not str or record[name] not in allowed:
                    raise ValueError('invalid observer category')
                value[name] = record[name]
        if 'tool_outcome' in record:
            from prosaic_runtime import ToolOutcome
            value['toolCode'] = ToolOutcome.from_dict(record['tool_outcome']).code
        if len(self._observations)>=512:
            self._dropped += 1
            return
        previous, closed = self._streams.get(stream,(0,False))
        if sequence != previous+1:
            self._sequence_issues += 1
        if sequence<=previous or closed:
            raise ValueError('duplicate or closed stream')
        closed = record['event'] in ('invocation_completed','waiting_committed','blocked_committed','run_completed')
        self._streams[stream] = (sequence,closed)
        self._ordinal += 1
        self._observations.append(dict(ordinal=self._ordinal,**value))

    def annotate(self, step_id, *, kind, status, evidence_digest):
        """Host-only observation of an independently performed check/decision."""
        step = self._ref('step',_reference(step_id))
        evidence = self._ref('evidence',sha(evidence_digest))
        if type(kind) is not str or kind not in HOST or type(status) is not str or status not in HOST[kind]:
            raise ValueError('invalid host annotation')
        with self._lock:
            if len(self._annotations)>=128:
                self._dropped += 1
                return
            self._ordinal += 1
            self._annotations.append(dict(ordinal=self._ordinal,stepRef=step,kind=kind,status=status,evidenceRef=evidence))

    def report(self, assessment):
        """Outcome/usage come only from trusted consumer checks, never telemetry."""
        _assessment(assessment,self._binding)
        assessed = deepcopy(assessment)
        assessed['evidenceRef'] = self._ref('evidence',assessed.pop('evidenceDigest'))
        with self._lock:
            value = dict(version=1,bindingDigest=self._binding,runRef=self._ref('run',self._run),
                observations=deepcopy(self._observations),hostAnnotations=deepcopy(self._annotations),
                assessment=assessed, monitoring=dict(rejectedRecords=self._rejected,droppedRecords=self._dropped,
                    sequenceIssues=self._sequence_issues,streams=len(self._streams),
                    openStreams=sum(not closed for _,closed in self._streams.values()),
                    noRecords=not self._observations))
        return value | dict(sha256=digest(value))


def _validate_report(value, binding):
    encode(value,maximum=1_048_576)
    _valid(REPORT,value)
    _assessment(value['assessment'],sha(binding),projected=True)
    if value['bindingDigest']!=binding or digest({k:v for k,v in value.items() if k!='sha256'})!=value['sha256']:
        raise ValueError('trajectory integrity or binding mismatch')
    ordinals = [v['ordinal'] for v in value['observations']+value['hostAnnotations']]
    if sorted(ordinals)!=list(range(1,len(ordinals)+1)):
        raise ValueError('invalid observation order')
    for item in value['observations']:
        if item['event'] not in EVENTS[item['source']] or item['sequence']<1:
            raise ValueError('invalid observation category')
        if 'outcome' in item and item['outcome'] not in OUTCOMES[item['source']]:
            raise ValueError('invalid observation outcome')
    for item in value['hostAnnotations']:
        if item['status'] not in HOST[item['kind']]:
            raise ValueError('invalid host status')
    monitoring = value['monitoring']
    if (monitoring['noRecords'] != (not value['observations']) or
        monitoring['streams'] != len({o['streamRef'] for o in value['observations']}) or
        monitoring['openStreams']>monitoring['streams']):
        raise ValueError('invalid monitoring summary')


def save_report(path, report):
    _validate_report(report,report.get('bindingDigest'))
    private_write(Path(path),report)


def read_report(path, *, binding_digest):
    path=Path(path)
    if not path.is_absolute() or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('private absolute report path required')
    parent=path.parent.stat()
    if parent.st_uid!=os.getuid() or parent.st_mode & 0o077:
        raise ValueError('private report directory required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as source:
        info=os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode & 0o077:
            raise ValueError('private regular report required')
        value=decode(source.read(1_048_577),maximum=1_048_576)
    _validate_report(value,binding_digest)
    return value
