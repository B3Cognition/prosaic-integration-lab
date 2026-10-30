"""Audit boundary tests: address-valid source text is never answer text."""
import copy
import hashlib
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / 'memory_benchmark_candidate'))
from test_completeness_profile import fixture
from lab_runner.memory_benchmark.completeness_profile import freeze_packet

try:
    audit = importlib.import_module('lab_runner.memory_benchmark.span_audit_contracts')
except ModuleNotFoundError:
    audit = None


def test_answer_span_audit_contract_is_available():
    assert audit is not None, 'answer-span audit is not implemented'


def ref(kind, identifier, text, start=0, end=None):
    end = len(text) if end is None else end
    return dict(kind=kind, id=identifier, sha256=hashlib.sha256(text.encode()).hexdigest(),
                start=start, end=end, quote=text[start:end])


@pytest.fixture
def sample():
    assert audit is not None, 'answer-span audit is not implemented'
    q, draft, frames, identity = fixture()
    packet = audit.freeze_audit(freeze_packet(q, draft, frames, identity=identity))
    source = frames['visible-001.json']['display']
    sr = ref('source', 'visible-001.json', source, source.index('Ž'))
    ar = ref('answer', 'c', draft['claims'][0]['text'])
    qr = ref('question', 'question', q)
    ledger = dict(version=1, questionParts=[dict(id='p1', questionSpans=[qr],
        answerability='answerable', reason='The supplied body states the boundary.')],
        obligations=[dict(id='o1', partIds=['p1'], proposition='The default must remain disabled.', sourceSpans=[sr])], unresolved=[])
    result = dict(version=1,
        obligations=[dict(id='o1', verdict='omitted', answerSpans=[], sourceSpans=[sr], reason='No actual answer wording states the disabled boundary.')],
        claims=[dict(id='c', verdict='supported', answerSpans=[ar], sourceSpans=[sr],
            citations=[dict(evidenceId='e', verdict='supported', sourceSpans=[sr], reason='Displayed support.')], reason='The draft states only that the fixture works.')],
        questionParts=[dict(id='p1', verdict='insufficient', answerSpans=[ar], limitationSpans=[], sourceSpans=[sr], reason='A material boundary is omitted.')],
        extraFindings=[], status=dict(recommendation='partial', partIds=['p1'], answerSpans=[ar], limitationSpans=[], reason='The requested boundary is omitted.'), unresolved=[])
    return packet, ledger, result


def test_frozen_views_own_inputs_and_hide_draft_from_source_view(sample):
    packet, ledger, result = sample
    data = packet.to_dict()
    assert 'draft' not in audit.source_view(packet)
    assert 'claims' not in audit.source_view(packet)
    assert 'The fixture works.' not in str(audit.source_view(packet))
    assert audit.answer_view(packet)['claims'][0]['text'] == 'The fixture works.'
    data['draft']['claims'][0]['text'] = 'changed'
    assert packet.to_dict()['draft']['claims'][0]['text'] == 'The fixture works.'
    assert '\r\n' in audit.source_view(packet)['frames']['visible-001.json']['display']
    assert audit.validate_ledger(ledger, packet) == ledger
    assert audit.validate_audit(result, packet, ledger)['outcome'] == 'findings'


@pytest.mark.parametrize('mutation', ['source-as-answer', 'no-answer', 'bad-quote', 'boolean-offset', 'foreign-id', 'header', 'missing-claim', 'missing-obligation', 'extra-field', 'wrong-citation'])
def test_false_coverage_and_invalid_proof_fail_closed(sample, mutation):
    packet, ledger, value = sample
    value = copy.deepcopy(value)
    row = value['obligations'][0]
    if mutation == 'source-as-answer': row.update(verdict='covered', answerSpans=row['sourceSpans'])
    if mutation == 'no-answer': row.update(verdict='covered', answerSpans=[])
    if mutation == 'bad-quote': value['claims'][0]['answerSpans'][0]['quote'] = 'Invented text'
    if mutation == 'boolean-offset': value['claims'][0]['answerSpans'][0]['start'] = False
    if mutation == 'foreign-id': value['claims'][0]['answerSpans'][0]['id'] = 'foreign'
    if mutation == 'header':
        text = packet.to_dict()['frames']['visible-001.json']['display']
        row['sourceSpans'] = [ref('source', 'visible-001.json', text, 0, 6)]
    if mutation == 'missing-claim': value['claims'] = []
    if mutation == 'missing-obligation': value['obligations'] = []
    if mutation == 'extra-field': value['approved'] = True
    if mutation == 'wrong-citation': value['claims'][0]['citations'][0]['evidenceId'] = 'other'
    with pytest.raises(ValueError): audit.validate_audit(value, packet, ledger)


