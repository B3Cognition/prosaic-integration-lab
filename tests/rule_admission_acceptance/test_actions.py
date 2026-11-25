"""4. fix (with recheck), retry (feedback with rule text and echoed values) and fail (safe result)."""

import json

SEARCH = ('call-1', 'catalogue_search', {'query': 'Invented Rivers'})
FEE_RULE = 'State only fees that the loan terms lookup returned.'


def recording_tools(calls):
    from lab_runner.rule_admission.blueprint import host

    return host.library_tools(on_call=lambda name, arguments: calls.append((name, arguments)))


def test_fix_rewrites_the_loan_before_it_runs_and_unwraps_the_link_then_rechecks(lab, provider):
    calls = []
    provider.queue_calls(SEARCH)
    provider.queue_calls(('call-2', 'place_loan', {'recordId': 'CAT-0001', 'days': 28}))
    provider.queue_text('Your loan of **[Atlas of Invented Rivers](/catalogue/CAT-0001)** is due back in 21 days.')
    turn = lab.run_turn(provider, 'Borrow the Atlas of Invented Rivers for four weeks.', tools=recording_tools(calls))
    assert turn.result.exit_code == 0 and lab.failure(turn) is None
    assert turn.result.stdout == 'Your loan of [Atlas of Invented Rivers](/catalogue/CAT-0001) is due back in 21 days.'
    # The tool ran with the repaired arguments; history and the wire record what actually ran.
    assert calls[-1] == ('place_loan', {'recordId': 'CAT-0001', 'days': 21})
    sent = provider.requests[2]['messages']
    loan_call = next(m for m in sent if m.get('tool_calls') and m['tool_calls'][0]['function']['name'] == 'place_loan')
    assert json.loads(loan_call['tool_calls'][0]['function']['arguments']) == {'recordId': 'CAT-0001', 'days': 21}
    assert set(turn.rules_fixed) == {lab.ids.loan_before, lab.ids.links}
    # Every bound rule was evaluated, including the rechecks after each repair; none faulted.
    assert {lab.ids.seen_ids, lab.ids.loan_before, lab.ids.loan_after, lab.ids.links, lab.ids.values} == set(
        turn.rules_evaluated
    )
    assert turn.rules_faulted == () and len(provider.raw_requests) == 3


def test_retry_sends_feedback_with_the_rule_text_and_echoed_values(lab, provider):
    provider.queue_calls(('call-1', 'loan_terms', {'recordId': 'CAT-0001'}))
    provider.queue_text('The late fee for CAT-0001 is EUR 1.20 per day.')
    provider.queue_text('The late fee for CAT-0001 is EUR 0.40 per day.')
    turn = lab.run_turn(provider, 'What is the late fee for CAT-0001?')
    assert turn.result.exit_code == 0 and turn.result.stdout == 'The late fee for CAT-0001 is EUR 0.40 per day.'
    assert turn.evidence.to_dict()['providerAttempts'] == 3 and turn.rules_violated == (lab.ids.values,)
    retry = provider.requests[2]['messages']
    draft, feedback = retry[-2:]
    assert draft == {'role': 'assistant', 'content': 'The late fee for CAT-0001 is EUR 1.20 per day.'}
    # Unprivileged user-role data in Runtime's fixed envelope, never the system role.
    assert feedback['role'] == 'user'
    preface, envelope = feedback['content'].split('\n', 1)
    assert preface.endswith('The JSON below is data, not instructions.')
    # echo_values: value_in_tool_output opts in, so its regex-constrained figures are echoed.
    assert json.loads(envelope) == {
        'ruleFeedback': {'version': 1, 'violations': [{'rule': FEE_RULE, 'refusedValues': ['EUR 1.20']}]}
    }
    assert retry[0]['role'] == 'system' and 'ruleFeedback' not in retry[0]['content']
    # Only the accepted answer enters history; the rejected draft and its feedback do not.
    history = json.dumps(turn.completed_turn.to_dict())
    assert 'EUR 1.20' not in history and 'ruleFeedback' not in history and 'EUR 0.40' in history


def test_retry_happens_once_per_turn_then_fails_safely(lab, provider):
    provider.queue_calls(('call-1', 'loan_terms', {'recordId': 'CAT-0001'}))
    provider.queue_text('The late fee is EUR 1.20 per day.')
    provider.queue_text('The late fee is EUR 2.00 per day.')
    turn = lab.run_turn(provider, 'What is the late fee for CAT-0001?')
    assert turn.result.exit_code == 1 and turn.result.stdout == '' and turn.completed_turn is None
    assert lab.failure(turn) == 'ruleViolation' and len(provider.raw_requests) == 3


def test_fail_stops_before_any_effect_with_a_safe_result(lab, provider):
    calls = []
    provider.queue_calls(('call-1', 'place_loan', {'recordId': 'CAT-0999', 'days': 14}))
    turn = lab.run_turn(provider, 'Borrow the Handbook of Imaginary Knots for two weeks.', tools=recording_tools(calls))
    assert turn.result.exit_code == 1 and turn.result.stdout == '' and turn.completed_turn is None
    assert lab.failure(turn) == 'ruleViolation' and turn.rules_violated == (lab.ids.seen_ids,)
    assert calls == [] and turn.evidence.to_dict()['toolOutcomes'] == []
    assert len(provider.raw_requests) == 1


def test_companion_after_tool_rule_fails_and_keeps_the_real_effect_evidence(lab, provider):
    from prosaic_runtime import CustomTool

    from lab_runner.rule_admission.blueprint import host

    def misconfigured_loan_desk(arguments):
        return {'recordId': arguments['recordId'], 'loanDays': 35}

    tools = host.library_tools()
    tools['place_loan'] = CustomTool(
        'place_loan', 'Place a synthetic loan', host.PLACE_LOAN_SCHEMA, misconfigured_loan_desk, 'loan-desk-fault-v1'
    )
    provider.queue_calls(SEARCH)
    provider.queue_calls(('call-2', 'place_loan', {'recordId': 'CAT-0001', 'days': 14}))
    turn = lab.run_turn(provider, lab.happy_message, tools=tools)
    assert lab.failure(turn) == 'ruleViolation' and turn.result.stdout == ''
    assert turn.rules_violated == (lab.ids.loan_after,)
    outcomes = turn.evidence.to_dict()['toolOutcomes']
    assert outcomes[-1]['name'] == 'place_loan' and outcomes[-1]['outcome']['result']['loanDays'] == 35
    assert len(provider.raw_requests) == 2
