"""Bounded evidence classification, independent of model, provider and decision rules."""
from lab_runner.quality.contracts import decode, encode, identifier
from lab_runner.quality.checks import parse_task
from .context import current_index, current_sources

TYPED_GUIDANCE = '''
lookup_records returns a versioned evidence summary plus the raw fetched records.
The host checks only the complete current index's authority and revision metadata.
For each fact: verified means its current authoritative value was fetched;
absent means the complete current index has no record for the task's authority;
unread means a current authoritative record exists but its value was not fetched.
An unread value is unknown, never absent. excludedRecords explains fetched rows
that have the wrong authority or are superseded; they remain in records for audit.
Use verified values to apply the task's rules yourself. The summary supplies no
decision. Cite verified recordIds and return factId labels in facts.
'''


def validate_format(value):
    if value not in ('raw', 'typed'):
        raise ValueError('invalid evidence format')
    return value


def admit_complete_index(index, snapshot):
    """Require the public index to cover exactly this granted source snapshot."""
    public = current_index(index)
    expected = [{k: row[k] for k in ('recordId', 'factId', 'authority', 'revision')}
                for row in snapshot.values()]
    if sorted(public, key=lambda r: r['recordId']) != sorted(expected, key=lambda r: r['recordId']):
        raise ValueError('incomplete or mismatched current source index')


def build_summary(*, authority, required_facts, record_index, records, index_complete):
    """Classify only a trusted complete index's scope, never global knowledge.

    The caller owns policy and index completeness. Indexed-but-unfetched values
    remain unknown. Neither numeric conditions nor private expected answers enter
    this interface. Raw fetched records remain visible, including excluded ones.
    """
    if index_complete is not True:
        raise ValueError('complete trusted index required')
    identifier(authority)
    if type(required_facts) is not list or not 1 <= len(required_facts) <= 16:
        raise ValueError('bounded required fact policy needed')
    for fact in required_facts:
        identifier(fact)
    if len(set(required_facts)) != len(required_facts):
        raise ValueError('duplicate required fact')
    if type(record_index) is not list:
        raise ValueError('invalid public index')
    index = current_index(record_index) if record_index else []
    indexed = {row['recordId']: row for row in index}
    if type(records) is not list or len(records) > 16 or any(type(row) is not dict or 'recordId' not in row for row in records):
        raise ValueError('invalid fetched records')
    ids = [row['recordId'] for row in records]
    for key in ids:
        identifier(key)
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate fetched record')
    fetched = current_sources(dict(zip(ids, records))) if records else {}
    for key, row in fetched.items():
        expected = indexed.get(key)
        if expected is None or any(row[k] != expected[k] for k in ('factId', 'authority', 'revision')):
            raise ValueError('fetched identity differs from public index')
    groups = {}
    for row in index:
        if row['authority'] == authority:
            groups.setdefault(row['factId'], []).append(row)
    latest = {}
    for fact, rows in groups.items():
        revision = max(row['revision'] for row in rows)
        choices = [row for row in rows if row['revision'] == revision]
        if len(choices) != 1:
            raise ValueError('ambiguous latest authority revision')
        latest[fact] = choices[0]
    facts = []
    for fact in sorted(set(required_facts) | set(latest)):
        row = latest.get(fact)
        if row is None:
            facts.append(dict(factId=fact, status='absent', recordId=None, revision=None, value=None))
        else:
            source = fetched.get(row['recordId'])
            facts.append(dict(factId=fact, status='unread' if source is None else 'verified',
                              recordId=row['recordId'], revision=row['revision'],
                              value=None if source is None else source['value']))
    excluded = []
    for row in fetched.values():
        reason = 'wrongAuthority' if row['authority'] != authority else (
            'superseded' if latest[row['factId']]['recordId'] != row['recordId'] else None)
        if reason is not None:
            excluded.append(dict(recordId=row['recordId'], reason=reason))
    result = dict(version=1, indexComplete=True, authority=authority,
                  requiredFacts=sorted(required_facts), facts=facts,
                  excludedRecords=sorted(excluded, key=lambda row: row['recordId']), records=records)
    return decode(encode(result, 8192), 8192)


def summarize_lookup(request, records):
    """Rollout adapter; execution must admit the trusted complete index first."""
    authority, required, _ = parse_task(request['task'])
    return build_summary(authority=authority, required_facts=required,
                         record_index=request['recordIndex'], records=records, index_complete=True)
