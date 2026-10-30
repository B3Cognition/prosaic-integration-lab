import json

import pytest

from lab_runner.memory_benchmark.dataset import freeze, load_frozen
from lab_runner.memory_benchmark.retrieval import prepare, fixture_provider, catalog_for, validate_capture


BALANCED = 'terms-round-robin-v2'


def source_case(tmp_path, text, queries):
    source = tmp_path / 'input'
    source.mkdir()
    (source / 'note.md').write_bytes(text.encode('utf-8'))
    dataset = dict(version=1, sources=[dict(id='note', path='note.md', wing='notes')],
        cases=[dict(id='q1', question='What is recorded?', queries=queries, sourceIds=['note'])])
    policy = dict(version=1, namespace='balanced-owner', root=str(source), allowedWings=['notes'])
    for name, value in [('dataset', dataset), ('policy', policy)]:
        (tmp_path / (name + '.json')).write_text(json.dumps(value))
    frozen = tmp_path / 'frozen'
    freeze(tmp_path / 'dataset.json', tmp_path / 'policy.json', frozen)
    bundle = load_frozen(frozen)
    return frozen, bundle


def bodies(capture, kind):
    return [frame['display'][span['start']:span['end']]
        for frame in capture['frames'].values() if frame['kind'] == kind
        for span in frame['bodySpans']]


def test_new_policy_matches_individual_words_and_ranks_term_coverage(tmp_path):
    root, data = source_case(tmp_path,
        'alpha-only line\nbeta is recorded here.\nalphabet must not match.\nALPHA and beta occur together.\n',
        ['alpha beta'])
    legacy = prepare(root, data, data['cases'][0], 'manual')
    assert bodies(legacy, 'search') == []
    data['retrievalPolicy'] = BALANCED
    result = prepare(root, data, data['cases'][0], 'manual')
    assert bodies(result, 'search') == [
        'ALPHA and beta occur together.', 'alpha-only line', 'beta is recorded here.']
    assert len(result['selectedIds']) == 3
    validate_capture(root, data, data['cases'][0], result)


def test_keyword_matching_handles_unicode_without_substring_matches(tmp_path):
    root, data = source_case(tmp_path,
        'ŽLUŤOUČKÝ has MEMORY.\nA memoryless alphabet.\n', ['Žluťoučký, memory'])
    data['retrievalPolicy'] = BALANCED
    result = prepare(root, data, data['cases'][0], 'manual')
    assert bodies(result, 'search') == ['ŽLUŤOUČKÝ has MEMORY.']


def test_top_five_keyword_anchors_leave_budget_for_later_queries_and_opens(tmp_path):
    text = ''.join(f'alpha row {i}\n' for i in range(120)) + 'alpha and beta together\n'
    root, data = source_case(tmp_path, text, ['alpha beta', 'together'])
    data['retrievalPolicy'] = BALANCED
    result = prepare(root, data, data['cases'][0], 'manual')
    search_frames = [f for f in result['frames'].values() if f['kind'] == 'search']
    assert len(search_frames[0]['bodySpans']) == 5
    assert bodies(dict(frames={'search': search_frames[0]}), 'search')[0] == 'alpha and beta together'
    assert len(search_frames[1]['bodySpans']) == 1
    assert any('alpha and beta together' in body for body in bodies(result, 'open'))
    assert len(result['selectedIds']) == 5
    assert sum(len(f['display'].encode()) for f in result['frames'].values()) <= 32768


def test_new_policy_opens_second_query_instead_of_starving_it(tmp_path):
    root, data = source_case(tmp_path,
        ''.join(f'alpha row{i}\n' for i in range(5)) + 'neutral filler\n' * 1000 + 'beta decisive\n',
        ['alpha', 'beta'])
    legacy = prepare(root, data, data['cases'][0], 'manual')
    assert legacy['selectedIds'] == ['q0-s0', 'q0-s1', 'q0-s2', 'q0-s3', 'q0-s4']
    assert not any('beta decisive' in body for body in bodies(legacy, 'open'))
    data['retrievalPolicy'] = BALANCED
    result = prepare(root, data, data['cases'][0], 'manual')
    assert result['selectedIds'] == ['q0-s0', 'q1-s0', 'q0-s1', 'q0-s2', 'q0-s3']
    assert any('beta decisive' in body for body in bodies(result, 'open'))


