"""Credential-free installed SDK delegation witnesses."""
from importlib.metadata import version
import json
from pathlib import Path
import re
from uuid import uuid4

CASES = ("chat", "workflow", "siblings", "scope-and-citations", "unauthorized",
         "write-refusal", "budget-exhaustion", "cancellation", "revoked-replay",
         "uncertain-child", "interrupted-parent", "receipt-adoption")

TRAIN = {"b3-prosaic": "0.5.0", "b3-prosaic-runtime": "0.9.23.dev1",
         "b3-prosaic-runtime-postgres": "0.3.0", "b3-prosaic-harness": "0.9.17.dev1",
         "b3-prosaic-harness-postgres": "0.4.5.dev1"}


def require_sub_agent_sdk():
    import prosaic_runtime as rt
    import prosaic_harness as h
    import prosaic_harness_postgres as pg

    if {name: version(name) for name in TRAIN} != TRAIN:
        raise ValueError("exact sub-agent SDK candidate family required")
    if ("sub_agents_v1" not in rt.ProsaicRuntime.capabilities
            or not hasattr(h, "SubAgentBindingsV1") or not hasattr(pg.PostgresSessionStore, "migrate_sub_agent_storage")
            or any("site-packages" not in Path(module.__file__).parts for module in (rt, h, pg))):
        raise ValueError("installed delegation capability required")


def calls(alias, arguments=None):
    return {"calls": [{"id": alias, "name": alias, "input": arguments or {}}]}


