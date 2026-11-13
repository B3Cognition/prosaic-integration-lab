"""Acceptance cases for the paired Runtime and Harness MCP candidate."""
from contextlib import ExitStack
import json
import re
from uuid import uuid4

from lab_runner.gates import MCP_CASES as CASES, MCP_CLIENT_RELEASE_TRAIN, MCP_CLIENT_TRAIN as TRAIN

MCP_LOCKED_VERSIONS = {
    "httpcore2": "2.16.0", "httpx2": "2.16.0", "mcp": "2.3.0", "mcp-types": "2.3.0",
    "python-multipart": "0.0.33", "sse-starlette": "3.7.0", "truststore": "0.10.5",
}


def require_mcp_client_sdk():
    from importlib.metadata import version
    from pathlib import Path
    import prosaic_runtime as rt
    import prosaic_harness as harness
    from prosaic_runtime.mcp import require_mcp_sdk

    from .sub_agents import RELEASE_TRAIN as DELEGATION_RELEASE_TRAIN, TRAIN as DELEGATION_TRAIN
    installed = {name: version(name) for name in TRAIN}
    from .catalogue_ontology import TRAIN as ONTOLOGY_TRAIN

    if installed not in (TRAIN, MCP_CLIENT_RELEASE_TRAIN, DELEGATION_TRAIN, DELEGATION_RELEASE_TRAIN,
                         ONTOLOGY_TRAIN) or any(
            version(name) != expected for name, expected in MCP_LOCKED_VERSIONS.items()):
        raise ValueError("exact MCP SDK family required")
    if "mcp_client_v1" not in rt.ProsaicRuntime.capabilities:
        raise ValueError("MCP Runtime capability missing")
    if any("site-packages" not in Path(module.__file__).parts for module in (rt, harness)):
        raise ValueError("installed MCP SDKs required")
    require_mcp_sdk()


def _batch(*aliases):
    return {"calls": [{"id": f"call{index}", "name": alias, "input": {"name": "service"}}
                      for index, alias in enumerate(aliases or ("graph_lookup",))]}


def _cited_answer(payload):
    evidence_id = re.search(r"ev_[0-9a-f]{64}", json.dumps(payload))
    assert evidence_id
    return f'14 dependents [cite:{evidence_id[0]}]'


