"""Regressions from an adversarial review of the blueprint: each test failed before its fix."""

import json
import subprocess
import sys
import warnings

import pytest

SEARCH = ('call-1', 'catalogue_search', {'query': 'Invented Rivers'})
FIRST_RULE = '- Search the catalogue before answering any question about a book.'


def recording_tools(calls):
    from lab_runner.rule_admission.blueprint import host

    return host.library_tools(on_call=lambda name, arguments: calls.append((name, arguments)))


def context(stage, *, arguments=None, tool_result=None, tool_name='place_loan'):
    from prosaic_runtime import GuardContext

    return GuardContext(
        stage,
        'subagents/catalogue-desk.md:10:loan_period_within_policy',
        'Never request a loan longer than the 21-day loan policy.',
        'subagents/catalogue-desk.md',
        {'max_days': 21},
        {},
        'borrow',
        None,
        (),
        tool_name=tool_name,
        arguments=arguments,
        tool_result=tool_result,
    )


# Bug 1: JSON Schema "integer" admits 28.0, which the guard skipped, so an over-policy loan ran unchanged.
def test_whole_number_float_loan_days_are_repaired_not_waved_through(lab, provider):
    calls = []
    provider.queue_calls(SEARCH)
    provider.queue_calls(('call-2', 'place_loan', {'recordId': 'CAT-0001', 'days': 28.0}))
    provider.queue_text('Your loan is due back in 21 days.')
    turn = lab.run_turn(provider, 'Borrow the Atlas for four weeks.', tools=recording_tools(calls))
    assert turn.result.exit_code == 0 and lab.ids.loan_before in turn.rules_fixed
    assert [arguments for name, arguments in calls if name == 'place_loan'] == [{'recordId': 'CAT-0001', 'days': 21}]


@pytest.mark.parametrize('days', [28.0, 22, 365, 10**400])
def test_before_tool_repairs_every_numeric_period_above_policy(days):
    from lab_runner.rule_admission.blueprint.guards import LOAN_PERIOD

    verdict = LOAN_PERIOD.check('before_tool', context('before_tool', arguments={'recordId': 'CAT-0001', 'days': days}))
    assert verdict.ok is False and verdict.fixed == {'recordId': 'CAT-0001', 'days': 21}


@pytest.mark.parametrize('days', [1, 21, 21.0])
def test_before_tool_accepts_periods_within_policy(days):
    from lab_runner.rule_admission.blueprint.guards import LOAN_PERIOD

    assert LOAN_PERIOD.check('before_tool', context('before_tool', arguments={'recordId': 'CAT-0001', 'days': days})).ok


# Bug 2: after_tool ignored any loanDays that was not an int, so a desk reporting 35.0 or "35" passed.
@pytest.mark.parametrize('reported', [35, 35.0, '35', True, None, [35]])
def test_after_tool_fails_closed_on_a_placed_loan_it_cannot_confirm(reported):
    from lab_runner.rule_admission.blueprint.guards import LOAN_PERIOD

    result = {'status': 'ok', 'result': {'recordId': 'CAT-0001', 'loanDays': reported}}
    assert LOAN_PERIOD.check('after_tool', context('after_tool', tool_result=result)).ok is False


def test_after_tool_fails_closed_when_a_placed_loan_omits_its_period():
    from lab_runner.rule_admission.blueprint.guards import LOAN_PERIOD

    result = {'status': 'ok', 'result': {'recordId': 'CAT-0001'}}
    assert LOAN_PERIOD.check('after_tool', context('after_tool', tool_result=result)).ok is False


@pytest.mark.parametrize(
    'result',
    [
        {'status': 'ok', 'result': {'recordId': 'CAT-0001', 'loanDays': 21}},
        {'status': 'ok', 'result': {'recordId': 'CAT-0001', 'loanDays': 21.0}},
        {'status': 'ok', 'result': {'error': 'unknown record'}},
        {'status': 'error', 'error': {'code': 'toolFailed'}},
    ],
    ids=['within-policy', 'within-policy-float', 'no-loan-placed', 'tool-error'],
)
def test_after_tool_accepts_confirmed_or_absent_loans(result):
    from lab_runner.rule_admission.blueprint.guards import LOAN_PERIOD

    assert LOAN_PERIOD.check('after_tool', context('after_tool', tool_result=result)).ok


