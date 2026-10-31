"""Authenticated embedding of the installed public Harness conversation API."""
from fastapi import HTTPException

from .conversation_registry import APPLICATION,ConversationRegistry,capacity,reference
from .views import public_conversation_history,public_usage
from .observability import scoped_observer


PHASES=frozenset({'receiptSaved','turnCommitted','workflowCommandPrepared','workflowCommandReturned'})


def phase_observer(config,on_event=None):
    def observed(event):
        if config.get('fixture_events_url') and event.get('event') in PHASES:
            import httpx
            response=httpx.post(config['fixture_events_url']+'/'+event['event'],timeout=35)
            response.raise_for_status()
        if on_event is not None:on_event(event)
    return observed


def require_conversation_sdk():
    import prosaic_harness as harness
    import prosaic_harness_postgres as postgres
    from prosaic_runtime import ProsaicRuntime
    if ('conversation_turn_v1' not in ProsaicRuntime.capabilities or
        any(not hasattr(harness,name) for name in ('Conversation','ConversationBindings',
            'ConversationScope','ConversationPolicy','ConversationError')) or
        not hasattr(postgres,'PostgresSessionStore')):
        raise ValueError('conversation capability unavailable')


def validate_settings(settings):
    if (type(settings) is not dict or set(settings)-{'dsn','bundles','tenants','max_sessions','max_owner_sessions'} or
            not {'dsn','bundles','tenants'}<=set(settings) or type(settings['dsn']) is not str or
            not settings['dsn'] or type(settings['bundles']) is not list or not settings['bundles'] or
            type(settings['tenants']) is not dict or not settings['tenants']):
        raise ValueError('invalid conversation configuration')
    capacity(settings.get('max_sessions',128),settings.get('max_owner_sessions',16))
    return settings


def current_grant(host,principal,version=None):
    settings=host.config['conversation']['tenants'].get(principal.tenant_id)
    if (type(settings) is not dict or settings.get('enabled') is not True or
        set(settings)-{'enabled','binding_version','retained_versions','actors'}):
        raise HTTPException(403,'conversation_access_denied')
    current=reference(settings['binding_version'])
    retained=settings.get('retained_versions',[])
    actors=settings.get('actors')
    if (type(retained) is not list or any(type(value) is not str for value in retained) or
        actors is not None and (type(actors) is not list or any(type(value) is not str for value in actors))):
        raise ValueError('invalid conversation grants')
    if actors is not None and principal.actor_id not in actors:
        raise HTTPException(403,'conversation_access_denied')
    if version is not None and version not in [current,*retained]:
        raise HTTPException(403,'conversation_access_denied')
    return settings