def test_clean_answer_and_paraphrase_require_real_answer_spans(sample):
    _, ledger, value = sample
    q, draft, frames, identity = fixture()
    draft['claims'][0]['text'] = 'The fixture works and memory stays switched off by default.'
    packet = audit.freeze_audit(freeze_packet(q, draft, frames, identity=identity))
    ar = ref('answer', 'c', draft['claims'][0]['text'])
    value['obligations'][0].update(verdict='covered', answerSpans=[ar])
    value['claims'][0]['answerSpans'] = [ar]
    value['questionParts'][0].update(verdict='fact-supported', answerSpans=[ar])
    value['status'].update(recommendation='answered', answerSpans=[ar])
    assert audit.validate_audit(value, packet, ledger)['outcome'] == 'clear'
    value['claims'][0]['citations'][0]['verdict'] = 'supported-elsewhere'
    assert audit.validate_audit(value, packet, ledger)['outcome'] == 'findings'


def test_correct_abstention_can_clear_without_proving_global_absence(sample):
    _, ledger, value = sample
    q, draft, frames, identity = fixture()
    draft['claims'] = []
    draft['evidence'] = []
    draft['citations'] = []
    draft['status'] = 'abstained'
    draft['missingEvidence'] = ['The requested fact is not established in the supplied context.']
    draft['questionParts'][0].update(claimIds=[], missingEvidenceIndices=[0])
    draft['sections']['directAnswer'].update(claimIds=[], reason='Insufficient supplied evidence.')
    draft['frameReview'][0].update(claimIds=[], disposition='insufficient')
    packet = audit.freeze_audit(freeze_packet(q, draft, frames, identity=identity))
    ledger['obligations'] = []
    ledger['questionParts'][0]['answerability'] = 'unknown-in-context'
    limitation = ref('limitation', 'missing-0', draft['missingEvidence'][0])
    value.update(obligations=[], claims=[])
    value['questionParts'][0].update(verdict='appropriately-limited', answerSpans=[], limitationSpans=[limitation], sourceSpans=[])
    value['status'].update(recommendation='abstained', answerSpans=[], limitationSpans=[limitation])
    assert audit.validate_audit(value, packet, ledger)['outcome'] == 'clear'
    value['questionParts'][0]['limitationSpans'] = []
    with pytest.raises(ValueError): audit.validate_audit(value, packet, ledger)


def test_scope_tampering_oversized_ledger_duplicate_keys_and_surrogates_rejected(sample):
    packet, ledger, value = sample
    q, draft, frames, identity = fixture(castle=True)
    frames['visible-001.json']['metadata']['records']['synthetic-record']['sourceIdentity']['namespace'] = 'foreign'
    with pytest.raises(ValueError): audit.freeze_audit(freeze_packet(q, draft, frames, identity=identity))
    huge = copy.deepcopy(ledger)
    huge['obligations'] = [dict(ledger['obligations'][0], id=f'o{i}') for i in range(33)]
    with pytest.raises(ValueError): audit.validate_ledger(huge, packet)
    for raw in ['{"version":1,"version":1}', '{"version":NaN}', '{"bad":"\\ud800"}']:
        with pytest.raises(ValueError): audit.validate_ledger(raw, packet)


def test_unresolved_audit_never_becomes_clear(sample):
    packet, ledger, value = sample
    value['unresolved'] = ['Cannot establish complete coverage.']
    assert audit.validate_audit(value, packet, ledger)['outcome'] == 'unresolved'


