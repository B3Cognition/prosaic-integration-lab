"""Bind a synthetic receipt workflow and optionally describe its ontology."""

import argparse
from inspect import signature
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from prosaic import inspect_artifact
from prosaic_harness import Harness, Workflow, WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import CustomTool, EndpointConfig, ProsaicArtifact, RuntimeConfig
import yaml


class ExperimentalSDKUnavailable(RuntimeError):
    """The installed SDKs cannot bind and project the attachment."""


def _load_attachment(project: Path) -> dict:
    required = ("Catalogue ontology requires Core 0.5.1 and Harness 0.9.18 "
                "or published Core 0.5.1rc1 and Harness 0.9.17rc1 from dependencies/catalogue-ontology-rc.lock.")
    if ("ontology" not in signature(WorkflowCatalog).parameters
            or "include_ontology" not in signature(WorkflowFactory.describe).parameters):
        raise ExperimentalSDKUnavailable(required)
    try:
        from prosaic.ontology import load_ontology
    except ModuleNotFoundError as exc:
        if exc.name != "prosaic.ontology":
            raise
        raise ExperimentalSDKUnavailable(required) from None
    return load_ontology(project / "fixtures/attachment.json")


def _agent(project: Path, name: str) -> ProsaicArtifact:
    result = inspect_artifact(project, f"subagents/{name}.md")
    if not result["ok"]:
        raise ValueError(f"Could not inspect fixture agent {name}")
    return ProsaicArtifact.from_inspection(result["data"])


def _read_receipt(_arguments: dict) -> dict:
    return {"candidateId": "fixture-17", "receiptId": "receipt-17", "check": "passed"}


def _read_policy(_arguments: dict) -> dict:
    raise AssertionError("The restricted fixture tool must not run")


def build_factory(project: Path, *, attach_ontology: bool = False) -> WorkflowFactory:
    """Bind host-owned agents, schemas, and tool permissions."""
    catalogue_options = {"ontology": _load_attachment(project)} if attach_ontology else {}
    catalog = WorkflowCatalog(
        agents={name: _agent(project, name) for name in ("reviewer", "private-reviewer")},
        schemas={"receipt": json.loads((project / "receipt.schema.json").read_bytes())},
        **catalogue_options,
    )
    arguments = {"type": "object", "additionalProperties": False}
    bindings = WorkflowBindings(
        config=RuntimeConfig(
            profiles={"fixture": EndpointConfig("http://127.0.0.1:1/v1", "unused")},
            routes={}, default_profile="fixture", allowed_tools=frozenset({"read_receipt"}),
        ),
        custom_tools={
            "read_receipt": CustomTool("read_receipt", "Read a synthetic receipt.", arguments, _read_receipt, "1"),
            "read_policy": CustomTool("read_policy", "Read restricted policy.", arguments, _read_policy, "1"),
        },
    )
    policy = WorkflowPolicy(
        allowed_agents={"reviewer"}, allowed_schemas={"receipt"},
        allowed_tools={"read_receipt", "read_policy"}, allowed_direct_tools={"read_receipt"},
        max_calls=1, max_visits=2, timeout_s=5, max_run_s=15, max_tokens=4096,
        max_provider_requests_per_invocation=0, max_tool_calls_per_invocation=1,
    )
    return WorkflowFactory(catalog=catalog, bindings=bindings, policy=policy)


def build_workflow(project: Path, factory: WorkflowFactory) -> Workflow:
    """Admit the copied native graph using the host policy."""
    definition = yaml.safe_load((project / "workflow.yml").read_text(encoding="utf-8"))
    return factory.build(definition)


def run_demo(workflow: Workflow) -> dict:
    """Run the fixture in owned local storage and return a curated result."""
    with TemporaryDirectory(prefix="ontology-receipt-") as run_dir:
        state = Harness(workflow, run_dir=Path(run_dir).resolve()).run({})
        if state["status"] != "completed":
            raise RuntimeError("The synthetic receipt workflow did not complete")
        return {"status": "completed", "receipt": state["outputs"]["read"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("discover", "run"):
        command = commands.add_parser(name)
        command.add_argument("--ontology", action="store_true", help="Enable the catalogue attachment")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    try:
        factory = build_factory(project, attach_ontology=args.ontology)
    except ExperimentalSDKUnavailable as exc:
        parser.error(str(exc))
    if args.command == "discover":
        output = factory.describe(include_ontology=True) if args.ontology else factory.describe()
    else:
        output = run_demo(build_workflow(project, factory))
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
