"""Regressions from the PR #45 review: each case uses the reviewer's reproduction inputs."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

LOAN_TAG = 'loan_period_within_policy(max_days=21, stage=before_tool, on_violation=fix)'
COMPANION_TAG = 'loan_period_within_policy(max_days=21, stage=after_tool, on_violation=fail)'
SEARCH = ('call-1', 'catalogue_search', {'query': 'Invented Rivers'})


def recording_tools(calls):
    from lab_runner.rule_admission.blueprint import host

    return host.library_tools(on_call=lambda name, arguments: calls.append((name, arguments)))


# [P1] The floor must protect the custom loan guard, not only the generic guards.
def test_floor_pins_the_custom_loan_guard_settings():
    from lab_runner.rule_admission.blueprint import host

    assert host.load_config().required_guards['loan_period_within_policy'] == {
        'action': 'fix',
        'settings': {'max_days': 21},
    }


def test_raising_the_loan_limit_in_prose_is_refused_before_any_request(lab, provider, tmp_path):
    from prosaic_runtime import TurnAdmissionError

    edits = {
        lab.agent: [(LOAN_TAG, LOAN_TAG.replace('max_days=21', 'max_days=365'))],
        lab.companion: [(COMPANION_TAG, COMPANION_TAG.replace('max_days=21', 'max_days=365'))],
    }
    with pytest.raises(TurnAdmissionError) as refused:
        lab.run_turn(provider, lab.happy_message, project=lab.copy_project(tmp_path, edits))
    assert refused.value.code == 'invalidPolicy' and provider.raw_requests == []
    assert refused.value.detail == 'required guard loan_period_within_policy: settings are pinned by host policy'


def test_deleting_the_loan_tags_is_refused_before_any_request(lab, provider, tmp_path):
    from prosaic_runtime import TurnAdmissionError

    edits = {
        lab.agent: [(f' <!-- enforce: {LOAN_TAG} -->', '')],
        lab.companion: [(f' <!-- enforce: {COMPANION_TAG} -->', '')],
    }
    with pytest.raises(TurnAdmissionError) as refused:
        lab.run_turn(provider, lab.happy_message, project=lab.copy_project(tmp_path, edits))
    assert refused.value.code == 'invalidPolicy' and provider.raw_requests == []
    assert refused.value.detail == 'required guard loan_period_within_policy is not bound to a registered guard'


def test_a_300_day_request_is_still_repaired_under_the_floor(lab, provider):
    calls = []
    provider.queue_calls(SEARCH)
    provider.queue_calls(('call-2', 'place_loan', {'recordId': 'CAT-0001', 'days': 300}))
    provider.queue_text('Your loan is due back in 21 days.')
    turn = lab.run_turn(provider, 'Borrow the Atlas for most of a year.', tools=recording_tools(calls))
    assert turn.result.exit_code == 0 and lab.ids.loan_before in turn.rules_fixed
    assert calls[-1] == ('place_loan', {'recordId': 'CAT-0001', 'days': 21})


# General point: one limit, written in several places, must never drift silently.
def test_the_loan_limit_agrees_in_prose_tags_floor_and_tool_data(lab):
    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import host

    pinned = host.load_config().required_guards['loan_period_within_policy']['settings']['max_days']
    artifact = host.compose(BLUEPRINT)
    loan_rules = [entry for entry in artifact.rules if entry['guard'] == 'loan_period_within_policy']
    assert {entry['settings']['max_days'] for entry in loan_rules} == {pinned}
    stated = {int(days) for days in re.findall(r'(\d+)-day', ' '.join(entry['text'] for entry in loan_rules))}
    assert stated == {pinned}
    assert host.LOAN_TERMS['loanDays'] == pinned


# [P2] The id rule must say what args_reference_seen_ids enforces: the message counts as evidence.
def test_id_rule_prose_names_both_sources_the_guard_accepts(lab):
    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import host

    text = next(entry['text'] for entry in host.compose(BLUEPRINT).rules if entry['id'] == lab.ids.seen_ids)
    assert 'the borrower named' in text and 'the catalogue search returned' in text


def test_an_id_the_borrower_named_is_accepted_without_a_search(lab, provider):
    calls = []
    provider.queue_calls(('call-1', 'place_loan', {'recordId': 'CAT-0002', 'days': 14}))
    provider.queue_text('Your loan is due back in 14 days.')
    turn = lab.run_turn(provider, 'Please borrow CAT-0002 for 14 days.', tools=recording_tools(calls))
    assert turn.result.exit_code == 0 and turn.rules_violated == ()
    assert calls == [('place_loan', {'recordId': 'CAT-0002', 'days': 14})]


def test_an_id_laundered_through_a_search_query_is_refused(lab, provider):
    """The reviewer's control: a query containing an id is not evidence the record exists."""
    calls = []
    provider.queue_calls(('call-1', 'catalogue_search', {'query': 'CAT-0002'}))
    provider.queue_calls(('call-2', 'place_loan', {'recordId': 'CAT-0002', 'days': 14}))
    turn = lab.run_turn(provider, 'Borrow the knots handbook for two weeks.', tools=recording_tools(calls))
    assert lab.failure(turn) == 'ruleViolation' and turn.rules_violated == (lab.ids.seen_ids,)
    assert [name for name, _ in calls] == ['catalogue_search']