def test_a_desk_reporting_a_float_period_above_policy_fails_the_turn(lab, provider):
    from prosaic_runtime import CustomTool

    from lab_runner.rule_admission.blueprint import host

    tools = host.library_tools()
    tools['place_loan'] = CustomTool(
        'place_loan',
        'Place a synthetic loan',
        host.PLACE_LOAN_SCHEMA,
        lambda arguments: {'recordId': arguments['recordId'], 'loanDays': 35.0},
        'loan-desk-fault-v2',
    )
    provider.queue_calls(SEARCH)
    provider.queue_calls(('call-2', 'place_loan', {'recordId': 'CAT-0001', 'days': 14}))
    turn = lab.run_turn(provider, lab.happy_message, tools=tools)
    assert lab.failure(turn) == 'ruleViolation' and turn.rules_violated == (lab.ids.loan_after,)


# Bugs 3-6: coverage reimplemented admission and disagreed with it. Coverage must equal real admission.
def malformed(lab, tmp_path):
    tag = ' <!-- enforce: no_wrapped_links(stage=nowhere) -->'
    return lab.copy_project(tmp_path, {lab.agent: [(FIRST_RULE, FIRST_RULE + tag)]})


def path_setting(lab, tmp_path):
    rule = '- Shelf marks follow the local list. <!-- enforce: shelf_list(file="shelves.txt", stage=final) -->'
    project = lab.copy_project(tmp_path, {lab.agent: [(FIRST_RULE, rule)]})
    (project / 'shelves.txt').write_text('RIV-12\n')
    return project


def superseded(lab, tmp_path):
    project = lab.copy_project(tmp_path)
    companion = lab.path(project, lab.companion)
    tag = '<!-- enforce: value_in_tool_output(stage=final, on_violation=fail) -->'
    companion.write_text(companion.read_text() + f'- Never quote an unlisted fee. {tag}\n')
    return project


def conflicting_settings(lab, tmp_path):
    """Same guard and stage in two files, different settings and actions (Runtime 65ba15d: refused)."""
    project = lab.copy_project(tmp_path)
    companion = lab.path(project, lab.companion)
    tag = '<!-- enforce: value_in_tool_output(currencies=[GBP], stage=final, on_violation=fail) -->'
    companion.write_text(companion.read_text() + f'- Quote fees only as the desk lists them. {tag}\n')
    return project


def loan_limit_raised(lab, tmp_path):
    tag = 'loan_period_within_policy(max_days=21, stage=before_tool, on_violation=fix)'
    return lab.copy_project(tmp_path, {lab.agent: [(tag, tag.replace('21', '365'))]})


def fix_at_after_tool(lab, tmp_path):
    tag = 'loan_period_within_policy(max_days=21, stage=after_tool, on_violation=fail)'
    return lab.copy_project(tmp_path, {lab.companion: [(tag, tag.replace('fail', 'fix'))]})


def loan_check_moved_after_tool(lab, tmp_path):
    tag = 'loan_period_within_policy(max_days=21, stage=before_tool, on_violation=fix)'
    return lab.copy_project(
        tmp_path, {lab.agent: [(tag, tag.replace('before_tool', 'after_tool').replace('fix)', 'fail)'))]}
    )


def loan_companion_dropped(lab, tmp_path):
    tag = ' <!-- enforce: loan_period_within_policy(max_days=21, stage=after_tool, on_violation=fail) -->'
    return lab.copy_project(tmp_path, {lab.companion: [(tag, '')]})


def weaker_than_floor(lab, tmp_path):
    seen = 'args_reference_seen_ids(keys=[recordId], stage=before_tool, on_violation='
    return lab.copy_project(tmp_path, {lab.agent: [(seen + 'fail)', seen + 'retry)')]})


def shelf_guard():
    from prosaic_runtime import Guard, Verdict

    schema = {'type': 'object', 'additionalProperties': False, 'properties': {'file': {'type': 'string'}}}
    return Guard(
        'shelf_list',
        'shelf-list-v1',
        ('final',),
        lambda stage, ctx: Verdict(True),
        settings_schema=schema,
        path_settings=('file',),
    )


def registry_plus_shelf():
    from lab_runner.rule_admission.blueprint import guards

    return [*guards.registry(), shelf_guard()]


def generic_only():
    from prosaic_runtime import generic_guards

    return generic_guards()


def without_required_guard():
    from prosaic_runtime import generic_guards

    from lab_runner.rule_admission.blueprint import guards

    return [guard for guard in generic_guards() if guard.name != 'args_reference_seen_ids'] + [guards.LOAN_PERIOD]


