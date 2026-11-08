"""Public installed SDK example; printing/copying makes no provider call."""
from dataclasses import replace
from pathlib import Path
from copy import deepcopy
from prosaic import inspect_artifact
from prosaic_runtime import ProsaicArtifact,ProsaicRuntime,RuntimeConfig,RunPolicy
from prosaic_harness import WorkflowFactory,WorkflowCatalog,WorkflowBindings,WorkflowPolicy

PROJECT=Path(__file__).resolve().parent
KEY='reasoning_effort_v1'


def load_agent(project=PROJECT):
    value=inspect_artifact(Path(project),'subagents/review.md')
    if not value.get('ok'):raise ValueError('cannot inspect review agent')
    return ProsaicArtifact.from_inspection(value['data'])


def build_runtime(*,project=PROJECT,base_url=None,provider=None,model=None,
                  accounting=None,custom_tools=None,guards=None,streaming=None):
    project=Path(project);config=RuntimeConfig.load(project/'runtime.yml');name=config.default_profile
    endpoint=config.profiles[name];changes={};features=dict(endpoint.features)
    if base_url is not None:changes['base_url']=base_url
    if model is not None:changes['model']=model
    if provider is not None:changes['provider']=provider
    if streaming is not None:features['streaming']=streaming
    if changes.get('provider',endpoint.provider)=='anthropic':
        features['reasoning_effort']=None
        changes['supported_efforts']=None
    tools=custom_tools or {}
    endpoint=replace(endpoint,features=features,**changes)
    config=replace(config,profiles={**config.profiles,name:endpoint},allowed_tools=frozenset(tools))
    runtime=ProsaicRuntime(config,source=project/'.prosaic',accounting=accounting,custom_tools=tools,guards=guards)
    if KEY not in runtime.capabilities:raise ValueError('Runtime reasoning_effort_v1 is required')
    return runtime


def effort_report(result):
    """Trusted operator diagnostic, never a public application/authorization view."""
    trace=result.metadata.get(KEY)
    return {'available':trace is not None,'trace':deepcopy(trace)}


def run_review(runtime,agent,*,context=None):
    return runtime.run(agent,context=context,policy=RunPolicy(max_provider_requests=1,max_tool_calls=0))


def workflow(runtime,*,project=PROJECT):
    return WorkflowFactory(catalog=WorkflowCatalog(agents={'author':load_agent(project)},
        schemas={'result':{'type':'object','properties':{'approved':{'type':'boolean'}},'required':['approved'],'additionalProperties':False}}),
        bindings=WorkflowBindings(config=runtime.config),
        policy=WorkflowPolicy(allowed_agents={'author'},allowed_schemas={'result'},allowed_model_tiers={'fast'},allow_agent_composition=True,
            max_calls=2,max_attempts=1,max_provider_requests_per_invocation=1,max_tool_calls_per_invocation=0)).build({
        'version':1,'name':'sent-effort','start':'first','steps':{
        'first':{'kind':'agent','agent':'author','schema':'result','next':'approval'},
        'approval':{'kind':'pause','question':'Continue?','choices':{'approve':'second'}},
        'second':{'kind':'agent','agent':'author','schema':'result','next':'done'},'done':{'kind':'finish'}}})


def public_view(state):
    return {key:state[key] for key in ('status','calls') if key in state}


def main():
    import argparse,json
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if not args.live:parser.error('--live is required to contact the configured endpoint')
    result=run_review(build_runtime(),load_agent())
    print(json.dumps(effort_report(result),sort_keys=True))
    if result.exit_code:raise SystemExit(result.exit_code)


if __name__=='__main__':main()
