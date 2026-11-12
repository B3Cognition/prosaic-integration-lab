"""Bind a dependency analyst and an optional reviewer to an owned parent."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import prosaic_harness as h
import prosaic_runtime as rt

FINDING = {"type": "object", "properties": {"finding": {"type": "string", "maxLength": 1024}},
           "required": ["finding"], "additionalProperties": False}
DRAFT = {"type": "object", "properties": {"claim": {"type": "string", "maxLength": 1024}},
         "required": ["claim"], "additionalProperties": False}


def _specialist_bindings(scope, names, *, documents, lookup, authorize_pack,
                         authorize_launch, authorize_result, authorize_evidence, budget, read_only, specialist_tokens):
    read = rt.CustomTool("graph_lookup", "Read the reviewed dependency record.",
        {"type": "object", "additionalProperties": False}, lambda _: lookup(), "1",
        result_contract=rt.ToolResultContractV1("1"), terminal=not read_only)
    observed = rt.SubAgentReadV1(read, source_refs=lambda _: ["service-graph:1"])
    specs, sources, evidence, pack_names, agents = {}, {}, {}, {}, []
    for alias in names:
        tools = ["graph_lookup"] if alias == "analyze" else []
        task = ("Check the transitive dependency in the captured graph and use graph_lookup for evidence."
                if alias == "analyze" else "Check the draft for unsupported claims using the reviewer brief.")
        artifact = rt.ProsaicArtifact(alias, "subagent", {"tools": tools}, task + " Return a JSON finding.")
        agents.append(rt.SubAgentSpecV1(alias, task, artifact, "1",
            rt.RunPolicy(allowed_tools=frozenset(tools), max_provider_requests=2 if tools else 1,
                         max_tool_calls=len(tools), max_reported_tokens=specialist_tokens), FINDING,
            reads=(observed,) if tools else (), draft_schema=DRAFT if alias == "review" else None,
            select_observations=(lambda rows: [row["id"] for row in rows]) if tools else None))
        specs[alias] = h.ContextPackSpec(alias, "1", [h.ContextSlot(alias, required=True)])
        path = alias + ".md"
        sources[alias] = h.EvidenceSource(path)
        text = documents[alias]
        evidence[path] = {"text": text, "sha256": sha256(text.encode()).hexdigest()}
        pack_names[alias] = alias
    packs = h.ContextPackBindings(specs=specs, sources=sources, scope=h.ContextScope.from_dict(scope.to_dict()),
                                  authorizer=h.ContextAuthorizer("graph", "1", authorize_pack))
    delegates = h.SubAgentBindingsV1(specs=agents, policy=budget, pack_bindings=packs, pack_names=pack_names,
        revision="1", authorize_launch=authorize_launch, authorize_result=authorize_result,
        session_token_allowance=4 * budget.max_reported_tokens, evidence=evidence)
    contracts = h.ToolContracts("graph", "1",
        evidence_authorizer=rt.EvidenceAuthorizerV1("graph", "1", authorize_evidence),
        citations=rt.CitationPolicyV1("optional"))
    return delegates, contracts


def build_host(config, scope, *, journal, namespace, documents, lookup,
               authorize_pack, authorize_launch, authorize_result, authorize_evidence,
               reviewer=True, budget=None, read_only=True):
    """Bind a conversation using the application's trusted identity and grants."""
    names = ["analyze", "review"] if reviewer else ["analyze"]
    budget = budget or rt.SubAgentPolicyV1(2, 6, 4, 100)
    delegates, contracts = _specialist_bindings(scope, names, documents=documents, lookup=lookup,
        authorize_pack=authorize_pack, authorize_launch=authorize_launch, authorize_result=authorize_result,
        authorize_evidence=authorize_evidence, budget=budget, read_only=read_only, specialist_tokens=40)
    parent = rt.ProsaicArtifact("coordinator", "subagent",
        {"name": "coordinator", "description": "Answer a service dependency question", "tools": names},
        "Call the dependency analyst. Use the optional reviewer for draft claims. Own and cite the final answer.")
    config = replace(config, allowed_tools=frozenset(names))
    return h.ConversationBindings(parent, version="1", config=config, policy=h.ConversationPolicy(),
        run_policy=rt.RunPolicy(allowed_tools=frozenset(names), max_provider_requests=budget.max_provider_requests,
            max_tool_calls=budget.max_tool_calls, max_reported_tokens=budget.max_reported_tokens),
        tool_contracts=contracts, operation_namespace=namespace, tool_journal=journal, sub_agents=delegates)



def build_workflow(scope, *, journal, namespace, documents, lookup, authorize_pack,
                   authorize_launch, authorize_result, authorize_evidence, executable="prosaic"):
    """Load the copied YAML with both host-registered specialist aliases."""
    budget = rt.SubAgentPolicyV1(2, 6, 4, 16_384)
    delegates, contracts = _specialist_bindings(scope, ("analyze", "review"), documents=documents, lookup=lookup,
        authorize_pack=authorize_pack, authorize_launch=authorize_launch, authorize_result=authorize_result,
        authorize_evidence=authorize_evidence, budget=budget, read_only=True, specialist_tokens=4_096)
    return h.Workflow.load(Path(__file__).with_name("workflow.yml"), executable=executable,
        sub_agents=delegates, tool_contracts=contracts, operation_namespace=namespace, tool_journal=journal)