# [P2] The companion must not be distributed by Core as a standalone agent.
def test_prosaic_apply_distributes_only_the_agent_never_the_companion(lab, tmp_path):
    project = lab.copy_project(tmp_path)
    completed = subprocess.run(
        [str(Path(sys.executable).with_name('prosaic')), 'apply', '--dry-run', '--targets', 'claude-code'],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, 'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')},
    )
    assert completed.returncode == 0, completed.stderr
    assert 'catalogue-desk.md' in completed.stdout and 'loan-desk' not in completed.stdout


def test_companion_is_plain_rules_outside_the_core_source(lab):
    from lab_runner.rule_admission import BLUEPRINT

    companion = BLUEPRINT / lab.companion
    assert companion.is_file() and not companion.read_text().startswith('---')
    assert not (BLUEPRINT / '.prosaic' / 'subagents' / 'loan-desk.md').exists()


def test_compose_refuses_a_companion_written_as_an_agent(lab, tmp_path):
    from lab_runner.rule_admission.blueprint import host

    project = lab.copy_project(tmp_path)
    path = lab.path(project, lab.companion)
    path.write_text('---\nname: loan-desk\ntools: [place_loan]\n---\n' + path.read_text())
    with pytest.raises(ValueError, match='frontmatter'):
        host.compose(project)


# [P2] fix at a stage where the guard returns no repair must be refused before any request.
def test_fix_where_the_guard_cannot_repair_is_refused_before_any_request(lab, provider, tmp_path):
    from lab_runner.rule_admission.blueprint import coverage

    project = lab.copy_project(tmp_path, {lab.companion: [(COMPANION_TAG, COMPANION_TAG.replace('fail', 'fix'))]})
    with pytest.raises(ValueError, match='cannot repair at after_tool'):
        lab.run_turn(provider, lab.happy_message, project=project)
    assert provider.raw_requests == []
    report = coverage.report(project)
    assert (report['admitted'], report['refusal']) == (False, 'hostPolicy')
    completed = subprocess.run(
        [sys.executable, '-m', 'lab_runner.rule_admission.blueprint.coverage', '--project', str(project), '--json'],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 1 and json.loads(completed.stdout)['refusal'] == 'hostPolicy'


# [P2] Fee formats: assert what value_in_tool_output catches; strict xfail marks what it still misses.
RUNTIME_GAP = 'prosaic-runtime#16: value_in_tool_output reads only currency markers written before the number'


@pytest.mark.parametrize(
    'draft',
    [
        'EUR 1.20',
        '€1.20',
        '€1,20',
        'eur 1.20',
        pytest.param('1.20 EUR', marks=pytest.mark.xfail(strict=True, reason=RUNTIME_GAP)),
        pytest.param('1.20 euros', marks=pytest.mark.xfail(strict=True, reason=RUNTIME_GAP)),
        pytest.param('120 cents', marks=pytest.mark.xfail(strict=True, reason=RUNTIME_GAP)),
    ],
)
def test_an_invented_fee_is_retried_in_every_common_format(lab, provider, draft):
    provider.queue_calls(('call-1', 'loan_terms', {'recordId': 'CAT-0001'}))
    provider.queue_text(f'The late fee is {draft} per day.')
    provider.queue_text('The late fee is EUR 0.40 per day.')
    turn = lab.run_turn(provider, 'What is the late fee for CAT-0001?')
    assert turn.rules_violated == (lab.ids.values,) and len(provider.raw_requests) == 3


# [P3] An enormous integer period is repaired, never a guard fault.
@pytest.mark.parametrize('days', [10**400, 10**3000], ids=['401-digits', '3001-digits'])
def test_an_enormous_loan_period_is_repaired_not_faulted(lab, provider, days):
    calls = []
    provider.queue_calls(SEARCH)
    provider.queue_calls(('call-2', 'place_loan', {'recordId': 'CAT-0001', 'days': days}))
    provider.queue_text('Your loan is due back in 21 days.')
    turn = lab.run_turn(provider, 'Borrow the Atlas forever.', tools=recording_tools(calls))
    assert turn.rules_faulted == () and turn.result.exit_code == 0
    assert calls[-1] == ('place_loan', {'recordId': 'CAT-0001', 'days': 21})


# General point: the copyable blueprint itself refuses an SDK without rule admission, clearly.
def test_blueprint_refuses_a_core_without_parse_rules_on_import(tmp_path):
    shadow = tmp_path / 'shadow' / 'prosaic'
    shadow.mkdir(parents=True)
    (shadow / '__init__.py').write_text('')
    root = Path(__file__).resolve().parents[2]
    code = (
        'import sys; sys.path.insert(0, sys.argv[1]); sys.path.insert(1, sys.argv[2])\n'
        'import lab_runner.rule_admission.blueprint.host\n'
    )
    completed = subprocess.run(
        [sys.executable, '-I', '-c', code, str(shadow.parent), str(root)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode != 0
    assert 'parse_rules' in completed.stderr and 'rule_admission_v1' in completed.stderr