def test_host_indexes_supply_exact_question_source_and_answer_addresses(sample):
    packet, _, _ = sample
    source = audit.source_view(packet)
    assert source['questionSpan']['quote'] == 'What is recorded, and what boundary applies?'
    assert source['quoteCandidates']
    for span in source['quoteCandidates']:
        text = source['frames'][span['id']]['display']
        assert span['quote'] == text[span['start']:span['end']]
        assert span['sha256'] == hashlib.sha256(text.encode()).hexdigest()
    claim = audit.answer_view(packet)['claims'][0]
    assert claim['span']['kind'] == 'answer'
    assert claim['span']['start'] == 0 and claim['span']['end'] == 18
    assert claim['span']['quote'] == 'The fixture works.'


def test_limitation_proof_cannot_be_borrowed_from_another_question_part(sample):
    _, ledger, value = sample
    _, draft, frames, identity = fixture()
    question = 'First? Second?'
    draft.update(claims=[], evidence=[], citations=[], status='abstained', missingEvidence=['First is unknown.', 'Second is unknown.'])
    draft['questionParts'] = [dict(id=f'd{i}', start=start, end=end, quote=question[start:end], claimIds=[], missingEvidenceIndices=[i])
        for i, (start, end) in enumerate([(0,6),(7,14)])]
    draft['sections']['directAnswer'].update(claimIds=[], reason='Insufficient context.')
    draft['frameReview'][0].update(claimIds=[], disposition='insufficient')
    packet = audit.freeze_audit(freeze_packet(question, draft, frames, identity=identity))
    ledger['obligations'] = []
    ledger['questionParts'] = [dict(id=f'p{i}', questionSpans=[ref('question','question',question,start,end)],
        answerability='unknown-in-context',reason='Not established in context.') for i,(start,end) in enumerate([(0,6),(7,14)])]
    limits = [ref('limitation',f'missing-{i}',text) for i,text in enumerate(draft['missingEvidence'])]
    value.update(claims=[], obligations=[])
    value['questionParts'] = [dict(id=f'p{i}',verdict='appropriately-limited',answerSpans=[],limitationSpans=[limits[i]],sourceSpans=[],reason='Explicitly limited.') for i in range(2)]
    value['status'].update(partIds=['p0','p1'],recommendation='abstained',answerSpans=[],limitationSpans=limits)
    assert audit.validate_audit(value,packet,ledger)['outcome']=='clear'
    value['questionParts'][0]['limitationSpans']=[limits[1]]
    with pytest.raises(ValueError): audit.validate_audit(value,packet,ledger)


def test_changed_workflow_helper_invalidates_frozen_packet(sample,tmp_path,monkeypatch):
    packet,_,_=sample
    original=Path(audit.__file__).parent
    for name in ['span_audit_contracts.py','span_audit_workflow.py','completeness_profile.py','answer_contract.py']:
        (tmp_path/name).write_bytes((original/name).read_bytes())
    monkeypatch.setattr(audit,'__file__',str(tmp_path/'span_audit_contracts.py'))
    assert audit.checked(packet)['draft']==packet.to_dict()['draft']
    with (tmp_path/'span_audit_workflow.py').open('a') as out: out.write('\n# changed host workflow helper\n')
    with pytest.raises(ValueError): audit.checked(packet)


def test_limitation_only_claim_cannot_cover_a_factual_obligation():
    from lab_runner.memory_benchmark.span_audit_fixture import materials
    packet, ledger, value = materials('complete')
    data = packet.to_dict()
    draft = data['draft']
    text = 'The supplied context does not establish the requested memory default.'
    draft['claims'][0].update(text=text, kind='absence', evidenceIds=[])
    draft.update(evidence=[], citations=[], missingEvidence=[text], status='partial')
    draft['sections']['directAnswer']['claimIds'] = []
    draft['sections']['limitations']['claimIds'] = ['claim']
    draft['questionParts'][0]['missingEvidenceIndices'] = [0]
    draft['frameReview'][0].update(disposition='insufficient', claimIds=[])
    packet = audit.freeze_audit(freeze_packet(data['question'], draft, data['frames'], identity=data['identity']))
    ar = ref('answer', 'claim', text)
    ledger['questionParts'][0]['answerability'] = 'partially-answerable'
    value['obligations'][0]['answerSpans'] = [ar]
    value['claims'][0].update(verdict='appropriate-limitation', answerSpans=[ar], sourceSpans=[], citations=[])
    value['questionParts'][0].update(verdict='appropriately-limited', answerSpans=[ar],
        limitationSpans=[ref('limitation', 'missing-0', text)])
    value['status'].update(recommendation='partial', answerSpans=[ar], limitationSpans=[])
    with pytest.raises(ValueError, match='factual coverage'):
        audit.validate_audit(value, packet, ledger)