def run_case(case, provider, *, journal, store, recorder, run_store=None, build_host=None):
    import prosaic_harness as h
    import prosaic_runtime as rt
    from lab_runner.blueprints.sub_agents.host import build_host as blueprint
    from lab_runner.parallel_tools import endpoint

    if case not in CASES:
        raise ValueError("unknown delegation case")
    build_host = build_host or blueprint
    delegate_claims, delegate_commits = [], []
    backend = journal

    class ObservedJournal:
        contract_version = backend.contract_version
        identity = backend.identity

        def claim(self, *args):
            nonlocal permitted
            claim = backend.claim(*args)
            delegate_claims.append(claim.state)
            if case == "revoked-replay" and claim.state == "replay":
                permitted = False
            return claim

        def commit(self, *args):
            backend.commit(*args)
            delegate_commits.append(True)

    journal = ObservedJournal()
    namespace = "delegation-" + uuid4().hex
    scope = h.ConversationScope(store.namespace, "sandbox", "graph", "tenant", "actor", "payer")
    context = rt.ExecutionContext(application_id="graph", tenant_id="tenant", actor_id="actor",
                                  billing_account_id="payer")
    permitted = True
    cancelled = False
    reads = []

    def lookup():
        nonlocal cancelled
        reads.append("graph")
        if case == "cancellation":
            cancelled = True
        return rt.ToolResultV1(data={"relationship": "api → worker → kafka"}, evidence=(
            rt.EvidenceDraftV1("service-graph", "1", "internal-locator", "/relationship", "Transitive dependency"),))

    with endpoint(provider) as (url, wire, replies):
        config = rt.RuntimeConfig({"fixture": rt.EndpointConfig(url, "synthetic", provider=provider,
            features={"streaming": False})}, {}, "fixture")
        if case == "write-refusal":
            try:
                build_host(config, scope, journal=journal, namespace=namespace,
                    documents={}, lookup=lookup, authorize_pack=lambda _: True, authorize_launch=lambda *_: True,
                    authorize_result=lambda *_: True, authorize_evidence=lambda _: True, read_only=False)
            except ValueError:
                assert not wire and not reads
            else:
                raise AssertionError("write-capable child tool admitted")
            child = rt.ProsaicArtifact("child", "subagent", {"tools": []}, "Return a JSON finding.")
            specialist = rt.SubAgentSpecV1("nested", "Nested specialist", child, "1",
                rt.RunPolicy(max_provider_requests=1, max_tool_calls=0, max_reported_tokens=10),
                {"type": "object", "additionalProperties": False})
            try:
                rt.SubAgentReadV1(rt.bind_sub_agent_tools((specialist,))["nested"], public=True)
            except ValueError:
                return
            raise AssertionError("nested specialist admitted as a read")
        binding = build_host(config, scope, journal=journal, namespace=namespace,
            documents={"analyze": "Analyst pack contains the graph", "review": "Reviewer pack rejects unsupported claims"},
            lookup=lookup, authorize_pack=lambda _: True, authorize_launch=lambda *_: case != "unauthorized",
            authorize_result=lambda *_: permitted, authorize_evidence=lambda _: True,
            budget=rt.SubAgentPolicyV1(2, 2, 2, 100) if case == "budget-exhaustion" else None)
        chat = h.Conversation(binding, store=store, scope=scope, context=context, accounting=recorder)
        launch = calls("analyze", {"task": "Check dependencies"})
        answer = "Kafka is a transitive dependency."
        expected_requests = 3
        replies[:] = [launch, '{"finding":"Kafka supported"}', answer]
        if case in {"unauthorized", "budget-exhaustion"}:
            replies[:] = [launch, "Specialist unavailable"]
            expected_requests = 2
        elif case == "siblings":
            replies[:] = [launch, '{"finding":"Kafka supported"}',
                calls("review", {"task": "Review claim", "draft": {"claim": "Redis is a dependency"}}),
                '{"finding":"Redis unsupported"}', answer]
            expected_requests = 5
        elif case in {"scope-and-citations", "cancellation"}:
            def cited(payload):
                text = json.dumps(payload)
                assert "internal-locator" not in text
                found = re.findall(r"ev_[0-9a-f]{64}", text)
                assert len(set(found)) == 1
                assert found[0] not in json.dumps(wire[2])
                return answer + " [cite:" + found[0] + "]"
            replies[:] = [launch, calls("graph_lookup"), '{"finding":"Kafka supported"}', cited]
            expected_requests = 2 if case == "cancellation" else 4
        elif case == "uncertain-child":
            replies[:] = [launch]
            expected_requests = 2
        elif case == "workflow":
            assert run_store is not None
            policy = h.WorkflowPolicy(allowed_agents={"coordinator"}, allowed_schemas={"answer"},
                allowed_tools=set(binding.agent.frontmatter["tools"]), max_provider_requests_per_invocation=6,
                max_tool_calls_per_invocation=4, max_tokens=400)
            factory = h.WorkflowFactory(catalog=h.WorkflowCatalog(agents={"coordinator": binding.agent},
                schemas={"answer": {"type": "object"}}), bindings=h.WorkflowBindings(
                    config=binding.config, tool_contracts=binding.tool_contracts, sub_agents=binding.sub_agents,
                    operation_namespace=namespace, tool_journal=journal), policy=policy)
            workflow = factory.build({"version": 1, "start": "graph", "steps": {
                "graph": {"kind": "agent", "agent": "coordinator", "schema": "answer",
                          "tools": binding.agent.frontmatter["tools"], "next": "done"},
                "done": {"kind": "finish"}}})
            replies[-1] = '{"supported":true}'
            state = h.Harness(workflow, store=run_store, run_id=uuid4().hex,
                              context=context, accounting=recorder).run({})
            assert state["status"] == "completed" and state["invocations"][0]["token_usage"] == 15
            assert len(wire) == 3 and not reads
            assert_recorder(recorder, 3, 1)
            return

        if case == "revoked-replay":
            operation = rt.InvocationScope(uuid4().hex, operation_namespace=namespace)
            frame = binding.sub_agents.frame(binding.agent, operation)
            runner = binding.runtime()
            options = dict(message="Check", policy=binding.run_policy, tool_journal=journal,
                tool_contract_bindings=binding.tool_contracts.bind(operation), sub_agent_frame=frame,
                sub_agent_access=binding.sub_agents.access(lambda: True),
                context=rt.ExecutionContext(application_id="graph", tenant_id="tenant", actor_id="actor",
                    billing_account_id="payer", invocation_id=operation.invocation_id), accounting=recorder)
            assert runner.turn(binding.agent, **options).result.exit_code == 0
            replies[:] = [launch, "Unavailable"]
            assert runner.turn(binding.agent, **options).result.stdout == "Unavailable"
            assert delegate_claims == ["new", "replay"] and delegate_commits == [True]
            assert "Kafka supported" not in json.dumps(wire[-1])
            assert len(wire) == 5 and not reads
            assert_recorder(recorder, 5, 1)
            return

        session = chat.create()
        events = []

        def event(data):
            events.append(data)
            if case == "receipt-adoption" and data["event"] == "receiptSaved":
                raise OSError("acknowledgment lost")

        def send(target=chat):
            return target.send(session.session_id, message_id="one", message="Parent-only question",
                expected_revision=session.revision, on_event=event, cancelled=lambda: cancelled)

        if case == "receipt-adoption":
            try:
                send()
            except OSError:
                pass
            else:
                raise AssertionError("receipt acknowledgment fault did not fire")
            assert chat.recover(session.session_id).document["answer"] == answer
        elif case == "interrupted-parent":
            class FailReceipt:
                def __getattr__(self, name):
                    return getattr(store, name)

                def save_receipt(self, *_args, **_kwargs):
                    raise OSError("parent receipt unavailable")

            interrupted = h.Conversation(binding, store=FailReceipt(), scope=scope,
                                          context=context, accounting=recorder)
            try:
                send(interrupted)
            except OSError:
                pass
            else:
                raise AssertionError("parent receipt fault did not fire")
            assert chat.recover(session.session_id).document["status"] == "needsResolution"
            assert delegate_claims == ["new"] and delegate_commits == [True]
        else:
            reply = send()
            if case in {"cancellation", "uncertain-child"}:
                assert reply.document["status"] != "completed"
            elif case in {"unauthorized", "budget-exhaustion"}:
                assert reply.document["answer"] == "Specialist unavailable"
                if case == "unauthorized":
                    replies[:] = [calls("forged_delegate", {"task": "Check"})]
                    forged = chat.send(session.session_id, message_id="forged", message="Try a foreign alias",
                        expected_revision=reply.document["revision"])
                    assert forged.document["failureCode"] == "invalidToolRequest"
                    expected_requests += 1
            else:
                assert reply.document["status"] == "completed"
                if case == "scope-and-citations":
                    citation = re.search(r"ev_[0-9a-f]{64}", reply.document["answer"])[0]
                    state = store.load_session(session.session_id, scope=scope).state
                    aid = state["turns"][0]["attempts"][0]
                    assert chat.citation_view(session.session_id, aid, citation)["available"]
                    permitted = False
                    try:
                        assert not chat.citation_view(session.session_id, aid, citation)["available"]
                    except h.ConversationError as exc:
                        assert exc.code == "evidenceUseDenied"
        if case == "uncertain-child":
            assert delegate_claims == ["new"] and not delegate_commits
        if case in {"unauthorized", "budget-exhaustion"}:
            assert not delegate_claims
        assert len(wire) == expected_requests
        if case not in {"unauthorized", "budget-exhaustion"}:
            assert "Analyst pack contains the graph" in json.dumps(wire[1])
            assert "Parent-only question" not in json.dumps(wire[1])
            assert "Reviewer pack" not in json.dumps(wire[1])
            assert "sourceLocator" not in json.dumps(wire[1])
            assert "sourceIdentity" not in json.dumps(wire[1])
        if case == "siblings":
            assert "Reviewer pack" in json.dumps(wire[3]) and "Analyst pack" not in json.dumps(wire[3])
            assert "Redis unsupported" in json.dumps(wire[4])
        assert len(reads) == int(case in {"cancellation", "scope-and-citations"})
        assert "graph_lookup" not in json.dumps(events)
        assert_recorder(recorder, expected_requests, 0 if case in {"unauthorized", "budget-exhaustion"}
                        else 2 if case in {"siblings", "scope-and-citations"} else 1)


def assert_recorder(recorder, requests, child_requests):
    calls = recorder.calls() if callable(getattr(recorder, "calls", None)) else recorder.intents.values()
    calls = [row.get("intent", row) for row in calls]
    assert len(calls) == requests
    contexts = [row["context"] for row in calls]
    root_ids = {row["invocation_id"] for row in contexts if not row["invocation_id"].startswith("child-")}
    children = [row for row in contexts if row["invocation_id"].startswith("child-")]
    assert len(children) == child_requests
    assert all(child["parent_invocation_id"] in root_ids for child in children)
    assert all(row["context"]["billing_account_id"] == "payer" for row in calls)
