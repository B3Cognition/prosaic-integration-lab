"""7. Byte-identical guarantee: the same agent with tags stripped runs identically without guards."""

import pytest


def happy(lab, provider, **options):
    lab.queue_happy(provider)
    return lab.run_turn(provider, lab.happy_message, **options)


def test_stripped_copy_is_cores_strip_tags_and_inspects_without_rules(lab, tmp_path):
    from prosaic import inspect_artifact, parse_rules

    project = lab.copy_project(tmp_path, strip=True)
    for name in (lab.agent, lab.companion):
        assert '<!--' not in lab.path(project, name).read_text()
    data = inspect_artifact(project, lab.agent)['data']
    assert 'rules' not in data and 'ruleIssues' not in data
    assert parse_rules(lab.path(project, lab.companion).read_text(), lab.companion) == {'rules': [], 'issues': []}


def test_stripped_agent_sends_identical_bytes_with_or_without_guards_registered(lab, tmp_path):
    from lab_runner.rule_admission.fixtures import scripted_provider

    project = lab.copy_project(tmp_path, strip=True)
    observed = []
    for guards in ((), None):
        with scripted_provider() as provider:
            turn = happy(lab, provider, project=project, guards=guards, required_guards=None)
            observed.append((list(provider.raw_requests), turn.result.exit_code, turn.result.stdout))
            assert turn.rules_evaluated == () and turn.rules_fingerprint is None
    assert observed[0] == observed[1]
    assert observed[0][1:] == (0, lab.happy_answer)


def test_tagged_agent_with_guards_sends_the_same_bytes_as_its_stripped_copy_without(lab, tmp_path):
    from lab_runner.rule_admission.fixtures import scripted_provider

    with scripted_provider() as provider:
        tagged = happy(lab, provider)
        tagged_requests = list(provider.raw_requests)
    with scripted_provider() as provider:
        stripped = happy(lab, provider, project=lab.copy_project(tmp_path, strip=True), guards=(), required_guards=None)
        stripped_requests = list(provider.raw_requests)
    assert tagged_requests == stripped_requests and len(tagged_requests) == 3
    assert (tagged.result.exit_code, tagged.result.stdout) == (stripped.result.exit_code, stripped.result.stdout)
    assert tagged.rules_fingerprint is not None and stripped.rules_fingerprint is None


def test_a_stripped_agent_cannot_slip_under_a_runtime_that_requires_guards(lab, provider, tmp_path):
    from prosaic_runtime import TurnAdmissionError

    with pytest.raises(TurnAdmissionError) as refused:
        happy(lab, provider, project=lab.copy_project(tmp_path, strip=True))
    assert refused.value.code == 'invalidPolicy' and provider.raw_requests == []