@pytest.mark.parametrize('verdict', ['supported', 'appropriate-limitation'])
def test_positive_claim_verdict_cannot_leave_an_unaudited_suffix(verdict):
    from lab_runner.memory_benchmark.span_audit_fixture import materials
    packet, ledger, value = materials('complete' if verdict == 'supported' else 'unavailable')
    data = packet.to_dict()
    draft = data['draft']
    prefix = 'Memory is disabled by default.' if verdict == 'supported' else draft['missingEvidence'][0]
    text = prefix + ' All users must enable memory.'
    if verdict == 'supported':
        draft['claims'][0]['text'] = text
        for row in [*value['obligations'], *value['claims'], *value['questionParts'], value['status']]:
            row['answerSpans'] = [ref('answer', 'claim', text, 0, len(prefix))]
    else:
        draft['claims'] = [dict(id='claim', text=text, kind='absence', evidenceIds=[])]
        draft['sections']['limitations']['claimIds'] = ['claim']
        draft['questionParts'][0]['claimIds'] = ['claim']
        value['claims'] = [dict(id='claim', verdict=verdict,
            answerSpans=[ref('answer', 'claim', text, 0, len(prefix))], sourceSpans=[], citations=[], reason='Only the prefix was inspected.')]
    packet = audit.freeze_audit(freeze_packet(data['question'], draft, data['frames'], identity=data['identity']))
    with pytest.raises(ValueError, match='complete claim'):
        audit.validate_audit(value, packet, ledger)


@pytest.mark.parametrize('status', ['abstained', 'partial'])
def test_fully_answered_audit_cannot_recommend_an_incompatible_status(status):
    from lab_runner.memory_benchmark.span_audit_fixture import materials
    packet, ledger, value = materials('complete')
    data = packet.to_dict()
    data['draft']['status'] = status
    packet = audit.freeze_audit(freeze_packet(data['question'], data['draft'], data['frames'], identity=data['identity']))
    value['status']['recommendation'] = status
    with pytest.raises(ValueError, match='status.*judgments'):
        audit.validate_audit(value, packet, ledger)


def test_same_version_changed_sdk_payload_invalidates_packet(sample, tmp_path, monkeypatch):
    from types import SimpleNamespace
    packet, _, _ = sample
    sdk = tmp_path / 'sdk.py'
    sdk.write_text('# original SDK payload\n')
    installed = SimpleNamespace(files=[Path('sdk.py')], locate_file=lambda name: tmp_path / name)
    monkeypatch.setattr(audit, 'distribution', lambda name: installed, raising=False)
    data = packet.to_dict()
    packet = audit.freeze_audit(freeze_packet(data['question'], data['draft'], data['frames'], identity=data['identity']))
    assert audit.checked(packet)
    sdk.write_text('# different SDK payload, same distribution version\n')
    with pytest.raises(ValueError, match='frozen audit input or version mismatch'):
        audit.checked(packet)


def test_positive_claim_can_use_multiple_exact_spans_without_keyword_matching():
    from lab_runner.memory_benchmark.span_audit_fixture import materials
    packet, ledger, value = materials('complete')
    text = packet.to_dict()['draft']['claims'][0]['text']
    value['claims'][0]['answerSpans'] = [ref('answer', 'claim', text, 0, 9), ref('answer', 'claim', text, 10)]
    assert text[9].isspace()
    assert audit.validate_audit(value, packet, ledger)['outcome'] == 'clear'


def test_incomplete_claim_disposition_can_identify_only_the_offending_clause():
    from lab_runner.memory_benchmark.span_audit_fixture import materials
    packet, ledger, value = materials('complete')
    value['claims'][0].update(verdict='unsupported', answerSpans=[ref('answer', 'claim',
        packet.to_dict()['draft']['claims'][0]['text'], 0, 6)])
    assert audit.validate_audit(value, packet, ledger)['outcome'] == 'findings'


