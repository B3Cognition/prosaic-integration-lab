"""6. Coverage: which of this agent's rules are enforced, and by what, from inspect plus registry."""

import json
import subprocess
import sys


def expected_rows(lab, *, custom_registered=True):
    custom = ('loan-period-v1', 'enforced') if custom_registered else (None, 'unregistered')
    generic = 'generic'
    return [
        {
            'id': lab.ids.seen_ids,
            'guard': 'args_reference_seen_ids',
            'version': generic,
            'stage': 'before_tool',
            'action': 'fail',
            'status': 'enforced',
            'floor': 'pinned',
        },
        {
            'id': lab.ids.loan_before,
            'guard': 'loan_period_within_policy',
            'version': custom[0],
            'stage': 'before_tool',
            'action': 'fix',
            'status': custom[1],
            'floor': None,
        },
        {
            'id': lab.ids.links,
            'guard': 'no_wrapped_links',
            'version': generic,
            'stage': 'before_answer',
            'action': 'fix',
            'status': 'enforced',
            'floor': None,
        },
        {
            'id': lab.ids.values,
            'guard': 'value_in_tool_output',
            'version': generic,
            'stage': 'final',
            'action': 'retry',
            'status': 'enforced',
            'floor': 'retry',
        },
        {
            'id': lab.ids.prose_only,
            'guard': None,
            'version': None,
            'stage': None,
            'action': None,
            'status': 'prose-only',
            'floor': None,
        },
        {
            'id': lab.ids.loan_after,
            'guard': 'loan_period_within_policy',
            'version': custom[0],
            'stage': 'after_tool',
            'action': 'fail',
            'status': custom[1],
            'floor': None,
        },
    ]


def normalised(rows):
    """Generic guard versions belong to Runtime; the blueprint pins that they are reported, not their value."""
    generic = {'no_wrapped_links', 'value_in_tool_output', 'args_reference_seen_ids'}
    return [
        {**row, 'version': 'generic' if row['guard'] in generic and row['version'] else row['version']} for row in rows
    ]


def test_coverage_answers_which_rules_are_enforced_and_by_what(lab):
    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import coverage

    report = coverage.report(BLUEPRINT)
    assert normalised(report['rules']) == expected_rows(lab)
    assert report['issues'] == 0 and report['admitted'] is True
    assert report['fingerprint'] is not None and len(report['fingerprint']) == 64


def test_coverage_agrees_with_runtime_rule_coverage(lab):
    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import coverage, host

    runtime = host.build_runtime(host.load_config())
    official = runtime.rule_coverage(host.compose(BLUEPRINT))
    rows = coverage.report(BLUEPRINT)['rules']
    assert official['registered'] == [row['id'] for row in rows if row['status'] == 'enforced']
    assert official['proseOnly'] == [row['id'] for row in rows if row['status'] == 'prose-only']
    assert official['unregistered'] == [] and official['issues'] == 0


def test_coverage_names_rules_whose_guard_is_not_registered(lab):
    from prosaic_runtime import generic_guards

    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import coverage

    report = coverage.report(BLUEPRINT, guards=generic_guards())
    assert normalised(report['rules']) == expected_rows(lab, custom_registered=False)
    assert report['admitted'] is False and report['fingerprint'] is None


def test_coverage_command_prints_the_same_report_as_json(lab):
    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import coverage

    completed = subprocess.run(
        [sys.executable, '-m', 'lab_runner.rule_admission.blueprint.coverage', '--json'],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == json.loads(json.dumps(coverage.report(BLUEPRINT)))
    table = subprocess.run(
        [sys.executable, '-m', 'lab_runner.rule_admission.blueprint.coverage'],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert table.returncode == 0 and 'prose-only' in table.stdout and 'loan-period-v1' in table.stdout
