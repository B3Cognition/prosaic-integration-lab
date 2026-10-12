"""Owned synthetic native workflows, admitted only through public SDK APIs."""
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

from fastapi import HTTPException
from prosaic_harness import (Harness, RunNotFound, Validator, WorkflowBindings,
    WorkflowBundle, WorkflowCatalog, WorkflowFactory, WorkflowPolicy, WorkflowReference)
from prosaic_runtime import EndpointConfig, ExecutionContext, ProsaicArtifact, RuntimeConfig

from .bundles import BundleRegistry
from .identity import Principal
from .observability import bind_run
from .proposals import (ProposalStore, bounded_text, canonical_proposal,
    proposal_transport_schema, validate_proposal_transport)
from .views import public_native_interaction, public_run, uncertain_run


def approved(output, context):
    return [] if output.get('approved') is True else ['synthetic_review_not_approved']


def approved_proposal():
    return {'definition':{'version':1,'start':'find','steps':{
        'find':{'kind':'agent','agent':'finder','schema':'found','next':'review'},
        'review':{'kind':'agent','agent':'reviewer','schema':'reviewed','inputs':['find'],'next':'checked'},
        'checked':{'kind':'check','from':'review','validators':['approved'],'pass':'gate','fail':'rejected'},
        'gate':{'kind':'gate','from':'review','field':['approved'],'equals':True,'pass':'confirm','fail':'rejected'},
        'confirm':{'kind':'pause','question':'Accept the synthetic review?',
            'choices':{'accept':'done','reject':'rejected'},'requires':['find','review'],'response_schema':'decision'},
        'done':{'kind':'finish','requires':['find','review']},
        'rejected':{'kind':'finish','outcome':'rejected'}}}}


def grants(value):
    """Trusted configuration; no request or model data enters this projection."""
    allowed = {'bundle_version','composition','inline','agents','schemas','validators','model_tiers',
               'review_outputs','response_schema','tools'}
    if type(value) is not dict or set(value) - allowed:
        raise ValueError('invalid native configuration')
    result = {'composition':False,'inline':False,'agents':['finder','reviewer'],
        'schemas':['found','reviewed','decision'],'validators':['approved'],'model_tiers':[],
        'review_outputs':False,'response_schema':False,'tools':[], **value}
    for name in ('composition','inline','review_outputs','response_schema'):
        if type(result[name]) is not bool: raise ValueError('invalid native configuration')
    for name in ('agents','schemas','validators','model_tiers','tools'):
        if type(result[name]) is not list or any(type(v) is not str for v in result[name]):
            raise ValueError('invalid native configuration')
    return result