VARIANTS = {
    'blueprint': (None, None, True, None),
    'malformed-tag': (malformed, None, False, 'invalidArtifact'),
    'path-setting-guard': (path_setting, registry_plus_shelf, True, None),
    'superseded-cross-file': (superseded, None, True, None),
    'conflicting-settings-cross-file': (conflicting_settings, None, False, 'invalidArtifact'),
    'loan-limit-raised': (loan_limit_raised, None, False, 'invalidPolicy'),
    'fix-at-after-tool': (fix_at_after_tool, None, False, 'hostPolicy'),
    'loan-check-moved-after-tool': (loan_check_moved_after_tool, None, False, 'hostPolicy'),
    'loan-companion-dropped': (loan_companion_dropped, None, False, 'hostPolicy'),
    'weaker-than-floor': (weaker_than_floor, None, False, 'invalidPolicy'),
    'custom-guard-unregistered': (None, generic_only, False, 'startup'),
    'required-guard-unregistered': (None, without_required_guard, False, 'startup'),
    'stripped-under-floor': ('strip', None, False, 'invalidPolicy'),
}


def real_admission(project, guards):
    from prosaic_runtime import TurnAdmissionError

    from lab_runner.rule_admission.blueprint import host

    try:
        runtime = host.build_runtime(host.load_config(project / 'runtime.yml'), project=project, guards=guards)
    except ValueError:
        return 'startup'
    try:
        artifact = host.compose(project)
    except ValueError:
        return 'hostPolicy'
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            runtime.prepare_turn(artifact, message='coverage check', policy=host.policy())
    except TurnAdmissionError as error:
        return error.code
    return None


@pytest.mark.parametrize('name', list(VARIANTS))
def test_coverage_verdict_always_equals_real_admission(lab, tmp_path, name):
    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import coverage

    build, guards, admitted, refusal = VARIANTS[name]
    if build is None:
        project = BLUEPRINT
    elif build == 'strip':
        project = lab.copy_project(tmp_path, strip=True)
    else:
        project = build(lab, tmp_path)
    registered = None if guards is None else guards()
    report = coverage.report(project, guards=registered)
    assert (report['admitted'], report['refusal']) == (admitted, refusal)
    assert real_admission(project, None if guards is None else guards()) == refusal
    assert (report['fingerprint'] is not None) == (admitted and name != 'stripped-under-floor')


def test_coverage_command_exits_non_zero_on_a_malformed_tag(lab, tmp_path):
    project = malformed(lab, tmp_path)
    completed = subprocess.run(
        [sys.executable, '-m', 'lab_runner.rule_admission.blueprint.coverage', '--project', str(project), '--json'],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 1, completed.stderr
    data = json.loads(completed.stdout)
    assert data['issues'] == 1 and data['admitted'] is False


def test_coverage_marks_a_binding_superseded_by_a_stronger_one_in_another_file(lab, tmp_path):
    from lab_runner.rule_admission.blueprint import coverage

    report = coverage.report(superseded(lab, tmp_path))
    rows = {row['id']: row for row in report['rules'] if row['guard'] == 'value_in_tool_output'}
    assert rows[lab.ids.values]['status'] == 'superseded'
    stronger = rows[f'{lab.companion}:4:value_in_tool_output']
    assert (stronger['status'], stronger['action']) == ('enforced', 'fail')
    assert len(report['warnings']) == 1 and 'final' in report['warnings'][0]


def test_coverage_fingerprint_matches_the_turn_fingerprint_with_path_settings(lab, provider, tmp_path):
    from lab_runner.rule_admission.blueprint import coverage

    project = path_setting(lab, tmp_path)
    report = coverage.report(project, guards=registry_plus_shelf())
    lab.queue_happy(provider)
    turn = lab.run_turn(provider, lab.happy_message, project=project, guards=registry_plus_shelf())
    assert turn.result.exit_code == 0 and report['fingerprint'] == turn.rules_fingerprint


# Bug 8: compose accepted the agent or one companion twice, duplicating prose and rules silently.
@pytest.mark.parametrize(
    'companions',
    [('companions/loan-desk.md', 'companions/loan-desk.md'), ('subagents/catalogue-desk.md',)],
    ids=['companion-twice', 'agent-as-companion'],
)
def test_compose_refuses_duplicate_files(companions):
    from lab_runner.rule_admission.blueprint import host

    with pytest.raises(ValueError, match='distinct'):
        host.compose(companions=companions)
