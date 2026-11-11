"""Regressions from the PR #45 re-review: each case uses the reviewer's probe inputs."""

import pytest

LOAN_TAG = 'loan_period_within_policy(max_days=21, stage=before_tool, on_violation=fix)'
COMPANION_TAG = 'loan_period_within_policy(max_days=21, stage=after_tool, on_violation=fail)'
SEARCH = ('call-1', 'catalogue_search', {'query': 'Invented Rivers'})
LONG_LOAN = ('call-2', 'place_loan', {'recordId': 'CAT-0001', 'days': 300})


def recording_tools(calls):
    from lab_runner.rule_admission.blueprint import host

    return host.library_tools(on_call=lambda name, arguments: calls.append((name, arguments)))


# [P1] Prose must not move the loan check from before the loan to after it, or drop either stage.
STAGE_EDITS = {
    'drop-preventive-tag': (lambda lab: lab.agent, f' <!-- enforce: {LOAN_TAG} -->', '', 'before_tool'),
    'move-to-after-tool': (lambda lab: lab.agent, LOAN_TAG, COMPANION_TAG, 'before_tool'),
    'drop-companion-tag': (lambda lab: lab.companion, f' <!-- enforce: {COMPANION_TAG} -->', '', 'after_tool'),
}


def stage_edit(lab, tmp_path, name):
    target, old, new, _ = STAGE_EDITS[name]
    return lab.copy_project(tmp_path, {target(lab): [(old, new)]})


def test_the_host_requires_the_loan_guard_at_both_stages():
    from lab_runner.rule_admission.blueprint import guards

    assert guards.REQUIRED_STAGES == {'loan_period_within_policy': ('before_tool', 'after_tool')}


@pytest.mark.parametrize('edit', list(STAGE_EDITS))
def test_prose_cannot_move_or_drop_a_loan_check_stage(lab, provider, tmp_path, edit):
    calls = []
    project = stage_edit(lab, tmp_path, edit)
    provider.queue_calls(SEARCH)
    provider.queue_calls(LONG_LOAN)
    provider.queue_text('Your loan is due back in 300 days.')
    missing = STAGE_EDITS[edit][3]
    with pytest.raises(ValueError, match=f'loan_period_within_policy must be bound at {missing}'):
        lab.run_turn(provider, 'Borrow the Atlas for most of a year.', project=project, tools=recording_tools(calls))
    assert provider.raw_requests == [] and calls == []


@pytest.mark.parametrize('edit', list(STAGE_EDITS))
def test_coverage_reports_a_missing_loan_check_stage_as_host_policy(lab, tmp_path, edit):
    from lab_runner.rule_admission.blueprint import coverage

    report = coverage.report(stage_edit(lab, tmp_path, edit))
    assert (report['admitted'], report['refusal']) == (False, 'hostPolicy')


def test_an_agent_without_any_loan_binding_is_left_to_the_floor(lab, tmp_path):
    """The host checks where a bound guard runs; whether it is bound at all is the floor's job."""
    from prosaic_runtime import TurnAdmissionError

    from lab_runner.rule_admission.blueprint import host

    project = lab.copy_project(tmp_path, strip=True)
    artifact = host.compose(project)  # No binding, so no stage to check: the untagged agent composes.
    runtime = host.build_runtime(host.load_config(), project=project)
    with pytest.raises(TurnAdmissionError) as refused:
        runtime.prepare_turn(artifact, message='check', policy=host.policy())
    assert refused.value.code == 'invalidPolicy'


# Belt and braces: the loan desk itself never places a loan above policy, even with no guard registered.
def test_the_loan_desk_refuses_a_period_above_policy_without_any_guard(lab, provider, tmp_path):
    provider.queue_calls(SEARCH)
    provider.queue_calls(LONG_LOAN)
    provider.queue_text('The desk refused that loan period.')
    project = lab.copy_project(tmp_path, strip=True)
    turn = lab.run_turn(provider, 'Borrow the Atlas for 300 days.', project=project, guards=(), required_guards={})
    outcome = turn.evidence.to_dict()['toolOutcomes'][-1]
    assert outcome['name'] == 'place_loan' and outcome['outcome']['result'] == {'error': 'loan period above policy'}


def test_the_guard_still_repairs_before_the_desk_would_refuse(lab, provider):
    calls = []
    provider.queue_calls(SEARCH)
    provider.queue_calls(LONG_LOAN)
    provider.queue_text('Your loan is due back in 21 days.')
    turn = lab.run_turn(provider, 'Borrow the Atlas for 300 days.', tools=recording_tools(calls))
    assert turn.rules_fixed == (lab.ids.loan_before,) and calls[-1] == (
        'place_loan',
        {'recordId': 'CAT-0001', 'days': 21},
    )
    assert turn.evidence.to_dict()['toolOutcomes'][-1]['outcome']['result'] == {'recordId': 'CAT-0001', 'loanDays': 21}


# Smaller point: value_in_tool_output reads a currency symbol after the number.
def test_an_invented_fee_with_a_trailing_symbol_is_retried(lab, provider):
    provider.queue_calls(('call-1', 'loan_terms', {'recordId': 'CAT-0001'}))
    provider.queue_text('The late fee is 1.20 € per day.')
    provider.queue_text('The late fee is EUR 0.40 per day.')
    turn = lab.run_turn(provider, 'What is the late fee for CAT-0001?')
    assert turn.rules_violated == (lab.ids.values,) and len(provider.raw_requests) == 3


def test_documented_fee_formats_are_required_passes_after_value_guard_v2():
    import ast
    from pathlib import Path

    from lab_runner.rule_admission import BLUEPRINT

    review = (Path(__file__).parent / 'test_pr_review.py').read_text()
    fee_case = next(node for node in ast.parse(review).body if isinstance(node, ast.FunctionDef)
        and node.name == 'test_an_invented_fee_is_retried_in_every_common_format')
    assert all('xfail' not in ast.unparse(mark) for mark in fee_case.decorator_list)
    readme = ' '.join((BLUEPRINT / 'README.md').read_text().split())
    assert '`1.20 €`' in readme and 'does not yet read a marker after the number' not in readme
    for fee in ('1.20 EUR', '1.20 euros', '120 cents'):
        assert fee in ast.unparse(fee_case) and '`' + fee + '`' in readme
    assert 'value-in-tool-output-v2' in readme and 'require passes on both wires' in readme


# Smaller point: frontmatter after a BOM or leading blank lines is still frontmatter.
@pytest.mark.parametrize('prefix', ['\ufeff', '\n\n', ' \t\r\n'], ids=['bom', 'blank-lines', 'whitespace'])
def test_compose_refuses_companion_frontmatter_behind_leading_whitespace(lab, tmp_path, prefix):
    from lab_runner.rule_admission.blueprint import host

    project = lab.copy_project(tmp_path)
    path = lab.path(project, lab.companion)
    path.write_text(prefix + '---\nname: loan-desk\ntools: [place_loan]\n---\n' + path.read_text(), encoding='utf-8')
    with pytest.raises(ValueError, match='frontmatter'):
        host.compose(project)


# Smaller point: the README table header appeared twice.
def test_readme_tables_have_one_header_each():
    from lab_runner.rule_admission import BLUEPRINT

    lines = (BLUEPRINT / 'README.md').read_text().splitlines()
    separators = [i for i, line in enumerate(lines) if line.startswith('| ---')]
    assert all(lines[i - 1].startswith('|') and not lines[i - 2].startswith('|') for i in separators), 'repeated header'
