"""Authenticated embedding of the installed public Harness conversation API."""
from fastapi import HTTPException

from .conversation_registry import APPLICATION,ConversationRegistry,capacity,reference
from .views import public_conversation_history,public_usage


def require_conversation_sdk():
    import prosaic_harness as harness
    import prosaic_harness_postgres as postgres
    from prosaic_runtime import ProsaicRuntime
    if ('conversation_turn_v1' not in ProsaicRuntime.capabilities or
        any(not hasattr(harness,name) for name in ('Conversation','ConversationBindings',
            'ConversationScope','ConversationPolicy','ConversationError')) or
        not hasattr(postgres,'PostgresSessionStore')):
        raise ValueError('conversation capability unavailable')


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
    def __init__(self,host):
        require_conversation_sdk()
        from prosaic_harness_postgres import PostgresSessionStore
        from .conversation_workflows import build_bindings
        self.host=host
        settings=host.config['conversation']
        if (type(settings) is not dict or set(settings)-{'dsn','bundles','tenants',
                'max_sessions','max_owner_sessions'} or not {'dsn','bundles','tenants'}<=set(settings)):
            raise ValueError('invalid conversation configuration')
        self.max_sessions=settings.get('max_sessions',128)
        self.max_owner_sessions=settings.get('max_owner_sessions',16)
        capacity(self.max_sessions,self.max_owner_sessions)
        self.registry=ConversationRegistry(host.config['app_dsn'],namespace=host.config['namespace'],
            environment=host.config['environment'])
        self.bindings={}
        for definition in settings['bundles']:
            binding=build_bindings(host,definition)
            if binding.version in self.bindings:raise ValueError('duplicate conversation binding version')
            self.bindings[binding.version]=binding
        if not self.bindings or type(settings['tenants']) is not dict:
            raise ValueError('invalid conversation configuration')
        for grant in settings['tenants'].values():
            if type(grant) is not dict or grant.get('binding_version') not in self.bindings:
                raise ValueError('missing retained conversation binding')
            if any(version not in self.bindings for version in grant.get('retained_versions',[])):
                raise ValueError('missing retained conversation binding')
        self.store=PostgresSessionStore(settings['dsn'],namespace=host.config['namespace'],
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
            accounting=self.host.recorder,observer=self.host.observer)

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
        return self._controller(principal,row).status(session_id).document

    def history_request(self,principal,session_id):
        row=self._owned(principal,session_id)
        return public_conversation_history(session_id,self._controller(principal,row).history(session_id))

    def usage_request(self,principal,session_id):
        row=self._owned(principal,session_id)
        self._controller(principal,row).status(session_id)
        report=self.host.recorder.report(application_id=APPLICATION,tenant_id=row['tenant_id'],
            actor_id=row['actor_id'],billing_account_id=row['billing_account_id'],
            request_id=session_id,run_id=session_id)
        return {'conversation':public_usage(report)}

    def send_request(self,principal,session_id,*,message_id,message,expected_revision,
            interaction_ref=None,on_event=None):
        row=self._owned(principal,session_id)
        return self._controller(principal,row).send(session_id,message_id=message_id,message=message,
            expected_revision=expected_revision,interaction_ref=interaction_ref,on_event=on_event).document

    def recover_request(self,principal,session_id):
        row=self._owned(principal,session_id)
        return self._controller(principal,row).recover(session_id).document

    def retry_request(self,principal,session_id,*,expected_revision,acknowledge_effect_risk):
        row=self._owned(principal,session_id)
        return self._controller(principal,row).retry_interrupted(session_id,
            expected_revision=expected_revision,acknowledge_effect_risk=acknowledge_effect_risk).document
