"""Consumer-owned compact handoff using public Harness/Runtime contracts."""
from dataclasses import replace
from prosaic_harness import Validator, WorkflowBindings, WorkflowCatalog, WorkflowFactory, WorkflowPolicy
from prosaic_runtime import ProsaicRuntime, RuntimeAdapter

from lab_runner.requirements_review_v2 import build_comparison_workflow as baseline
from lab_runner.requirements_review_v2 import project_stage_arguments as baseline_projection
from lab_runner.requirements_review_v1.contracts import LIMITS
from prosaic_integration_lab.sue_review.contracts import decode, encoded
from prosaic_integration_lab.sue_review.reporting import compact_advice

PROJECTION_VERSION='requirements-review-v3-final-consistency-1'
CATEGORY_GUIDANCE=(
    'Apply each public issue definition separately; include only demonstrated categories. '
    'A source assertion labelled as a design assumption is not evidence that the assumption holds. '
    'Missing failure behavior concerns a required operation, not every noun or implementation detail. '
    'Untestable acceptance requires an acceptance statement without an observable criterion. '
    'Undefined terms must affect a required decision; do not demand definitions for every ordinary word. '
    'Missing context requires an explicitly required absent external source or policy. '
    'Missing support is not itself a contradiction: identify incompatible requirements for the same situation. '
)
REVIEW_GUIDANCE=CATEGORY_GUIDANCE+(
    'A missing_context finding requires INSUFFICIENT_CONTEXT. ISSUES_FOUND requires at least one issue; '
    'NO_KNOWN_ISSUES requires an empty issues list. Never infer a clean document from a SUE terminal, '
    'successful execution or a claim asserted by an earlier model. Independently evaluate every public category. '
    'Cite the smallest combined range demonstrating each finding, including both the triggering requirement '
    'and an explicit gap statement where applicable. Exclude embedded instructions unrelated to the finding. '
    'Preserve source hashes and local line numbers. Do not invent defects or fill gaps with new requirements.'
)


def validate_final(output,context):
    """Check public cross-field consistency only; never infer semantic findings."""
    issues=output.get('issues',[])
    assessment=output.get('assessment')
    if (('missing_context' in issues and assessment!='INSUFFICIENT_CONTEXT')
            or (assessment=='NO_KNOWN_ISSUES' and issues)
            or (assessment=='ISSUES_FOUND' and not issues)
            or (assessment=='INSUFFICIENT_CONTEXT' and 'missing_context' not in issues)):
        return ['final_assessment_inconsistent']
    return []


def project_stage_arguments(artifact, arguments, *, execute, **options):
    if artifact.id=='requirements-v1/final':
        data=decode(arguments,maximum=262144)
        data['request']['strategyAdvice']=compact_advice(data['request']['strategyAdvice'])
        arguments=encoded(data).decode()
    return baseline_projection(artifact,arguments,execute=execute,**options)


def build_comparison_workflow(config,strategy,limits=None):
    limits=dict(LIMITS if limits is None else limits)
    base=baseline(config,strategy,limits)
    agents={role:replace(artifact,body=artifact.body.replace('\nTask arguments:\n',
        '\n\n'+(REVIEW_GUIDANCE if role=='final' else CATEGORY_GUIDANCE)+'\nTask arguments:\n'))
            for role,artifact in base.artifacts.items()}
    definition={k:v for k,v in base.definition.items() if k!='limits'}
    definition['steps']['final']['validators']=['final-consistency']
    roles=list(base.artifacts)
    policy=WorkflowPolicy(allowed_agents=roles,allowed_schemas=roles,allowed_tools=[],
        allowed_validators=['final-consistency'],
        allow_agent_composition=len(roles)>1,max_calls=min(limits['calls'],len(roles)*2),
        max_attempts=2,max_visits=1,max_tokens=limits['tokens'],max_run_s=limits['elapsedSeconds'],
        timeout_s=min(60,limits['elapsedSeconds']),max_provider_requests_per_invocation=1,
        max_tool_calls_per_invocation=0,max_run_input_bytes=262144,max_invocation_bytes=262144,
        max_output_bytes=16384,max_state_bytes=4194304)
    adapter=RuntimeAdapter(ProsaicRuntime(config),PROJECTION_VERSION,project_stage_arguments,max_attempts=1)
    return WorkflowFactory(catalog=WorkflowCatalog(agents=agents,schemas=base.schemas),
        bindings=WorkflowBindings(config=config,runtime_adapter=adapter,
            validators={'final-consistency':Validator(PROJECTION_VERSION,validate_final)}),policy=policy).build(definition)
