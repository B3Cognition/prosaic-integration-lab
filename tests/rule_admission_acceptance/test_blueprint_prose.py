"""1. Tagged prose: four stages, a prose-only rule and a two-file per-(file, stage) composition."""

STAGES = {'before_tool', 'after_tool', 'before_answer', 'final'}


def test_agent_and_companion_tag_all_four_stages_and_one_prose_only_rule(lab):
    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import host

    artifact = host.compose(BLUEPRINT)
    assert list(artifact.rule_issues) == []
    by_id = {entry['id']: entry for entry in artifact.rules}
    assert set(by_id) == set(vars(lab.ids).values())
    assert {entry['stage'] for entry in artifact.rules if entry['kind'] == 'enforce'} == STAGES
    prose_only = by_id[lab.ids.prose_only]
    assert prose_only['kind'] == 'prose_only' and prose_only['guard'] is None
    assert prose_only['reason'] == 'tone is judged by people, not checks'


def test_one_guard_binds_once_per_file_at_a_different_stage_in_each(lab):
    from prosaic_runtime import compile_rules

    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import guards, host

    config = host.load_config()
    rules = compile_rules(
        list(host.compose(BLUEPRINT).rules), guards.registry(), required_guards=config.required_guards
    )
    loan = {(b.file, b.stage, b.action) for b in rules.bindings if b.guard_name == 'loan_period_within_policy'}
    assert loan == {(lab.agent, 'before_tool', 'fix'), (lab.companion, 'after_tool', 'fail')}


def test_core_refuses_the_same_guard_twice_in_one_file_which_is_why_the_companion_exists():
    from prosaic import parse_rules

    body = (
        '- Keep loans short. <!-- enforce: loan_period_within_policy(max_days=21, stage=before_tool) -->\n'
        '- Stop on long loans. <!-- enforce: loan_period_within_policy(max_days=21, stage=after_tool) -->\n'
    )
    assert [issue['code'] for issue in parse_rules(body, 'one.md')['issues']] == ['enforce-duplicate-guard']


def test_both_files_bindings_run_in_one_turn_and_the_model_sees_only_stripped_prose(lab, provider):
    from prosaic import inspect_artifact, strip_tags

    from lab_runner.rule_admission import BLUEPRINT

    lab.queue_happy(provider)
    turn = lab.run_turn(provider, lab.happy_message)
    assert turn.result.exit_code == 0 and turn.result.stdout == lab.happy_answer
    assert {lab.ids.loan_before, lab.ids.loan_after} <= set(turn.rules_evaluated)
    agent = inspect_artifact(BLUEPRINT, lab.agent)['data']['body']
    companion = lab.path(BLUEPRINT, lab.companion).read_text()
    expected = f'{strip_tags(agent)}\n\n## Bundled resource: {lab.companion}\n{strip_tags(companion)}'
    for request in provider.requests:
        assert request['messages'][0] == {'role': 'system', 'content': expected}
    wire = b''.join(provider.raw_requests).decode()
    assert 'enforce:' not in wire and 'prose-only' not in wire and 'max_days' not in wire


def test_blueprint_folder_ships_complete_with_the_lab():
    from lab_runner.rule_admission import BLUEPRINT

    expected = [
        'README.md',
        'runtime.yml',
        'guards.py',
        'host.py',
        'coverage.py',
        '.prosaic/subagents/catalogue-desk.md',
        'companions/loan-desk.md',
    ]
    assert all((BLUEPRINT / name).is_file() for name in expected)
    readme = (BLUEPRINT / 'README.md').read_text()
    for step in ('Rename the agent', 'Write prose rules', 'Tag them', 'Register guards', 'Set the floor'):
        assert step in readme
    assert 'prosaic-runtime#16' in readme
