"""5. The rules fingerprint: from TurnResult; binding changes move it, prompt bytes do not."""

VALUES = 'value_in_tool_output(stage=final, on_violation=retry)'


def happy(lab, provider, **options):
    lab.queue_happy(provider)
    turn = lab.run_turn(provider, lab.happy_message, **options)
    assert turn.result.exit_code == 0 and turn.result.stdout == lab.happy_answer
    return turn


def test_turn_result_carries_the_fingerprint_of_the_compiled_bindings(lab, provider):
    from prosaic_runtime import compile_rules, rules_fingerprint

    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import guards, host

    turn = happy(lab, provider)
    compiled = compile_rules(
        list(host.compose(BLUEPRINT).rules), guards.registry(), required_guards=host.load_config().required_guards
    )
    assert turn.rules_fingerprint == compiled.rules_fingerprint() == rules_fingerprint(compiled.bindings)
    assert len(turn.rules_fingerprint) == 64


def test_changing_a_binding_action_changes_the_fingerprint_but_not_one_request_byte(lab, provider, tmp_path):
    from lab_runner.rule_admission.fixtures import scripted_provider

    original = happy(lab, provider)
    tightened = lab.copy_project(
        tmp_path, {lab.agent: [(VALUES, 'value_in_tool_output(stage=final, on_violation=fail)')]}
    )
    with scripted_provider() as other:
        changed = happy(lab, other, project=tightened)
        other_requests = list(other.raw_requests)
    assert changed.rules_fingerprint != original.rules_fingerprint
    assert other_requests == provider.raw_requests


def test_a_line_added_above_the_rules_changes_their_ids_but_not_the_fingerprint(lab, provider, tmp_path):
    from lab_runner.rule_admission.fixtures import scripted_provider

    original = happy(lab, provider)
    anchor = '- Search the catalogue before answering any question about a book.'
    edited = lab.copy_project(
        tmp_path, {lab.agent: [(anchor, anchor + '\n- Greet the borrower by the name they give.')]}
    )
    with scripted_provider() as other:
        moved = happy(lab, other, project=edited)
    assert moved.rules_fingerprint == original.rules_fingerprint
    assert set(moved.rules_evaluated) != set(original.rules_evaluated)


def test_a_new_guard_version_changes_the_fingerprint(lab, provider):
    from prosaic_runtime import Guard, generic_guards

    from lab_runner.rule_admission.blueprint import guards
    from lab_runner.rule_admission.fixtures import scripted_provider

    original = happy(lab, provider)
    current = guards.LOAN_PERIOD
    upgraded = Guard(
        current.name,
        'loan-period-v2',
        current.stages,
        current.check,
        fixes=current.fixes,
        settings_schema=current.settings_schema,
    )
    with scripted_provider() as other:
        bumped = happy(lab, other, guards=[*generic_guards(), upgraded])
    assert bumped.rules_fingerprint != original.rules_fingerprint
