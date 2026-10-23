"""Explicit candidate-only contract; missing pool SDK must fail, never skip."""


def test_controls_restore_only_their_own_marks_and_preserve_provider_cooldowns(tmp_path):
    from prosaic_runtime import CapacityStore
    from lab_runner.native_eval.unified_benchmark import controlled_capacity
    store = CapacityStore(tmp_path / 'capacity.json')
    quotas = {'claude': 'c', 'codex': 'x', 'local': 'l'}
    store.mark_unavailable('c', reason='rate_limit', until=9999999999)
    with controlled_capacity(store, quotas, ('claude', 'codex')):
        assert not store.available('c') and not store.available('x')
        store.mark_unavailable('l', reason='usage_limit', until=9999999998)
    assert store.status('c') == {'state': 'cooling_down', 'reason': 'rate_limit', 'until': 9999999999}
    assert store.available('x') and not store.available('l')