def test_conflicting_sources_can_clear_only_with_source_answer_and_limitation_proof():
    from lab_runner.memory_benchmark.span_audit_fixture import materials
    packet, ledger, value = materials('complete')
    data = packet.to_dict()
    draft, frame = data['draft'], data['frames']['body']
    frame['display'] += '\n\nMemory is enabled by default.'
    frame['bodySpans'][0]['end'] = len(frame['display'])
    frame['metadata']['endChar'] += len('\n\nMemory is enabled by default.')
    digest = audit.sha(frame['display'][frame['bodySpans'][0]['start']:])
    frame['metadata']['sourceFileSha256'] = frame['metadata']['sourceIdentity']['sourceFileSha256'] = digest
    draft['citations'][0].update(sourceFileSha256=digest, chars=[0, frame['metadata']['endChar']])
    draft['evidence'][0]['displaySha256'] = audit.sha(frame['display'])
    second = ref('source', 'body', frame['display'], frame['display'].index('Memory is enabled'))
    draft['evidence'].append(dict(id='e2', frameId='body', displaySha256=second['sha256'],
        start=second['start'], end=second['end'], quote=second['quote']))
    draft['claims'][0].update(text='The supplied notes disagree: memory is disabled or enabled by default.', evidenceIds=['evidence', 'e2'])
    draft.update(status='partial', missingEvidence=['The supplied notes do not establish which default applies.'])
    draft['questionParts'][0]['missingEvidenceIndices'] = [0]
    packet = audit.freeze_audit(freeze_packet(data['question'], draft, data['frames'], identity=data['identity']))
    first = ref('source', 'body', frame['display'], draft['evidence'][0]['start'], draft['evidence'][0]['end'])
    ar = ref('answer', 'claim', draft['claims'][0]['text'])
    lr = ref('limitation', 'missing-0', draft['missingEvidence'][0])
    ledger['questionParts'][0]['answerability'] = 'conflicting'
    ledger['obligations'][0]['sourceSpans'] = [first]
    ledger['obligations'].append(dict(id='o2', partIds=['p'], proposition='Another note says memory is enabled.', sourceSpans=[second]))
    value['obligations'][0].update(answerSpans=[ar], sourceSpans=[first])
    value['obligations'].append(dict(id='o2', verdict='covered', answerSpans=[ar], sourceSpans=[second], reason='The answer reports the opposing position.'))
    value['claims'][0].update(answerSpans=[ar], sourceSpans=[first, second], citations=[
        dict(evidenceId=eid, verdict='supported', sourceSpans=[span], reason='Attached opposing position.')
        for eid, span in [('evidence', first), ('e2', second)]])
    value['questionParts'][0].update(verdict='appropriately-limited', answerSpans=[ar], limitationSpans=[lr], sourceSpans=[first, second])
    value['status'].update(recommendation='partial', answerSpans=[ar], limitationSpans=[lr])
    assert audit.validate_audit(value, packet, ledger)['outcome'] == 'clear'
    value['questionParts'][0]['sourceSpans'] = [first]
    with pytest.raises(ValueError, match='conflict requires opposing'):
        audit.validate_audit(value, packet, ledger)


@pytest.mark.parametrize('text', ['Memory is enabled by default.',
    'Memory is disabled by default, except all users must enable it.',
    'The worker digest belongs to the adapter artifact.'])
def test_adverse_semantic_judgments_remain_findings_with_exact_proof(text):
    from lab_runner.memory_benchmark.span_audit_fixture import materials
    packet, ledger, value = materials('complete')
    data = packet.to_dict()
    data['draft']['claims'][0]['text'] = text
    packet = audit.freeze_audit(freeze_packet(data['question'], data['draft'], data['frames'], identity=data['identity']))
    ar = ref('answer', 'claim', text)
    value['obligations'][0].update(verdict='contradicted', answerSpans=[ar])
    value['claims'][0].update(verdict='contradicted', answerSpans=[ar])
    value['questionParts'][0].update(verdict='insufficient', answerSpans=[ar])
    value['status'].update(recommendation='abstained', answerSpans=[ar])
    assert audit.validate_audit(value, packet, ledger)['outcome'] == 'findings'
