"""2. Guard registration: four generic guards plus one custom guard the blueprint defines."""

import pytest

LOAN_TAG = 'loan_period_within_policy(max_days=21, stage=before_tool, on_violation=fix)'


def test_registry_is_the_four_generic_guards_plus_the_custom_domain_guard():
    from lab_runner.rule_admission.blueprint import guards

    registry = {guard.name: guard for guard in guards.registry()}
    assert set(registry) == {
        'no_wrapped_links',
        'value_in_tool_output',
        'args_reference_seen_ids',
        'strict_json',
        'loan_period_within_policy',
    }
    custom = registry['loan_period_within_policy']
    assert custom is guards.LOAN_PERIOD
    assert (custom.version, custom.stages, custom.fixes, custom.echo_values) == (
        'loan-period-v1',
        ('before_tool', 'after_tool'),
        True,
        False,
    )
    schema = custom.settings_schema
    assert schema['additionalProperties'] is False and schema['required'] == ['max_days']
    assert schema['properties']['max_days']['type'] == 'integer'


@pytest.mark.parametrize(
    'replacement',
    [
        'loan_period_within_policy(max_days=long, stage=before_tool, on_violation=fix)',
        'loan_period_within_policy(max_days=21, grace=3, stage=before_tool, on_violation=fix)',
        'loan_period_within_policy(stage=before_tool, on_violation=fix)',
    ],
    ids=['wrong-type', 'unknown-key', 'missing-required'],
)
def test_custom_guard_settings_are_validated_before_any_request(lab, provider, tmp_path, replacement):
    from prosaic_runtime import TurnAdmissionError

    project = lab.copy_project(tmp_path, {lab.agent: [(LOAN_TAG, replacement)]})
    with pytest.raises(TurnAdmissionError) as refused:
        lab.run_turn(provider, lab.happy_message, project=project, required_guards=lab.generic_floor)
    assert refused.value.code == 'invalidArtifact' and provider.raw_requests == []


@pytest.mark.parametrize(
    'replacement',
    [
        'loan_period_within_policy(max_days=21, stage=final, on_violation=fail)',
        'strict_json(stage=before_tool, on_violation=retry)',
    ],
    ids=['custom-guard-unsupported-stage', 'generic-guard-unsupported-stage'],
)
def test_a_stage_the_guard_does_not_declare_is_refused(lab, provider, tmp_path, replacement):
    from prosaic_runtime import TurnAdmissionError

    project = lab.copy_project(tmp_path, {lab.agent: [(LOAN_TAG, replacement)]})
    with pytest.raises(TurnAdmissionError) as refused:
        lab.run_turn(provider, lab.happy_message, project=project, required_guards=lab.generic_floor)
    assert refused.value.code == 'invalidArtifact' and provider.raw_requests == []


def test_fix_on_a_guard_that_cannot_repair_is_refused(lab, provider, tmp_path):
    from prosaic_runtime import TurnAdmissionError

    edits = {
        lab.agent: [
            (
                'value_in_tool_output(stage=final, on_violation=retry)',
                'value_in_tool_output(stage=final, on_violation=fix)',
            )
        ]
    }
    with pytest.raises(TurnAdmissionError) as refused:
        lab.run_turn(provider, lab.happy_message, project=lab.copy_project(tmp_path, edits))
    assert refused.value.code == 'invalidArtifact' and provider.raw_requests == []


def test_prose_naming_an_unregistered_guard_is_refused_never_run_unenforced(lab, provider):
    from prosaic_runtime import TurnAdmissionError, generic_guards

    with pytest.raises(TurnAdmissionError) as refused:
        lab.run_turn(provider, lab.happy_message, guards=generic_guards(), required_guards=lab.generic_floor)
    assert refused.value.code == 'invalidArtifact' and provider.raw_requests == []
