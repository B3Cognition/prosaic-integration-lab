"""Consumer-owned policy helpers. No inference, allowance, tools or authorization.

All expected checks, observation provenance and pinned digests must come from a
trusted host. Reports are evidence records, not signed capability grants.
"""
from dataclasses import dataclass
from copy import deepcopy
from jsonschema import Draft202012Validator
from lab_runner.quality.contracts import encode, decode, digest, identifier, sha

LIMITS = dict(providerRequests=4, toolCalls=2, reportedTokens=8192,
              timeoutSeconds=600, outputTokens=512)


def _schema(schema):
    encode(schema, maximum=65536)
    def inline(value):
        if isinstance(value, dict):
            if any(k in value for k in ('$ref', '$dynamicRef')):
                raise ValueError('inline schemas required')
            for child in value.values(): inline(child)
        elif isinstance(value, list):
            for child in value: inline(child)
    inline(schema)
    Draft202012Validator.check_schema(schema)
    if not isinstance(schema, dict) or schema.get('type') != 'object' or schema.get('additionalProperties') is not False:
        raise ValueError('closed object schema required')
    return Draft202012Validator(schema)


@dataclass(frozen=True)
class FieldCheck:
    path: str
    expected: object
    evidence_refs: tuple[str, ...] = ()
    comparison: str = 'equal'

    def __post_init__(self):
        if (type(self.path) is not str or len(self.path)>256 or self.path and not self.path.startswith('/')
                or self.comparison not in ('equal','set')):
            raise ValueError('invalid field check')
        import re
        if re.search(r'~(?![01])', self.path): raise ValueError('invalid JSON pointer')
        if len(self.evidence_refs)>32 or any(type(r) is not str or not 1<=len(r)<=128 for r in self.evidence_refs):
            raise ValueError('invalid evidence references')
        encode(self.expected, maximum=65536)
        if self.comparison=='set': _items(self.expected)


def _items(value):
    if type(value) is not list: raise ValueError('unordered checks require arrays')
    items=[encode(item) for item in value]
    if len(set(items))!=len(items): raise ValueError('unordered checks require unique arrays')
    return set(items)


def _get(value, path):
    for token in path.split('/')[1:] if path else ():
        key=token.replace('~1','/').replace('~0','~')
        if isinstance(value, dict): value=value[key]
        elif isinstance(value, list) and key.isdecimal() and str(int(key))==key:value=value[int(key)]
        else: raise KeyError(key)
    return value


def assess_output(text, schema, *, checks=(), exit_code=0, usage_known=True,
                  budget_violation=False, abstained=False):
    """Compare host expectations; never return raw values or validation messages."""
    validator=_schema(schema);checks=list(checks)
    if len(checks)>64 or any(not isinstance(c,FieldCheck) for c in checks):raise ValueError('invalid checks')
    if type(exit_code) is not int or any(type(v) is not bool for v in (usage_known,budget_violation,abstained)):
        raise ValueError('invalid host observation')
    diagnostics=[]
    def add(code,field='',refs=()):
        item=dict(code=code,field=field,evidenceRefs=list(refs))
        if item not in diagnostics:diagnostics.append(item)
    if exit_code!=0:add('unusable_output')
    if not usage_known:add('unknown_usage')
    if budget_violation:add('budget_violation')
    if abstained:add('abstained')
    try:value=decode(text, maximum=65536)
    except (ValueError,TypeError):add('invalid_json');value=None
    if not any(d['code']=='invalid_json' for d in diagnostics):
        errors=list(validator.iter_errors(value))
        for error in errors:
            path=''.join('/'+str(k).replace('~','~0').replace('/','~1') for k in error.absolute_path)
            add('schema_mismatch',path)
        if not errors:
            for check in checks:
                try:
                    actual=_get(value,check.path)
                    same=(_items(actual)==_items(check.expected) if check.comparison=='set'
                          else encode(actual)==encode(check.expected))
                except (KeyError,IndexError,ValueError):same=False
                if not same:add('field_mismatch',check.path,check.evidence_refs)
    return dict(version=1,status='abstained' if abstained else 'failed' if diagnostics else 'passed',
                schemaDigest=digest(schema),diagnostics=diagnostics)


def qualification_binding(*, role, schema, profile_fingerprint, adapter_revision,
                          evaluator_revision, evidence_revision, suite_revision, limits=None):
    _schema(schema);identifier(role);sha(profile_fingerprint)
    revisions=dict(adapter=adapter_revision,evaluator=evaluator_revision,
                   evidence=evidence_revision,suite=suite_revision)
    if any(type(v) is not str or not 1<=len(v)<=128 for v in revisions.values()):raise ValueError('invalid revision')
    limits=deepcopy(LIMITS if limits is None else limits)
    if (set(limits)!=set(LIMITS) or any(type(v) is not int or not 1<=v<=LIMITS[k] for k,v in limits.items())):
        raise ValueError('qualification exceeds current limits')
    return dict(version=1,role=role,contractDigest=digest(schema),profileFingerprint=profile_fingerprint,
                revisions=revisions,limits=limits)


def _scenarios(values):
    if type(values) is not list or not 1<=len(values)<=64:raise ValueError('required scenarios missing')
    for value in values:identifier(value)
    if len(set(values))!=len(values):raise ValueError('duplicate scenarios')
    return sorted(values)


def qualification_report(binding, observations, *, required_scenarios, origin):
    """Aggregate trusted host observations. Synthetic success is never live eligible."""
    required=_scenarios(required_scenarios)
    if origin not in ('synthetic','live'):raise ValueError('invalid observation origin')
    # Bounded JSON snapshot: no object aliases, executable callbacks or private state.
    binding=decode(encode(binding));observations=decode(encode(observations))
    if type(observations) is not list or len(observations)>256:raise ValueError('invalid observations')
    ids=set();seen=set();passed=bool(observations)
    for row in observations:
        if set(row)!= {'caseId','scenario','bindingDigest','evidenceDigest','assessment'}:raise ValueError('invalid observation')
        identifier(row['caseId']);identifier(row['scenario']);sha(row['evidenceDigest'])
        if row['caseId'] in ids:raise ValueError('duplicate case identity')
        ids.add(row['caseId']);seen.add(row['scenario'])
        a=row['assessment']
        if (row['bindingDigest']!=digest(binding) or a.get('schemaDigest')!=binding['contractDigest']):
            raise ValueError('observation binding mismatch')
        passed=passed and a.get('version')==1 and a.get('status')=='passed' and a.get('diagnostics')==[]
    qualified=bool(passed and set(required)<=seen)
    return dict(version=1,binding=binding,origin=origin,requiredScenarios=required,
                observations=observations,qualified=qualified,liveEligible=qualified and origin=='live')


def require_qualification(report, *, expected_binding, trusted_digest, required_scenarios):
    """Optional consumer gate; requires a host-pinned report and separate call consent."""
    sha(trusted_digest)
    if digest(report)!=trusted_digest or report.get('binding')!=expected_binding:
        raise ValueError('qualification integrity or binding changed')
    rebuilt=qualification_report(expected_binding,report['observations'],
        required_scenarios=required_scenarios,origin=report['origin'])
    if rebuilt!=report or not rebuilt['liveEligible']:raise ValueError('complete live qualification required')
