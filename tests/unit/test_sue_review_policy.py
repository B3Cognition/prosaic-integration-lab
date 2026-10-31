from dataclasses import replace
import pytest

from prosaic_integration_lab.sue_review.contracts import ReviewSettings, ReviewError


def test_direct_settings_construction_enforces_host_caps():
    for values in ({'enabled':1},{'max_turns':15},{'max_calls':True},{'lifetime_s':604801},{'timeout_s':61},{'engine_identity':'unqualified'}):
        with pytest.raises(ReviewError):ReviewSettings(**values)


def test_immutable_settings_cannot_expand_by_replacement():
    current=ReviewSettings.from_mapping({'enabled':True})
    with pytest.raises(ReviewError):replace(current,max_tokens=65537)
