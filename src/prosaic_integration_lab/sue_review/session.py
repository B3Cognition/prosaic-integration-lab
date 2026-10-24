"""Trusted host API. Public Harness stores own every accepted answer and receipt."""

from dataclasses import asdict
import re

from .contracts import ReviewError, ReviewSettings, digest, own, reference
from .engine import load_engine
from .sources import freeze_documents, verify_frozen


class SueReviewSession:
    def __init__(self, settings, store, config, principal, namespace, accounting=None, *, clock=None, constrained_json=False):
        if type(constrained_json) is not bool:
            raise ReviewError('invalid_review_settings')
        self.constrained_json = constrained_json
        self.settings = settings if type(settings) is ReviewSettings else ReviewSettings.from_mapping(settings)
        if not reference(namespace) or any(not reference(getattr(principal,n,None)) for n in ('tenant_id','actor_id','billing_account_id')):
            raise ReviewError('invalid_review_owner')
        self.store,self.config,self.principal,self.namespace,self.accounting = store,config,principal,namespace,accounting
        self.clock = clock

    def _id(self, run_id):
        if type(run_id) is not str or not re.fullmatch('[0-9a-f]{32}',run_id):
            raise ReviewError('invalid_run_id')

    def _owned(self, run_id):
        self._id(run_id)
        snapshot = self.store.load_run(run_id)
        expected = {'application_id':'integration-lab-sue-review','project_id':self.namespace,
                    'tenant_id':self.principal.tenant_id,'actor_id':self.principal.actor_id,
                    'billing_account_id':self.principal.billing_account_id}
        saved = snapshot.state.get('accounting_context') or {}
        if any(saved.get(k) != v for k,v in expected.items()):
            raise PermissionError('run_not_found')
        return snapshot

    def _harness(self, run_id, policy, expected_engine):
        from prosaic_harness import Harness
        from prosaic_runtime import ExecutionContext
        from .workflow import build_review_workflow
        engine = load_engine(expected_engine)
        policy = dict(policy)
        constrained_json = policy.pop('constrained_json', False)
        settings = ReviewSettings.from_mapping({'enabled':True,**policy})
        workflow = build_review_workflow(config=self.config,settings=settings,engine=engine,
                                         constrained_json=constrained_json)
        options = {'clock':self.clock} if self.clock is not None else {}
        return Harness(workflow,store=self.store,run_id=run_id,accounting=self.accounting,
               context=ExecutionContext(application_id='integration-lab-sue-review',project_id=self.namespace,
                    tenant_id=self.principal.tenant_id,actor_id=self.principal.actor_id,
                    billing_account_id=self.principal.billing_account_id,request_id=run_id),**options)

    def start(self, run_id, *, seed, sources, lens='euthyphro', max_turns=14):
        if not self.settings.enabled:
            raise ReviewError('review_disabled')
        from prosaic_harness import RunNotFound
        self._id(run_id)
        if type(seed) is not str or not seed.strip() or len(seed.encode('utf-8'))>2048 or type(max_turns) is not int or not 1<=max_turns<=self.settings.max_turns:
            raise ReviewError('invalid_review_request')
        engine = load_engine(self.settings.engine_identity)
        caps = engine.capabilities()
        if lens not in caps['lenses']:
            raise ReviewError('invalid_lens')
        frozen = freeze_documents(sources) if type(sources) is list else verify_frozen(sources)
        capture = frozen['capture']
        if capture is not None and any(capture.get(k) != v for k,v in {'tenant_id':self.principal.tenant_id,'actor_id':self.principal.actor_id,'billing_account_id':self.principal.billing_account_id,'namespace':self.namespace}.items()):
            raise PermissionError('source_scope_mismatch')
        policy = {k:v for k,v in asdict(self.settings).items() if k!='enabled'}
        if self.constrained_json:
            policy['constrained_json'] = True
        policy['engine_identity'] = caps['engineIdentity']['digest']
        request = own({'seed':seed,'lens':lens,'maxTurns':max_turns,'evidence':frozen,'engine':caps,'reviewPolicy':policy})
        request['requestSignature'] = digest(request)
        try:
            saved = self._owned(run_id)
        except RunNotFound:
            saved = None
        if saved is not None:
            if saved.state['inputs']['requestSignature'] != request['requestSignature']:
                raise ReviewError('review_request_conflict')
            return self.status(run_id)
        self._harness(run_id,policy,policy['engine_identity']).run(request)
        return self.status(run_id)

    def _saved_harness(self, run_id):
        snapshot = self._owned(run_id)
        request = snapshot.state['inputs']
        check = dict(request); signature=check.pop('requestSignature',None)
        if signature!=digest(check):
            raise ReviewError('request_identity_mismatch')
        try:
            harness = self._harness(run_id,request['reviewPolicy'],request['engine']['engineIdentity']['digest'])
            return harness,harness.status()
        except ReviewError as error:
            if error.code in {'engine_unavailable','engine_identity_mismatch'}:
                raise ReviewError('binding_unavailable') from None
            raise
        except ValueError:
            # Public Harness validation also rejects changed runtime/catalogue
            # fingerprints. Inspection must not silently rebuild or dispatch.
            raise ReviewError('binding_unavailable') from None

    def status(self, run_id):
        _,snapshot = self._saved_harness(run_id)
        state = snapshot.state
        outputs = state['outputs']
        terminal = outputs[sorted(outputs)[-1]]['terminal'] if outputs else None
        return {'runId':run_id,'status':state['status'],'reason':state['reason'],'revision':snapshot.revision,
                'terminal':terminal,'acceptedTurns':len(outputs),'attempts':state['calls'],
                'sourcesSha256':state['inputs']['evidence']['sourcesSha256'],'deadline':state['deadline'],
                'proposal':self._proposal(state['inputs'])}

    @staticmethod
    def _proposal(request):
        return own({'requestSignature':request['requestSignature'],'seed':request['seed'],
                    'lens':request['lens'],'maxTurns':request['maxTurns'],
                    'engineIdentity':request['engine']['engineIdentity']['digest'],
                    'sourcesSha256':request['evidence']['sourcesSha256'],
                    'sources':[{'sourceId':s['sourceId'],'textSha256':s['textSha256'],
                                'revision':s['revision'],'reference':s['reference']} for s in request['evidence']['sources']],
                    'policy':request['reviewPolicy']})

    def resume(self, run_id, *, expected_revision, choice=None):
        if not self.settings.enabled:
            raise ReviewError('review_disabled')
        if choice is not None and choice not in {'continue','reject'}:
            raise ReviewError('invalid_review_choice')
        harness,snapshot = self._saved_harness(run_id)
        harness.resume(expected_revision=expected_revision,choice=choice)
        return self.status(run_id)

    def report(self, run_id):
        from .workflow import fold_accepted
        from .reporting import render_review
        _,snapshot = self._saved_harness(run_id)
        request,state = snapshot.state['inputs'],snapshot.state
        engine = load_engine(request['engine']['engineIdentity']['digest'])
        accepted = fold_accepted(request,state['outputs'],engine=engine)
        usage = [v['token_usage'] for v in state['invocations']]
        report = render_review(request,accepted,{'coverage':engine.coverage(accepted),'attempts':state['calls'],
                      'reportedTokens':sum(v for v in usage if v is not None),'usageComplete':all(v is not None for v in usage)})
        return {**report,'runId':run_id,'status':state['status'],'reason':state['reason'],
                'deadline':state['deadline'],'proposal':self._proposal(request)}
