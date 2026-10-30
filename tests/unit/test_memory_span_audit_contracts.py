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
