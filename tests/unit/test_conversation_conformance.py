from concurrent.futures import ThreadPoolExecutor
import json

import pytest


def test_unknown_attempt_keeps_shared_allowance(tmp_path):
    from lab_runner.live_allowance import SharedLiveAllowance,AllowanceExhausted
    allowance=SharedLiveAllowance(tmp_path/'allowance.json',max_calls=2)
    token=allowance.reserve(maximum_requests=2)
    allowance.finish(token,actual_requests=None)
    allowance.finish(token,actual_requests=None)
    with pytest.raises(AllowanceExhausted):allowance.reserve(maximum_requests=1)
    assert allowance.status()=={'maximum':2,'retained':2,'remaining':0,'unknown':1}


def test_known_completion_releases_only_unused_requests_and_replays(tmp_path):
    from lab_runner.live_allowance import SharedLiveAllowance
    first=SharedLiveAllowance(tmp_path/'allowance.json',max_calls=4)
    token=first.reserve(maximum_requests=3)
    first.finish(token,actual_requests=1)
    second=SharedLiveAllowance(tmp_path/'allowance.json',max_calls=4)
    second.finish(token,actual_requests=1)
    assert second.status()['remaining']==3
    with pytest.raises(ValueError):second.finish(token,actual_requests=0)


def test_concurrent_reservations_do_not_overspend(tmp_path):
    from lab_runner.live_allowance import SharedLiveAllowance,AllowanceExhausted
    path=tmp_path/'allowance.json'
    SharedLiveAllowance(path,max_calls=2)
    def reserve():
        try:return SharedLiveAllowance(path,max_calls=2).reserve(maximum_requests=1)
        except AllowanceExhausted:return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:reserve(),range(8)))
    assert len([value for value in results if value is not None])==2
    assert SharedLiveAllowance(path,max_calls=2).status()['remaining']==0


@pytest.mark.parametrize('maximum',[True,0,13,1.5])
def test_allowance_validates_finite_schedule_before_file_effects(tmp_path,maximum):
    from lab_runner.live_allowance import SharedLiveAllowance
    with pytest.raises(ValueError):SharedLiveAllowance(tmp_path/'allowance.json',max_calls=maximum)
    assert not (tmp_path/'allowance.json').exists()


def test_bound_and_corruption_cannot_reset_consumption(tmp_path):
    from lab_runner.live_allowance import SharedLiveAllowance
    path=tmp_path/'allowance.json'
    allowance=SharedLiveAllowance(path,max_calls=2)
    token=allowance.reserve(maximum_requests=2)
    with pytest.raises(ValueError):SharedLiveAllowance(path,max_calls=3)
    path.write_text('{"version":1,"version":1}')
    with pytest.raises(ValueError):allowance.finish(token,actual_requests=0)


def test_unknown_completion_cannot_be_changed_by_later_finish(tmp_path):
    from lab_runner.live_allowance import SharedLiveAllowance
    allowance=SharedLiveAllowance(tmp_path/'allowance.json',max_calls=2)
    token=allowance.reserve(maximum_requests=2)
    allowance.finish(token,actual_requests=None)
    with pytest.raises(ValueError):allowance.finish(token,actual_requests=0)


def test_symlink_state_and_unowned_permission_fail_closed(tmp_path):
    from lab_runner.live_allowance import SharedLiveAllowance
    target=tmp_path/'private.json'
    SharedLiveAllowance(target,max_calls=2)
    alias=tmp_path/'alias.json';alias.symlink_to(target)
    with pytest.raises(ValueError):SharedLiveAllowance(alias,max_calls=2)
    target.chmod(0o644)
    with pytest.raises(ValueError):SharedLiveAllowance(target,max_calls=2)


def write_profile(tmp_path):
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    profile=tmp_path/'conversation.json'
    profile.write_text(json.dumps({'runtime_config':str(root/'configs/runtime-local.example.yml'),
        'allowance_file':str(tmp_path/'allowance.json')}))
    return profile


def test_preflight_without_optin_does_not_create_allowance_or_open_credentials(tmp_path):
    from lab_runner.conversation_conformance import preflight
    plan=preflight(write_profile(tmp_path),max_calls=12)
    assert plan['mode']=='preflight' and plan['maximum_requests']==12
    assert not (tmp_path/'allowance.json').exists()


@pytest.mark.parametrize('allowance',[True,0,1,8,11,13])
def test_incomplete_live_schedule_fails_before_configuration(tmp_path,allowance):
    from lab_runner.conversation_conformance import preflight
    with pytest.raises(ValueError,match='allowance|schedule'):
        preflight(tmp_path/'missing.json',live_local=True,max_calls=allowance)


def test_live_modes_are_mutually_exclusive_before_configuration(tmp_path):
    from lab_runner.conversation_conformance import preflight
    with pytest.raises(ValueError,match='mode'):
        preflight(tmp_path/'missing.json',live_local=True,live_hosted=True,max_calls=12)


def test_missing_private_configuration_never_starts_live_allowance(tmp_path):
    from lab_runner.conversation_conformance import preflight
    with pytest.raises(ValueError,match='configuration'):
        preflight(tmp_path/'missing.json',live_local=True,max_calls=12)
    assert not (tmp_path/'allowance.json').exists()


def test_local_preflight_returns_distinct_approved_qwen_tiers(tmp_path):
    from lab_runner.conversation_conformance import preflight,public_preflight
    plan=preflight(write_profile(tmp_path),live_local=True,max_calls=12)
    view=public_preflight(plan)
    assert view['mode']=='local' and view['dispatches']==0
    assert view['tiers']==['balanced','strong']
    assert view['maximum_requests']==12
    encoded=json.dumps(view)
    assert '127.0.0.1' not in encoded and 'omlx_token' not in encoded and str(tmp_path) not in encoded