def run_case(case, provider, *, journal, store=None, build_host=None):
    import prosaic_harness as h
    import prosaic_runtime as rt
    from prosaic_runtime.mcp import McpServerV1
    from lab_runner.mcp_fixture import LEGACY, MODERN, fault_endpoint, sdk_endpoint
    from lab_runner.parallel_tools import endpoint
    from lab_runner.blueprints.mcp_client import host

    if case not in CASES:
        raise ValueError("unknown MCP acceptance case")
    build_host = host.build_host if build_host is None else build_host
    grant, evidence, order = [True], [True], []
    namespace = "mcp-" + uuid4().hex
    real = case in {"approved-structured", "approved-text", "legacy-negotiation"}
    citations = case == "citation-retained-read"
    server_endpoint = (sdk_endpoint(text=case == "approved-text") if real
                       else fault_endpoint(case, grant))
    with ExitStack() as remote, endpoint(provider) as (model_url, model_requests, replies):
        url, methods, effects = remote.enter_context(server_endpoint)
        server = McpServerV1("lab-graph", "1", url,
                             LEGACY if case == "legacy-negotiation" else MODERN,
                             auth_mode="none", allow_loopback_http=True)
        client = host.build_client(server, allow_destination=lambda endpoint: endpoint == url,
                                   credentials=lambda *_: None, scope_key=lambda _: "scope",
                                   authorize=lambda *_: grant[0] and case != "scope-denial")
        remote.enter_context(client)
        catalog = client.discover(access_scope="scope")

        def project(value, _context):
            order.append("remote")
            if not citations:
                return rt.ToolResultV1(data=value)
            return rt.ToolResultV1(data=value, evidence=(
                rt.EvidenceDraftV1("graph", "1", "fixture:service", "/count", "Dependents"),))

        def local(arguments, context):
            order.append(context.call_index)
            return arguments

        parallel = case == "parallel-barrier"
        options = dict(namespace=namespace, journal=journal, projector=project,
                       result_mode="text" if case == "approved-text" else "structured",
                       tool_cap=0 if case == "budget-exhaustion" else 4,
                       evidence_authorizer=rt.EvidenceAuthorizerV1("graph", "1", lambda _: evidence[0]),
                       citations=rt.CitationPolicyV1("required") if citations else None)
        if parallel:
            options.update(neighbors={"local_read": rt.CustomTool(
                "local_read", "Read locally.", host.ARGUMENTS, local, "1", with_context=True,
                parallel_read=True)}, parallel=rt.ParallelToolPolicyV1(max_concurrency=2))
        config = rt.RuntimeConfig({"fixture": rt.EndpointConfig(model_url, "synthetic", provider=provider,
                                                                 features={"streaming": False})}, {}, "fixture")
        binding = build_host(client, catalog, config, **options)
        replies.extend([_batch("local_read", "graph_lookup", "local_read") if parallel else _batch(),
                        _cited_answer if citations else "done"])
        if case in {"receipt-adoption", "citation-retained-read"}:
            if store is None:
                raise ValueError("owned session store required")
            scope = h.ConversationScope(store.namespace, "synthetic", "graph", "tenant", "actor")
            chat = h.Conversation(binding, store=store, scope=scope)
            session = chat.create()
            def send(**kwargs):
                return chat.send(session.session_id, message_id="question", message="Review",
                                 expected_revision=session.revision, **kwargs)

            if case == "receipt-adoption":
                class AfterReceipt(OSError):
                    pass

                def lose_owner(event):
                    if event["event"] == "receiptSaved":
                        raise AfterReceipt("durable receipt saved")

                try:
                    send(on_event=lose_owner)
                except AfterReceipt:
                    pass
                else:
                    raise AssertionError("receipt adoption fault did not fire")
                reply = None
            else:
                reply = send()
                assert reply.document["status"] == "completed", reply.document
            snapshot = store.load_session(session.session_id, scope=scope)
            attempt = snapshot.state["turns"][0]["attempts"][-1]
            receipt = store.load_receipt(session.session_id, attempt, scope=scope)
            assert receipt["version"] == 4
            if case == "receipt-adoption":
                assert snapshot.state["pending"]["invocationId"] == attempt
                assert snapshot.state["attempts"][attempt]["receiptAdopted"] is False
            frozen = catalog.to_dict()
            remote.close()
            restored = client.restore_catalog(frozen, access_scope="scope", expected_sha256=catalog.sha256)
            fresh = h.Conversation(build_host(client, restored, config, **options), store=store, scope=scope)
            if case == "receipt-adoption":
                recovered = fresh.recover(session.session_id)
                assert recovered.document["status"] == "completed", recovered.document
                assert recovered.document["answer"] == "done"
            else:
                assert fresh.status(session.session_id).document == reply.document
            if citations:
                citation_id = re.search(r"ev_[0-9a-f]{64}", reply.document["answer"])[0]
                assert fresh.citation_view(session.session_id, attempt, citation_id)["available"] is True
                evidence[0] = False
                assert fresh.citation_view(session.session_id, attempt, citation_id)["available"] is False
            assert len(model_requests) == 2
        else:
            runtime = binding.runtime()
            scope = rt.InvocationScope("question", operation_namespace=namespace)
            call = dict(message="Review", policy=binding.run_policy, tool_journal=journal,
                        tool_contract_bindings=binding.tool_contracts.bind(scope))
            result = runtime.turn(binding.agent, **call)
            if case in {"budget-exhaustion", "uncertain-dispatch"}:
                assert result.result.exit_code != 0, result.result
            else:
                assert result.result.exit_code == 0, result.result
            if case in {"uncertain-dispatch", "completed-replay"}:
                replies[:] = [_batch(), "done"]
                replay = runtime.turn(binding.agent, **call)
                assert (replay.result.exit_code == 0) == (case == "completed-replay")
            if parallel:
                assert order == [0, "remote", 2]
            if case == "approved-text":
                assert "14 dependents" in json.dumps(model_requests[-1])
            if case == "approved-structured":
                assert "count" in json.dumps(model_requests[-1])
        no_post = case in {"scope-denial", "revocation-during-listing", "catalogue-drift", "budget-exhaustion"}
        expected_lists = 1 if case in {"scope-denial", "budget-exhaustion"} else 2
        assert methods.count("tools/call") == len(effects) == int(not no_post), methods
        assert methods.count("tools/list") == expected_lists, methods
        if case == "legacy-negotiation":
            assert methods.count("initialize") == expected_lists, methods
        return {"case": case, "provider": provider, "passed": True,
                "providerRequests": len(model_requests), "toolPosts": len(effects)}