class ConversationExecution:
    def __init__(self,host,*,session_store=None):
        require_conversation_sdk()
        from prosaic_harness_postgres import PostgresSessionStore
        from .conversation_workflows import build_bindings
        self.host=host
        settings=validate_settings(host.config['conversation'])
        self.max_sessions=settings.get('max_sessions',128)
        self.max_owner_sessions=settings.get('max_owner_sessions',16)
        capacity(self.max_sessions,self.max_owner_sessions)
        self.registry=ConversationRegistry(host.config['app_dsn'],namespace=host.config['namespace'],
            environment=host.config['environment'])
        self.bindings={}
        self.workflow_materials={}
        for definition in settings['bundles']:
            binding=build_bindings(host,definition,registry=self.registry,workflow_materials=self.workflow_materials)
            if binding.version in self.bindings:raise ValueError('duplicate conversation binding version')
            self.bindings[binding.version]=binding
        if not self.bindings or type(settings['tenants']) is not dict:
            raise ValueError('invalid conversation configuration')
        for grant in settings['tenants'].values():
            if type(grant) is not dict or grant.get('binding_version') not in self.bindings:
                raise ValueError('missing retained conversation binding')
            if any(version not in self.bindings for version in grant.get('retained_versions',[])):
                raise ValueError('missing retained conversation binding')
        self.store=session_store if session_store is not None else PostgresSessionStore(settings['dsn'],namespace=host.config['namespace'],
            max_active_leases=2,lease_s=15,renew_s=3,operation_timeout_s=5,pool_timeout_s=2,
            connect_timeout_s=3,lock_timeout_s=1,statement_timeout_s=3)

    def ready(self):
        self.registry.check_ready()
        self.store.check_ready()

    def close(self):self.store.close()

    def _controller(self,principal,reservation):
        from prosaic_harness import Conversation,ConversationScope
        from prosaic_runtime import ExecutionContext
        binding=self.bindings.get(reservation['binding_version'])
        if binding is None or binding.identity!=reservation['binding_identity']:
            raise HTTPException(409,{'code':'bindingConflict'})
        scope=ConversationScope(reservation['namespace'],reservation['environment'],APPLICATION,
            reservation['tenant_id'],reservation['actor_id'],reservation['billing_account_id'])
        context=ExecutionContext(application_id=APPLICATION,tenant_id=reservation['tenant_id'],
            actor_id=reservation['actor_id'],billing_account_id=reservation['billing_account_id'],
            request_id=reservation['session_id'],run_id=reservation['session_id'])
        return Conversation(binding,store=self.store,scope=scope,context=context,
            accounting=self.host.recorder,observer=scoped_observer(self.host,reservation['session_id']))

    def _owned(self,principal,session_id):
        current_grant(self.host,principal)
        reservation=self.registry.owned(principal,session_id)
        if reservation is None:raise HTTPException(404,'not_found')
        current_grant(self.host,principal,reservation['binding_version'])
        return reservation

    def create_request(self,principal,key):
        settings=current_grant(self.host,principal)
        reservation=self.registry.creation(principal,key)
        if reservation is None:
            binding=self.bindings[settings['binding_version']]
            reservation=self.registry.reserve_creation(principal,key,binding.identity,binding.version,
                max_sessions=self.max_sessions,max_owner_sessions=self.max_owner_sessions)
        current_grant(self.host,principal,reservation['binding_version'])
        controller=self._controller(principal,reservation)
        # Public create is idempotent for the exact preallocated scope and binding.
        # No application transaction/connection remains open across this call.
        snapshot=controller.create(session_id=reservation['session_id'])
        self.registry.adopt_creation(reservation,snapshot.session_id)
        return controller.status(snapshot.session_id).document

    def status_request(self,principal,session_id):
        row=self._owned(principal,session_id)
        return self._attachment_status(row,self._controller(principal,row).status(session_id).document)

    def _workflow_harness(self,row):
        from prosaic_harness import Harness
        from prosaic_runtime import ExecutionContext
        workflow,registration=self.workflow_materials[row['binding_version']]
        context=ExecutionContext(application_id=APPLICATION,tenant_id=row['tenant_id'],
            actor_id=row['actor_id'],billing_account_id=row['billing_account_id'],
            request_id='workflow-'+row['session_id'],run_id=row['session_id'])
        return registration,Harness(workflow,store=self.host.store,run_id=row['session_id'],context=context,
            accounting=self.host.recorder,observer=scoped_observer(self.host,row['session_id']))

    def _attachment_status(self,row,reply):
        """Project uncertain host intent; neither read nor recovery grants a start."""
        from prosaic_harness import RunNotFound
        link=self.registry.workflow(row)
        if link is None or link['phase']=='attached':return reply
        registration,harness=self._workflow_harness(row)
        if link['registration']!=registration:raise HTTPException(409,{'code':'bindingConflict'})
        try:harness.status()
        except RunNotFound:
            return {**reply,'status':'needsResolution','recoveryStatus':'needsResolution'}
        return reply

    def history_request(self,principal,session_id):
        row=self._owned(principal,session_id)
        return public_conversation_history(session_id,self._controller(principal,row).history(session_id))

    def usage_request(self,principal,session_id):
        row=self._owned(principal,session_id)
        self._controller(principal,row).status(session_id)
        report=self.host.recorder.report(application_id=APPLICATION,tenant_id=row['tenant_id'],
            actor_id=row['actor_id'],billing_account_id=row['billing_account_id'],
            request_id=session_id,run_id=session_id)
        result={'conversation':public_usage(report)}
        if self.registry.workflow(row) is not None:
            workflow=self.host.recorder.report(application_id=APPLICATION,tenant_id=row['tenant_id'],
                actor_id=row['actor_id'],billing_account_id=row['billing_account_id'],
                request_id='workflow-'+session_id,run_id=session_id)
            result['workflow']=public_usage(workflow)
        return result

    def observation_request(self,principal,session_id,observations):
        from .run_observations import usage_projection
        row = self._owned(principal,session_id)
        status = self._controller(principal,row).status(session_id).document
        # Frozen accounting attribution comes from the host reservation, never
        # a browser field. Observation availability does not authorize a retry.
        try:
            rows = self.host.recorder.calls(application_id=APPLICATION,
                tenant_id=row['tenant_id'],actor_id=row['actor_id'],
                billing_account_id=row['billing_account_id'],run_id=session_id)
        except Exception:
            rows = None
        result = observations.snapshot(session_id)
        result['usage'] = usage_projection(rows)
        result['sessionStatus'] = status.get('status')
        result['failureCode'] = status.get('failureCode')
        result['waiting'] = status.get('pendingInteraction') is not None
        return result

    def send_request(self,principal,session_id,*,message_id,message,expected_revision,
            interaction_ref=None,on_event=None):
        row=self._owned(principal,session_id)
        controller=self._controller(principal,row)
        reply=controller.send(session_id,message_id=message_id,message=message,
            expected_revision=expected_revision,interaction_ref=interaction_ref,
            on_event=phase_observer(self.host.config,on_event)).document
        if message=='Find players' and reply.get('status')=='completed' and row['binding_version'] in self.workflow_materials:
            return self.attach_owned_workflow(principal,row,controller,reply)
        return reply

    def attach_owned_workflow(self,principal,row,controller,reply):
        """A host-approved intent; unknown starts never grant a second run call."""
        from prosaic_harness import RunNotFound
        registration,harness=self._workflow_harness(row)
        current=controller.status(row['session_id']).document
        link=self.registry.workflow(row)
        if link is None:
            if (current.get('messageId')!=reply.get('messageId') or current['revision']!=reply['revision'] or
                    current.get('pendingInteraction') is not None):
                return reply
            link=self.registry.reserve_workflow(row,registration,reply['messageId'],reply['revision'])
        if link['source_message_id']!=reply['messageId'] or link['registration']!=registration:
            return reply
        if link['phase']=='attached':
            return current if current.get('messageId')==reply.get('messageId') else reply
        claimed=self.registry.claim_workflow_start(row)
        try:saved=harness.status()
        except RunNotFound:
            if not claimed:raise HTTPException(409,{'code':'needsResolution'}) from None
            # The one durable claim was committed before this only dispatch.
            harness.run(inputs={})
            saved=harness.status()
        displayed=current.get('pendingInteraction')
        if displayed is not None and displayed.get('runId')==row['session_id']:
            self.registry.workflow_started(row)
            self.registry.workflow_attached(row)
            return current if current.get('messageId')==reply.get('messageId') else reply
        if saved.state['status']=='completed':
            # Public attach is idempotent for an already linked registration/run.
            # This repairs only the immutable existing intent; no run is started
            # or resumed, and the SDK retains its authoritative session state.
            result=controller.attach_workflow(row['session_id'],registration=registration,
                run_id=row['session_id'],expected_revision=current['revision']).document
            self.registry.workflow_started(row)
            self.registry.workflow_attached(row)
            return result if current.get('messageId')==reply.get('messageId') else reply
        interaction=harness.interaction(include_response_schema=True)
        if interaction is None or interaction.to_dict().get('stepId')!='select':
            raise HTTPException(409,{'code':'needsResolution'})
        self.registry.workflow_started(row)
        current=controller.status(row['session_id']).document
        displayed=current.get('pendingInteraction')
        if displayed is not None and displayed.get('runId')==row['session_id']:
            self.registry.workflow_attached(row)
            return current
        if (current.get('messageId')!=link['source_message_id'] or current['revision']!=link['source_revision']):
            raise HTTPException(409,{'code':'interactionStale'})
        result=controller.attach_workflow(row['session_id'],registration=registration,
            run_id=row['session_id'],expected_revision=current['revision']).document
        self.registry.workflow_attached(row)
        return result

    def recover_request(self,principal,session_id):
        row=self._owned(principal,session_id)
        controller=self._controller(principal,row)
        current=controller.status(session_id).document
        projected=self._attachment_status(row,current)
        if projected!=current:return projected
        return self._attachment_status(row,controller.recover(session_id).document)

    def retry_request(self,principal,session_id,*,expected_revision,acknowledge_effect_risk):
        row=self._owned(principal,session_id)
        return self._controller(principal,row).retry_interrupted(session_id,
            expected_revision=expected_revision,acknowledge_effect_risk=acknowledge_effect_risk).document
