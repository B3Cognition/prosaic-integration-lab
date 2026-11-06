"""Independent Runtime review cases against the exact installed Lab train."""
import pytest

from lab_runner.rule_admission.fixtures import scripted_provider
from .test_harness import open_host


@pytest.mark.parametrize('wire', ['openai-compatible', 'anthropic'])
@pytest.mark.parametrize('source,answer', [
    ({'amount': 'EUR 12abc'}, 'The amount is EUR 12.'),
    ({'ratio': 4.7}, 'Return -4.7x.'),
])
def test_malformed_sources_and_strict_sign_changes_fail_through_harness(lab, tmp_path, wire, source, answer):
    from prosaic_runtime import CustomTool
    from lab_runner.rule_admission.blueprint import host
    tools = host.library_tools()
    tools['loan_terms'] = CustomTool('loan_terms', 'Synthetic lookup', host.RECORD_SCHEMA,
        lambda args: source, 'review-v1')
    project = lab.copy_project(tmp_path, {lab.agent: [
        ('value_in_tool_output(stage=final, on_violation=retry)',
         'value_in_tool_output(stage=final, on_violation=fail)')]})
    with scripted_provider(wire) as provider:
        controller, store, scope = open_host(tmp_path, provider, wire, tools=tools, project=project)
        try:
            session = controller.create()
            provider.queue_calls(('one', 'loan_terms', {'recordId': 'CAT-0001'}))
            provider.queue_text(answer)
            reply = controller.send(session.session_id, message_id='one', message='Read the figure for CAT-0001.',
                expected_revision=session.revision).document
            assert reply['status'] == 'failed' and reply['failureCode'] == 'ruleViolation'
            assert 'answer' not in reply and len(provider.raw_requests) == 2
        finally:
            store.close()


@pytest.mark.parametrize('source', ['-12', 'EUR -12', '€-12'])
def test_explicit_magnitude_policy_retains_signed_source_support(source):
    from prosaic_runtime import GuardContext
    from prosaic_runtime.guards import value_in_tool_output
    context = GuardContext(stage='final', rule_id='a.md:1:check', rule_text='Synthetic rule.',
        source_file='a.md', settings={'sign': 'magnitude'}, paths={}, user_message='', input_data=None,
        tool_results=({'amount': source},), draft='The amount is EUR 12.')
    assert value_in_tool_output().check('final', context).ok
