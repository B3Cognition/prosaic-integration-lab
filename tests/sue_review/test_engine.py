import sys

import pytest

from prosaic_integration_lab.sue_review.engine import load_engine


def test_engine_is_separately_installable_and_identity_checked():
    engine = load_engine()
    caps = engine.capabilities()
    assert len(caps['lenses']) == 9
    assert caps['apiVersion'] == 1 and caps['policyVersion'] == '2026-09-24'
    assert 'cognitive_castle' not in sys.modules
    with pytest.raises(ValueError):
        load_engine('0'*64)
