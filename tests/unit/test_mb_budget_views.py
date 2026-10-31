"""Private harness renderer checks; synthetic data only."""
import hashlib
import importlib.util
from pathlib import Path


def module():
    from lab_runner.memory_benchmark import budget_views
    return budget_views


def test_search_broad_discovery_round_robin_and_no_hidden_payload():
    b = module().EvidenceBudget()
    files = [{'path': f'f{i:02}', 'count': 3} for i in range(18)]
    previews = [dict(selectionId=f'{i}-{j}', path=f'f{i:02}', line=j+1,
                     preview='z'*170, secret='DO NOT EXPOSE')
                for i in range(18) for j in range(3)]
    r = b.render_search('search', files, previews, maxBytes=4200)
    assert all(f['path'] in r['display'] for f in files)
    assert r['visibleSelectionIds'][:18] == [f'{i}-0' for i in range(18)]
    assert 'DO NOT EXPOSE' not in str(r)
    assert 'z'*161 not in r['display']
    assert r['omitted'] and '[omitted]' in r['display']
    assert r['bytes'] == len(r['display'].encode()) <= 4200


def test_budget_monotone_duplicates_charged_and_unicode_safe():
    b = module().EvidenceBudget(limit=400)
    p = [dict(selectionId='a', path='界', line=1, preview='🙂'*160)]
    a = b.render_memory_search('h', p, maxBytes=150)
    c = b.render_memory_search('h', p, maxBytes=150)
    assert a['display'] == c['display']
    assert b.used == a['bytes'] + c['bytes']
    for _ in range(10):
        r = b.render_memory_search('h', p, maxBytes=150)
        assert r['bytes'] == len(r['display'].encode('utf-8'))
    assert b.used <= 400
    b.charge('x' * (400 - b.used))
    used = b.used
    assert b.render_memory_search('h', p)['bytes'] == 0
    assert b.used == used
    try:
        b.used = 0
        assert False, 'budget counter must not be resettable'
    except AttributeError:
        pass


def rec(i, text):
    return dict(recordId=str(i), text=text,
                textSha256=hashlib.sha256(text.encode()).hexdigest())


def test_records_seed_priority_whole_chunks_source_order_and_raw_order():
    b = module().EvidenceBudget()
    records = [rec(i, str(i)*800) for i in range(5)]
    r = b.render_records('source', '2', records, limitBytes=2800)
    assert r['retainedIds'] == ['1', '2', '3']
    assert r['display'].index('@1 ') < r['display'].index('@2 ') < r['display'].index('@3 ')
    assert '1'*800 in r['display'] and '0'*100 not in r['display']
    assert '[omitted]' in r['display'] and r['bytes'] <= 2800
    a = b.render_memory_search('fts', [dict(selectionId=x, preview=x) for x in ['z','a','q']])
    assert a['visibleSelectionIds'] == ['z','a','q']


def test_five_ascii_800_character_chunks_fit_compact_context():
    b = module().EvidenceBudget()
    r = b.render_records('source path=x sha256='+'a'*64, '2', [rec(i, 'x'*800) for i in range(5)])
    assert r['retainedIds'] == ['0','1','2','3','4']
    assert r['bytes'] <= 5120 and not r['omitted']


def test_manual_window_is_exact_slice_centered_and_bounded():
    b = module().EvidenceBudget()
    source = ''.join(f'{i}:界🙂 line\n' for i in range(100))
    r = b.render_window('manual', source, 'note.md', 51, limitBytes=500)
    assert r['startChar'] < r['endChar']
    exact = source[r['startChar']:r['endChar']]
    assert exact in r['display'] and '50:界🙂 line' in exact
    assert r['bytes'] == len(r['display'].encode()) <= 500
    assert r['omitted'] and '[omitted]' in r['display']


def test_small_caps_never_overshoot_and_invalid_budget_rejected():
    m = module()
    for cap in range(40):
        b = m.EvidenceBudget(limit=cap)
        r = b.render_memory_search('heading🙂'*20, [dict(selectionId='x', preview='界'*100)])
        assert len(r['display'].encode()) <= cap
        assert r['bytes'] == b.used
        assert 'x' not in r['visibleSelectionIds']
    for cap in [-1, True, 1.1]:
        try:
            m.EvidenceBudget(limit=cap)
            assert False, 'invalid cap accepted'
        except ValueError:
            pass


def test_omitted_manual_frame_has_marker_and_charge_failure_is_atomic():
    b = module().EvidenceBudget(limit=100)
    r = b.render_window('h', 'data\n', 'very-long-path-'*100, 1, limitBytes=45)
    assert r['omitted'] and '[omitted]' in r['display']
    used = b.used
    try:
        b.charge('x'*101)
        assert False, 'unbounded display was accepted'
    except ValueError:
        pass
    assert b.used == used


def test_manual_window_can_anchor_exact_match_within_very_long_line():
    b = module().EvidenceBudget()
    source = 'NEEDLE ' + '界'*10000 + '\n'
    r = b.render_window('h', source, 'x', 1, anchorChar=2, limitBytes=500)
    assert source[r['startChar']:r['endChar']].startswith('NEEDLE ')
    assert r['bytes'] <= 500


def test_memory_search_displays_charged_trusted_scope_and_source_hash_only():
    b = module().EvidenceBudget()
    metadata = dict(sourceFileSha256='a'*64, sourceId='source-1', wing='notes',
                    revision='revision-1', namespace='private-pilot')
    preview = dict(selectionId='seed', preview='excerpt', hiddenExtra='NEVER DISPLAY',
                   **metadata)
    r = b.render_memory_search('search', [preview])
    for key, value in metadata.items():
        assert f'{key}="{value}"' in r['display']
    assert 'NEVER DISPLAY' not in str(r) and 'hiddenExtra' not in str(r)
    assert r['bytes'] == len(r['display'].encode()) == b.used


def test_exact_source_bounds_visible_and_charged_without_hidden_fields():
    b = module().EvidenceBudget()
    bounds = dict(startLine=7, endLine=12, startChar=123, endChar=456)
    record = dict(rec('r', 'source slice'), secret='DO NOT EXPOSE', **bounds)
    r = b.render_records('source', 'r', [record])
    assert r['retainedIds'] == ['r']
    for key, value in bounds.items():
        assert f'{key}="{value}"' in r['display']
    p = dict(selectionId='r', preview='source slice', line=7, endLine=12,
             startChar=123, endChar=456, secret='DO NOT EXPOSE')
    s = b.render_memory_search('search', [p])
    for key in ('line', 'endLine', 'startChar', 'endChar'):
        assert f'{key}="{p[key]}"' in s['display']
    assert 'secret' not in str(r) + str(s) and 'DO NOT EXPOSE' not in str(r) + str(s)
    assert b.used == len(r['display'].encode()) + len(s['display'].encode())
