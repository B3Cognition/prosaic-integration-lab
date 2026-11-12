"""Bind the approved graph lookup to a Prosaic conversation."""
from dataclasses import replace

import prosaic_harness as harness
import prosaic_runtime as runtime
from prosaic_runtime.mcp import McpClientV1, McpToolSpecV1

ARGUMENTS = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
    "additionalProperties": False,
}


def build_client(server, *, allow_destination, credentials, scope_key, authorize):
    return McpClientV1(server, allow_destination=allow_destination, credentials=credentials,
                       scope_key=scope_key, authorize=authorize)


def build_host(client, catalog, config, *, namespace, journal, evidence_authorizer,
               result_mode="structured", citations=None, tool_cap=4, projector=None,
               neighbors=None, parallel=None):
    def project(value, _context):
        return runtime.ToolResultV1(data=value)

    spec = McpToolSpecV1(
        alias="graph_lookup", remote_name="lookup", description="Read the graph entry for a service.",
        binding_version="1", result_mode=result_mode, projector=projector or project,
        result_contract=runtime.ToolResultContractV1("1"), read_only=True, argument_schema=ARGUMENTS,
    )
    tools = client.bind_tools(catalog, [spec], existing=neighbors)
    aliases = frozenset(tools)
    agent = runtime.ProsaicArtifact(
        "graph-review", "subagent", {"name": "graph-review", "description": "Read the graph.",
                                    "tools": sorted(aliases)},
        "Use the approved graph lookup to answer the question.",
    )
    return harness.ConversationBindings(
        agent, version="graph-1", config=replace(config, allowed_tools=aliases),
        policy=harness.ConversationPolicy(), custom_tools=tools, operation_namespace=namespace,
        tool_journal=journal,
        tool_contracts=harness.ToolContracts("graph-host", "1", evidence_authorizer=evidence_authorizer,
                                            citations=citations),
        run_policy=runtime.RunPolicy(allowed_tools=aliases, max_provider_requests=4,
                                     max_tool_calls=tool_cap, parallel_tools=parallel),
    )
