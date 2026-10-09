from decimal import Decimal
import httpx

from test_approval import headers, start
from test_accounting import count


def configure(lab, scenario):
    response = httpx.post(lab['model'] + '/control', json={'scenario': scenario}, timeout=5)
    assert response.status_code == 200


def test_missing_final_usage_is_unknown_not_zero(lab):
    configure(lab, 'missing_usage')
    try:
        before = count(lab)
        run = start(lab, workflow='synthetic').json()
        assert run['status'] == 'blocked'
        assert run['recovery_status'] == 'usage_reconciliation_required'
        usage = httpx.get(lab['b'] + '/runs/' + run['run_id'] + '/usage', headers=headers(lab), timeout=10).json()
        assert usage['total_calls'] == 1
        assert usage['fully_costed'] is False
        assert usage['unresolved_calls'] == 1
        assert usage['estimated_amounts'] == {}
        assert count(lab) == before + 1
    finally:
        configure(lab, 'normal')


def test_rejected_output_keeps_both_validation_attempts_usage(lab):
    configure(lab, 'invalid_output')
    try:
        before = count(lab)
        run = start(lab, workflow='synthetic').json()
        assert run['status'] == 'blocked'
        usage = httpx.get(lab['b'] + '/runs/' + run['run_id'] + '/usage', headers=headers(lab), timeout=10).json()
        assert usage['total_calls'] == 2
        assert usage['complete_calls'] == 2
        assert Decimal(usage['estimated_amounts']['USD']) == Decimal('0.00074')
        assert count(lab) == before + 2
    finally:
        configure(lab, 'normal')