def test_castle_round_robin_preserves_raw_ranks_and_expanded_seeds(tmp_path):
    chunks = []
    for prefix in [f'alpha record{i}\n' for i in range(5)] + ['beta decisive\n']:
        chunks.append(prefix + '.' * (800 - len(prefix)))
    root, data = source_case(tmp_path, ''.join(chunks), ['alpha', 'beta'])
    data['retrievalPolicy'] = BALANCED
    catalog, _, _ = catalog_for(root, data)
    ids = list(catalog['records'])
    provider = fixture_provider(root, data)
    strict = prepare(root, data, data['cases'][0], 'strict', provider=provider)
    assert strict['selectedIds'] == [ids[0], ids[5], ids[1], ids[2], ids[3]]
    assert [h['record_id'] for h in strict['audit'][0]['result']['hits']] == ids[:5]
    expanded = prepare(root, data, data['cases'][0], 'expanded', provider=provider,
        search_replay=[a['result'] for a in strict['audit']])
    assert expanded['selectedIds'] == strict['selectedIds']
    assert [a['result'] for a in expanded['audit']] == [a['result'] for a in strict['audit']]
    validate_capture(root, data, data['cases'][0], expanded)


def test_repeated_file_query_does_not_consume_duplicate_open_slots(tmp_path):
    root, data = source_case(tmp_path, 'alpha here\nbeta there\n', ['alpha', 'alpha', 'beta'])
    data['retrievalPolicy'] = BALANCED
    result = prepare(root, data, data['cases'][0], 'manual')
    assert result['selectedIds'] == ['q0-s0', 'q2-s0']


def test_explicit_policy_freezes_offline_and_rejects_empty_keyword_query(tmp_path):
    root, data = source_case(tmp_path, 'alpha memory\n', ['alpha memory'])
    output = tmp_path / 'balanced'
    freeze(tmp_path / 'dataset.json', tmp_path / 'policy.json', output, retrieval_policy=BALANCED)
    assert load_frozen(output)['retrievalPolicy'] == BALANCED
    original = json.loads((tmp_path / 'dataset.json').read_text())
    original['cases'][0]['queries'] = ['.* -- !!!']
    (tmp_path / 'dataset.json').write_text(json.dumps(original))
    with pytest.raises(ValueError, match='keyword'):
        freeze(tmp_path / 'dataset.json', tmp_path / 'policy.json', tmp_path / 'bad', retrieval_policy=BALANCED)
    assert not (tmp_path / 'bad').exists()


def test_unknown_retrieval_policy_rejected_before_any_provider_operation(tmp_path):
    root, data = source_case(tmp_path, 'alpha memory\n', ['alpha'])
    data['retrievalPolicy'] = 'unrecognized'
    with pytest.raises(ValueError, match='policy'):
        prepare(root, data, data['cases'][0], 'manual')


@pytest.mark.parametrize(('line', 'query'), [('area m²', 'm'), ('length x½', 'x'), ('ž🙂 foo²', 'foo')])
def test_rg_unicode_word_matches_keep_exact_character_anchors(tmp_path, line, query):
    root, data = source_case(tmp_path, line+'\n', [query])
    data['retrievalPolicy'] = BALANCED
    result = prepare(root, data, data['cases'][0], 'manual')
    assert bodies(result, 'search') == [line]
    assert bodies(result, 'open') == [line+'\n']
    validate_capture(root, data, data['cases'][0], result)


@pytest.mark.parametrize('separator', ['\u2028', '\r', '\x85'])
@pytest.mark.parametrize('policy', [None, BALANCED])
def test_rg_lf_line_numbers_survive_other_unicode_line_separators(tmp_path, separator, policy):
    first = 'prefix'+separator+'alpha on the first LF line'
    text = first+'\nbeta on the second LF line\n'
    root, data = source_case(tmp_path, text, ['alpha', 'beta'])
    if policy is not None:
        data['retrievalPolicy'] = policy
    result = prepare(root, data, data['cases'][0], 'manual')
    assert bodies(result, 'search') == [first, 'beta on the second LF line']
    assert bodies(result, 'open') == [text, text]
    validate_capture(root, data, data['cases'][0], result)


def test_overlapping_query_words_count_independently_before_top_five_selection(tmp_path):
    root, data = source_case(tmp_path, 'm\n'*5+'m²\n', ['m m²'])
    data['retrievalPolicy'] = BALANCED
    result = prepare(root, data, data['cases'][0], 'manual')
    assert bodies(result, 'search') == ['m²', 'm', 'm', 'm', 'm']
    assert len(result['selectedIds']) == 5
