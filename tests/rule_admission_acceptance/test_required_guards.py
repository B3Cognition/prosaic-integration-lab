"""3. The floor: required_guards in both forms; prose may tighten it, never weaken or conflict."""

import pytest

SEEN = 'args_reference_seen_ids(keys=[recordId], stage=before_tool, on_violation=fail)'
VALUES = 'value_in_tool_output(stage=final, on_violation=retry)'


def test_runtime_yml_declares_the_action_form_and_the_pinned_form():
    from lab_runner.rule_admission.blueprint import host

    assert host.load_config().required_guards == {
        'value_in_tool_output': 'retry',
        'args_reference_seen_ids': {'action': 'fail', 'stage': 'before_tool', 'settings': {'keys': ['recordId']}},
    }


def test_blueprint_prose_meets_the_floor_and_may_tighten_it(lab, provider, tmp_path):
    from lab_runner.rule_admission.blueprint import host

    tightened = lab.copy_project(
        tmp_path, {lab.agent: [(VALUES, 'value_in_tool_output(stage=final, on_violation=fail)')]}
    )
    for project in (None, tightened):
        config = host.load_config(base_url=provider.url)
        runtime = host.build_runtime(config, project=project or host.BLUEPRINT)
        runtime.prepare_turn(host.compose(project or host.BLUEPRINT), message=lab.happy_message, policy=host.policy())
    assert provider.raw_requests == []


@pytest.mark.parametrize(
    'old,new,detail',
    [
        (
            SEEN,
            'args_reference_seen_ids(keys=[recordId], stage=before_tool, on_violation=retry)',
            'required guard args_reference_seen_ids: action weaker than host minimum',
        ),
        (
            SEEN,
            'args_reference_seen_ids(keys=[recordId, branchCode], stage=before_tool, on_violation=fail)',
            'required guard args_reference_seen_ids: settings are pinned by host policy',
        ),
        (
            f' <!-- enforce: {VALUES} -->',
            '',
            'required guard value_in_tool_output is not bound to a registered guard',
        ),
    ],
    ids=['weaker-action-than-pin', 'settings-conflict-with-pin', 'required-guard-untagged'],
)
def test_prose_cannot_weaken_or_conflict_with_the_floor(lab, provider, tmp_path, old, new, detail):
    from prosaic_runtime import TurnAdmissionError

    with pytest.raises(TurnAdmissionError) as refused:
        lab.run_turn(provider, lab.happy_message, project=lab.copy_project(tmp_path, {lab.agent: [(old, new)]}))
    assert refused.value.code == 'invalidPolicy' and provider.raw_requests == []
    # The detail names the guard and the pin in host wording; it never echoes prose values.
    assert refused.value.detail == detail


def test_a_pinned_stage_applies_to_every_composed_file(lab, provider):
    """Pinning the custom guard to before_tool refuses the companion's after_tool binding."""
    from prosaic_runtime import TurnAdmissionError

    from lab_runner.rule_admission.blueprint import host

    floor = {
        **host.load_config().required_guards,
        'loan_period_within_policy': {'action': 'fix', 'stage': 'before_tool'},
    }
    with pytest.raises(TurnAdmissionError) as refused:
        lab.run_turn(provider, lab.happy_message, required_guards=floor)
    assert refused.value.code == 'invalidPolicy' and provider.raw_requests == []
    assert refused.value.detail == 'required guard loan_period_within_policy: stage is pinned by host policy'


def test_a_required_guard_the_host_did_not_register_fails_at_startup():
    from prosaic_runtime import generic_guards

    from lab_runner.rule_admission.blueprint import guards, host

    without = [guard for guard in generic_guards() if guard.name != 'args_reference_seen_ids'] + [guards.LOAN_PERIOD]
    with pytest.raises(ValueError):
        host.build_runtime(host.load_config(), guards=without)
