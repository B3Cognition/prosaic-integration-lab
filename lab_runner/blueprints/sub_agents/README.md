# Dependency analyst and reviewer

Copy this directory and point `runtime.yml` at your approved model endpoint. Supply the host's trusted identity, captured Markdown, reviewed local lookup, current grants, and fenced tool journal. The launch grant authorizes a specialist call and its task. The live result grant authorizes the selected sources, including their status disclosures, before dispatch and on reuse.

The analyst receives its graph pack and `graph_lookup`. The reviewer receives its own checklist and a schema-checked draft. The coordinator writes the answer and can cite observations delivered by Runtime.

## Run the authored workflow

The `review_dependencies` node in [workflow.yml](workflow.yml) grants `analyze` and `review` through its `tools` list. The [coordinator Markdown](.prosaic/subagents/coordinator.md) declares the same aliases. The host registers those aliases, context packs, and access policy before Harness loads the workflow.

```python
from uuid import uuid4

from prosaic_harness import ContextScope, FileRunStore, Harness
from prosaic_runtime import ExecutionContext

from host import build_workflow

# These values come from the authenticated application request.
scope = ContextScope(namespace, environment, application, tenant, actor, billing_account)
context = ExecutionContext(application_id=application, tenant_id=tenant, actor_id=actor,
                           billing_account_id=billing_account)
workflow = build_workflow(
    scope, journal=journal, namespace=operation_namespace,
    documents={"analyze": captured_graph_markdown, "review": captured_review_checklist},
    lookup=lookup, authorize_pack=authorize_pack, authorize_launch=authorize_launch,
    authorize_result=authorize_result, authorize_evidence=authorize_evidence,
)
store = FileRunStore(owned_store_path, namespace=namespace)
store.initialize(sub_agents=True)
with store:
    result = Harness(workflow, store=store, run_id=uuid4().hex, context=context,
                     accounting=recorder).run({"question": "Does api depend on Kafka?"})
```

The application supplies the journal, recorder, and authorization callbacks. The lookup can return an `EvidenceDraftV1` with its typed result when a relationship can be cited. Harness validates the coordinator's result against [the output schema](schemas/dependency-review.json).

## Use the same specialists in a conversation

Use `build_host` with a trusted conversation scope and the same sources and grants. Provision the owned session store using `initialize(sub_agents=True)` and pass the returned bindings to Harness `Conversation` with the host-owned execution context and recorder. Set `reviewer=False` to enable the analyst alone.