class NativeExecution:
    def __init__(self, host):
        self.host = host
        self.proposals = ProposalStore(host.config['app_dsn'])
        self.registry = BundleRegistry()
        self.factories = {}
        materials, frozen_grants = {}, {}
        native = host.config['native']
        if type(native) is not dict or set(native) != {'bundles','tenants'} or not native['bundles']:
            raise ValueError('invalid native configuration')
        for definition in native['bundles']:
            if set(definition) - {'version','model_url','operation_namespace','journal_identity','policies','routes','assets','fixture_effects','fixture_effect_version','fixture_provider_request_limit','fixture_tiers'}:
                raise ValueError('invalid native configuration')
            if (type(definition.get('fixture_tiers',False)) is not bool or
                definition.get('fixture_tiers') and not definition.get('fixture_effects')):
                raise ValueError('fixture tiers require explicit fixture bindings')
            if type(definition.get('fixture_effects',False)) is not bool:
                raise ValueError('invalid native configuration')
            if definition.get('fixture_effect_version','v1') not in {'v1','v2'}:
                raise ValueError('invalid fixture semantic version')
            if 'fixture_provider_request_limit' in definition and (
                not definition.get('fixture_effects') or type(definition['fixture_provider_request_limit']) is not int or
                definition['fixture_provider_request_limit'] not in {1,2}):
                raise ValueError('invalid fixture provider limit')
            material = self.material(definition)
            # Historical grants travel with each retained host bundle. Never rebuild
            # an old identity using mutable current tenant grants on a fresh worker.
            for tenant, settings in definition['policies'].items():
                setting = grants(settings)
                factory = self.factory(material, setting)
                bundle = self.registry.register(WorkflowBundle(definition['version'],factory))
                key = (tenant,definition['version'])
                if key in self.factories: raise ValueError('invalid native configuration')
                self.factories[key] = (bundle,factory)
                materials[key] = material
                # An encoded owned value cannot alias mutable host configuration.
                frozen_grants[key] = json.dumps(setting,sort_keys=True)
        self._materials = MappingProxyType(materials)
        self._frozen_grants = MappingProxyType(frozen_grants)
        for tenant, value in native['tenants'].items():
            current = grants(value)
            if (tenant,current['bundle_version']) not in self.factories:
                raise ValueError('invalid native configuration')

    def material(self, definition):
        directory = Path(definition['assets']) if 'assets' in definition else Path(self.host.config['assets'])/'native'
        agents = {}
        for alias in ('finder','reviewer'):
            agents[alias] = ProsaicArtifact.from_inspection({'id':f'native/agents/{alias}.md',
                'type':'subagent','frontmatter':{'name':alias,'description':f'Synthetic {alias}',
                'tools':[]},'body':(directory/'agents'/f'{alias}.md').read_text()})
        effects=definition.get('fixture_effects',False)
        if effects:
            if not self.host.config.get('fixture_events_url') or not definition.get('journal_identity'):
                raise ValueError('fixture effects require explicit fixture bindings')
            agents['effecter']=ProsaicArtifact.from_inspection({'id':'native/agents/effecter.md',
                'type':'subagent','frontmatter':{'name':'effecter','description':'Synthetic domain operation',
                'tools':['fixture_apply']},'body':'ALWAYS execute fixture_apply once, then return the request entity_id as JSON.'})
        schemas = {name:json.loads((directory/'schemas'/f'{name}.json').read_text())
            for name in ('found','reviewed','decision')}
        tools=self.effect_tools(definition.get('fixture_effect_version','v1')) if effects else {}
        catalog = WorkflowCatalog(agents=agents,schemas=schemas,public_metadata={
            'agents':{name:{'description':f'Synthetic {name} fixture'} for name in agents},
            'schemas':{name:{'description':f'Closed synthetic {name} value'} for name in schemas},
            'validators':{'approved':{'description':'Synthetic approved flag check'}}})
        profiles={'fixture':EndpointConfig(definition['model_url'],'test-model',features={'streaming':False})}
        routes=dict(definition.get('routes',{}))
        if definition.get('fixture_tiers',False):
            for tier in ('balanced','strong'):
                profiles['fixture-'+tier]=EndpointConfig(definition['model_url'],'fixture-'+tier,
                    features={'streaming':False})
                routes[tier]='fixture-'+tier
        config = RuntimeConfig(profiles,routes,'fixture',
            allowed_tools=frozenset(tools))
        journal = None
        if 'journal_identity' in definition:
            from .tool_journal import PgToolJournal
            journal = PgToolJournal(self.host.config['app_dsn'],identity=definition['journal_identity'])
            if effects:
                native=self
                class FixtureJournal(PgToolJournal):
                    def claim(self,*args):
                        result=super().claim(*args)
                        if result.state=='new':native.effect_event('tool-claimed')
                        return result
                    def commit(self,*args):
                        super().commit(*args)
                        native.effect_event('tool-committed')
                journal=FixtureJournal(self.host.config['app_dsn'],identity=definition['journal_identity'])
        bindings = WorkflowBindings(config=config,custom_tools=tools,validators={'approved':Validator('1.0.0',approved)},
            operation_namespace=definition['operation_namespace'],tool_journal=journal)
        return catalog, bindings, definition.get('fixture_provider_request_limit',2 if effects else 1)

    def effect_event(self,name):
        import httpx
        result=httpx.post(self.host.config['fixture_events_url']+'/'+name,timeout=35)
        result.raise_for_status()

    def effect_tools(self,version):
        from prosaic_runtime import CustomTool
        def business_key(arguments,context):
            # Trusted SDK scope identifies an already owner-authorized reservation.
            with self.host.metadata.connection() as connection:
                row=connection.execute('SELECT request FROM lab_app.runs WHERE run_id=%s',
                    (context.scope.run_id,)).fetchone()
            entity=row['request']['inputs']['entity_id']
            return bounded_text(entity)
        def apply(arguments,context):
            self.effect_event('tool-handler')
            with self.host.metadata.connection() as connection:
                connection.execute('''INSERT INTO lab_fixture.effects(namespace,business_key,amount)
                    VALUES (%s,%s,%s)''',(context.scope.operation_namespace,context.operation_key,
                        arguments['amount']*(2 if version=='v2' else 1)))
            self.effect_event('tool-effect')
            return {'applied':True}
        return {'fixture_apply':CustomTool('fixture_apply','Synthetic owned consequential operation',
            {'type':'object','properties':{'amount':{'type':'integer','minimum':1,'maximum':2}},
             'required':['amount'],'additionalProperties':False},apply,'fixture-domain-'+version+'-key-resolver-v1',
            with_context=True,operation_key=business_key,max_result_bytes=4096)}

    @staticmethod
    def factory(material, setting):
        catalog, bindings, provider_cap = material
        policy = WorkflowPolicy(allowed_agents=frozenset(setting['agents']),allowed_schemas=frozenset(setting['schemas']),
            allowed_tools=frozenset(setting['tools']),
            allowed_validators=frozenset(setting['validators']),allowed_model_tiers=frozenset(setting['model_tiers']),
            allow_agent_composition=setting['composition'],allow_inline_agents=setting['inline'],
            max_proposal_bytes=65536,max_run_input_bytes=4096,max_human_response_bytes=8192,
            max_calls=3,max_tokens=4096,max_run_s=120,timeout_s=30,max_attempts=1,
            max_provider_requests_per_invocation=provider_cap if setting['tools'] else 1,
            max_tool_calls_per_invocation=1 if setting['tools'] else 0)
        return WorkflowFactory(catalog=catalog,bindings=bindings,policy=policy)

    def current(self, principal):
        setting = self.host.config['native']['tenants'].get(principal.tenant_id)
        if setting is None: raise HTTPException(403,'native_access_denied')
        return grants(setting)

    def catalogue(self, principal):
        setting = self.current(principal)
        key = (principal.tenant_id,setting['bundle_version'])
        frozen = json.loads(self._frozen_grants[key])
        effective = {**setting}
        for name in ('composition','inline'):
            effective[name] = frozen[name] and setting[name]
        for name in ('agents','schemas','validators','model_tiers','tools'):
            effective[name] = sorted(set(frozen[name]) & set(setting[name]))
        # Discovery uses the registered bundle's public immutable material. It
        # never reads changed files or creates a replacement proposal identity.
        factory = self.factory(self._materials[key],effective)
        schema=factory.proposal_schema()
        schema.setdefault('allOf',[]).append(proposal_transport_schema())
        return {'bundle_version':setting['bundle_version'],'manifest':factory.describe(),
                'proposal_schema':schema}

    def propose(self, principal, key, text):
        bounded_text(key)
        content = canonical_proposal(text)
        digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
        # Replay's immutable reference is returned before newest-policy admission.
        row = self.proposals.replay(principal,key,digest)
        if row is None:
            setting = self.current(principal)
            bundle, _ = self.factories[(principal.tenant_id,setting['bundle_version'])]
            prepared = bundle.prepare_json(content)
            validate_proposal_transport(prepared.proposal_json)
            self.authorize(principal,content)
            row = self.proposals.reserve(principal,key,prepared,
                maximum_records=self.host.capacity['max_runs'],maximum_tenant_records=self.host.capacity['max_tenant_runs'])
        return {'proposal_id':row['proposal_id'],'reference':dict(row['reference'])}

    def authorize(self, principal, content):
        setting = self.current(principal)
        envelope = json.loads(content)
        definition = envelope.get('definition',{})
        steps = definition.get('steps',{}) if type(definition) is dict else {}
        if type(steps) is not dict: return  # SDK admission provides safe structural errors.
        agents = [step for step in steps.values() if type(step) is dict and step.get('kind') == 'agent']
        denied = (len(agents)>1 and not setting['composition'] or
                  bool(envelope.get('inline_agents')) and not setting['inline'])
        inline = envelope.get('inline_agents',{})
        for step in steps.values():
            if type(step) is not dict: continue
            for field, grant in (('schema','schemas'),('response_schema','schemas')):
                if field in step and step[field] not in setting[grant]: denied = True
            if step.get('kind') == 'agent':
                alias = step.get('agent')
                if type(alias) is str and alias not in setting['agents'] and alias not in inline: denied = True
                if any(tool not in setting['tools'] for tool in step.get('tools',[])):denied=True
            values = step.get('validators',[])
            if type(values) is list and any(name not in setting['validators'] for name in values): denied = True
        # Inline tiers must remain currently authorized independently of composition.
        if type(inline) is dict:
            for artifact in inline.values():
                if type(artifact) is not dict: continue
                fm = artifact.get('frontmatter',{})
                if type(fm) is dict:
                    if 'model_tier' in fm and fm['model_tier'] not in setting['model_tiers']:denied=True
                    if isinstance(fm.get('tools',[]),list) and any(tool not in setting['tools'] for tool in fm.get('tools',[])):denied=True
        if denied: raise HTTPException(403,'native_access_denied')
        return setting

    def workflow(self, principal, proposal_id):
        bounded_text(proposal_id)
        row = self.proposals.owned(principal,proposal_id)
        if row is None: raise HTTPException(404,'not_found')
        self.authorize(principal,row['proposal_json'])
        # Older retained proposals keep their original immutable reference. An
        # unsupported HTTP choice fails before run reservation or execution.
        validate_proposal_transport(row['proposal_json'])
        try:
            bundle = self.registry.resolve(row['bundle_version'],row['bundle_identity'])
        except ValueError:
            raise HTTPException(409,'bundle_unavailable') from None
        reference = WorkflowReference.from_dict(row['reference'])
        return row, bundle.reconstruct(row['proposal_json'],reference)

    @staticmethod
    def owner(reservation):
        return Principal(reservation['tenant_id'],reservation['actor_id'],reservation['billing_account_id'])

    def harness(self, reservation):
        self.host.check_scope(reservation)
        row, workflow = self.workflow(self.owner(reservation),reservation['request']['proposal_id'])
        if reservation['assets_hash'] != row['bundle_identity']: raise HTTPException(409,'bundle_conflict')
        context = ExecutionContext(application_id='integration-lab',tenant_id=reservation['tenant_id'],
            actor_id=reservation['actor_id'],billing_account_id=reservation['billing_account_id'],request_id=reservation['run_id'])
        return Harness(workflow,store=self.host.store,run_id=reservation['run_id'],context=context,
            accounting=self.host.recorder,observer=self.host.observer,
            on_event=self.host.fixture_event if self.host.config.get('fixture_events_url') else None)

    def status(self, reservation):
        bind_run(reservation)
        harness = self.harness(reservation)
        setting = self.current(self.owner(reservation))
        steps = harness.workflow.definition['steps']
        pauses = [step for step in steps.values() if step['kind']=='pause']
        review = ('review',) if (setting['review_outputs'] and steps.get('review',{}).get('kind')=='agent'
            and pauses and all('review' in step.get('requires',[]) for step in pauses)) else ()
        schema = setting['response_schema'] and all(step.get('response_schema') in (None,'decision') for step in pauses)
        try:
            interaction = harness.interaction(review_outputs=review,include_response_schema=schema,maximum_bytes=262144)
            if interaction is not None:
                view = public_native_interaction(interaction.to_dict(),include_response_schema=schema)
                return {'run_id':reservation['run_id'],'status':'waiting','current_step':view['stepId'],
                    'revision':view['revision'],'recovery_status':None,'interaction':view}
            snapshot = harness.status()
        except RunNotFound:
            return {**uncertain_run(reservation['run_id']),'interaction':None}
        return {**public_run(reservation['run_id'],snapshot.state,snapshot.revision,workflow='native'),'interaction':None}

    def start_request(self, principal, key, proposal_id, inputs):
        bounded_text(key)
        row, workflow = self.workflow(principal,proposal_id)
        owned = workflow.prepare_inputs(inputs)
        reservation = self.host.metadata.reserve_native(principal,key,row,owned,
            namespace=self.host.config['namespace'],environment=self.host.config['environment'],
            max_runs=self.host.capacity['max_runs'],max_tenant_runs=self.host.capacity['max_tenant_runs'])
        bind_run(reservation)
        if reservation['phase'] != 'reserved': return self.status(reservation)
        harness = self.harness(reservation)
        if not self.host.metadata.claim_start(reservation['run_id']): return self.status(reservation)
        harness.run(inputs=reservation['request']['inputs'])
        self.host.metadata.started(reservation['run_id'])
        return self.status(reservation)

    def resume(self, reservation, revision, choice, response, retry):
        self.harness(reservation).resume(choice=choice,response=response,expected_revision=revision,retry_interrupted=retry)
        return self.status(reservation)
