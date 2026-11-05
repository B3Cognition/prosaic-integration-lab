"""Installed Harness enforces the blueprint before effects and persists rule receipts."""
from dataclasses import replace

import pytest

from lab_runner.rule_admission.fixtures import scripted_provider


def config(provider, wire):
    from lab_runner.rule_admission.blueprint import host
    cfg = host.load_config(base_url=provider.url)
    name = cfg.default_profile
    return replace(cfg, profiles={name: replace(cfg.profiles[name], provider=wire)})


def open_host(tmp_path, provider, wire, **options):
    from prosaic_harness import Conversation, ConversationScope, FileSessionStore
    from lab_runner.rule_admission.blueprint.harness import build_bindings
    scope = ConversationScope('rules', 'synthetic', 'catalogue', 'tenant', 'borrower')
    store = FileSessionStore(tmp_path / 'sessions', namespace=scope.namespace)
    store.initialize()
    bindings = build_bindings(config=config(provider, wire), **options)
    return Conversation(bindings, store=store, scope=scope), store, scope


def receipt(controller, store, scope, session):
    state = store.load_session(session.session_id, scope=scope).state
    aid = state['turns'][-1]['attempts'][-1]
    return store.load_receipt(session.session_id, aid, scope=scope)


@pytest.mark.parametrize('wire', ['openai-compatible', 'anthropic'])
def test_harness_repairs_before_tool_and_saves_rule_evidence(tmp_path, wire):
    from prosaic_harness import Conversation
    from lab_runner.rule_admission.blueprint import host
    calls = []
    with scripted_provider(wire) as provider:
        controller, store, scope = open_host(tmp_path, provider, wire,
            tools=host.library_tools(on_call=lambda name, args: calls.append((name, args))))
        try:
            session = controller.create()
            provider.queue_calls(('one', 'catalogue_search', {'query': 'Invented Rivers'}))
            provider.queue_calls(('two', 'place_loan', {'recordId': 'CAT-0001', 'days': 300}))
            provider.queue_text('Your loan is due back in 21 days.')
            args = dict(message_id='borrow', message='Borrow the Atlas for 300 days.', expected_revision=session.revision)
            reply = controller.send(session.session_id, **args).document
            assert reply['status'] == 'completed'
            assert ('place_loan', {'recordId': 'CAT-0001', 'days': 21}) in calls
            saved = receipt(controller, store, scope, session)
            assert saved['rules']['fixed'] == ['subagents/catalogue-desk.md:10:loan_period_within_policy']
            assert saved['rules']['fingerprint']
            # Reopen the actual on-disk store and replay with a fresh controller.
            store.close()
            from prosaic_harness import FileSessionStore
            store = FileSessionStore(tmp_path / 'sessions', namespace=scope.namespace)
            store.check_ready()
            fresh = Conversation(controller.bindings, store=store, scope=scope)
            assert fresh.send(session.session_id, **args).document == reply
            assert fresh.recover(session.session_id).document == reply
            assert len(provider.raw_requests) == 3 and len(calls) == 2
        finally:
            store.close()


@pytest.mark.parametrize('wire', ['openai-compatible', 'anthropic'])
def test_harness_retries_then_persists_failure_and_recovers_saved_receipt(tmp_path, wire):
    class Crash(BaseException): pass
    with scripted_provider(wire) as provider:
        controller, store, scope = open_host(tmp_path, provider, wire)
        try:
            session = controller.create()
            provider.queue_text('The late fee is EUR 999.')
            provider.queue_text('The late fee is EUR 999.')
            def crash(event):
                if event['event'] == 'receiptSaved': raise Crash()
            with pytest.raises(Crash):
                controller.send(session.session_id, message_id='fee', message='What is the fee?',
                    expected_revision=session.revision, on_event=crash)
            saved = receipt(controller, store, scope, session)
            assert saved['result']['failureCode'] == 'ruleViolation'
            assert saved['rules']['violated'] == ['subagents/catalogue-desk.md:12:value_in_tool_output']
            reply = controller.recover(session.session_id).document
            assert reply['status'] == 'failed' and reply['failureCode'] == 'ruleViolation'
            assert controller.recover(session.session_id).document == reply
            assert len(provider.raw_requests) == 2
        finally:
            store.close()


@pytest.mark.parametrize('wire', ['openai-compatible', 'anthropic'])
def test_harness_preserves_floor_and_composed_rules_before_any_request(lab, tmp_path, wire):
    from prosaic_harness import ConversationError
    from lab_runner.rule_admission.blueprint.harness import build_bindings
    with scripted_provider(wire) as provider:
        cfg = config(provider, wire)
        with pytest.raises((ValueError, ConversationError)):
            build_bindings(config=cfg, guards=())
        with pytest.raises((ValueError, ConversationError)):
            build_bindings(config=cfg, project=lab.copy_project(tmp_path, strip=True))
        assert provider.raw_requests == []


@pytest.mark.parametrize('wire', ['openai-compatible', 'anthropic'])
def test_harness_composed_after_tool_rule_is_enforced(tmp_path, wire):
    from prosaic_runtime import CustomTool
    from lab_runner.rule_admission.blueprint import host
    tools = host.library_tools()
    tools['place_loan'] = CustomTool('place_loan', 'Synthetic faulty desk', host.PLACE_LOAN_SCHEMA,
        lambda args: {'recordId': args['recordId'], 'loanDays': 300}, 'fault-v1')
    with scripted_provider(wire) as provider:
        controller, store, scope = open_host(tmp_path, provider, wire, tools=tools)
        try:
            session = controller.create()
            provider.queue_calls(('one', 'place_loan', {'recordId': 'CAT-0001', 'days': 14}))
            reply = controller.send(session.session_id, message_id='borrow', message='Borrow CAT-0001.',
                expected_revision=session.revision).document
            assert reply['failureCode'] == 'ruleViolation'
            saved = receipt(controller, store, scope, session)
            assert saved['rules']['violated'] == ['companions/loan-desk.md:3:loan_period_within_policy']
            assert saved['evidence']['toolOutcomes'][-1]['outcome']['result']['loanDays'] == 300
            assert len(provider.raw_requests) == 1
        finally:
            store.close()
