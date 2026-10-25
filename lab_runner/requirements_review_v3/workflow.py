"""Consumer-owned compact handoff using public Harness/Runtime contracts."""
from prosaic_harness import WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import ProsaicRuntime, RuntimeAdapter

from lab_runner.requirements_review_v2 import build_comparison_workflow as baseline
from lab_runner.requirements_review_v2 import project_stage_arguments as baseline_projection
from lab_runner.requirements_review_v1.contracts import LIMITS
from prosaic_integration_lab.sue_review.contracts import decode, encoded
from prosaic_integration_lab.sue_review.reporting import compact_advice

PROJECTION_VERSION='requirements-review-v3-compact-advice-1'


def project_stage_arguments(artifact, arguments, *, execute, **options):
    if artifact.id=='requirements-v1/final':
        data=decode(arguments,maximum=262144)
        data['request']['strategyAdvice']=compact_advice(data['request']['strategyAdvice'])
        arguments=encoded(data).decode()
    return baseline_projection(artifact,arguments,execute=execute,**options)


def build_comparison_workflow(config,strategy,limits=None):
    limits=dict(LIMITS if limits is None else limits)
    base=baseline(config,strategy,limits)
    roles=list(base.artifacts)
    policy=WorkflowPolicy(allowed_agents=roles,allowed_schemas=roles,allowed_tools=[],
        allow_agent_composition=len(roles)>1,max_calls=min(limits['calls'],len(roles)*2),
        max_attempts=2,max_visits=1,max_tokens=limits['tokens'],max_run_s=limits['elapsedSeconds'],
        timeout_s=min(60,limits['elapsedSeconds']),max_provider_requests_per_invocation=1,
        max_tool_calls_per_invocation=0,max_run_input_bytes=262144,max_invocation_bytes=262144,
        max_output_bytes=16384,max_state_bytes=4194304)
    adapter=RuntimeAdapter(ProsaicRuntime(config),PROJECTION_VERSION,project_stage_arguments,max_attempts=1)
    return WorkflowFactory(catalog=WorkflowCatalog(agents=base.artifacts,schemas=base.schemas),
        bindings=WorkflowBindings(config=config,runtime_adapter=adapter),policy=policy).build(
            {k:v for k,v in base.definition.items() if k!='limits'})
