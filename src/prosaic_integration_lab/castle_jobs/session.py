"""Host-authorized job sessions; no retrieval hooks or corpus writers."""

from dataclasses import asdict
import re

from .contracts import (CastleJobError, JobSettings, KINDS, digest, freeze_candidates,
                        freeze_entities, interpret, own, reference, validate_request)

APPLICATION = 'integration-lab-castle-jobs'


class CastleJobSession:
    def __init__(self, settings, store, config, principal, namespace, accounting=None, *, clock=None):
        self.settings = settings if type(settings) is JobSettings else JobSettings.from_mapping(settings)
        if not reference(namespace) or any(not reference(getattr(principal,k,None)) for k in ('tenant_id','actor_id','billing_account_id')):
            raise CastleJobError('invalid_job_owner')
        self.store,self.config,self.principal,self.namespace,self.accounting = store,config,principal,namespace,accounting
        self.clock = clock

    def _owner(self):
        return {'application_id':APPLICATION,'project_id':self.namespace,'tenant_id':self.principal.tenant_id,
                'actor_id':self.principal.actor_id,'billing_account_id':self.principal.billing_account_id}

    @staticmethod
    def _id(run_id):
        if type(run_id) is not str or re.fullmatch('[0-9a-f]{32}',run_id) is None:
            raise CastleJobError('invalid_run_id')

    def _owned(self, run_id):
        self._id(run_id)
        snapshot = self.store.load_run(run_id)
        saved = snapshot.state.get('accounting_context') or {}
        if any(saved.get(k) != v for k,v in self._owner().items()):
            raise PermissionError('run_not_found')
        request = snapshot.state['inputs']
        validate_request(request)
        if request['owner'] != self._owner():
            raise PermissionError('run_not_found')
        return snapshot

    def _harness(self, run_id, policy):
        from prosaic_harness import Harness
        from prosaic_runtime import ExecutionContext
        from .workflow import build_job_workflow
        workflow = build_job_workflow(config=self.config,settings=JobSettings.from_mapping({'enabled':True,**policy}))
        options = {'clock':self.clock} if self.clock is not None else {}
        return Harness(workflow,store=self.store,run_id=run_id,accounting=self.accounting,
                       context=ExecutionContext(**self._owner(),request_id=run_id),**options)

    def start(self, run_id, *, kind, candidates, query=None, top_n=None, entities=None):
        if not self.settings.enabled:
            raise CastleJobError('castle_jobs_disabled')
        from prosaic_harness import RunNotFound
        self._id(run_id)
        if type(kind) is not str or kind not in KINDS:
            raise CastleJobError('invalid_job_kind')
        frozen = freeze_candidates(candidates)
        if kind == 'judge' and top_n is None:
            top_n = min(10,len(frozen))
        if kind == 'entity_refinement':
            entities = freeze_entities(entities,frozen)
        policy = {k:v for k,v in asdict(self.settings).items() if k != 'enabled'}
        request = own({'kind':kind,'candidates':frozen,'query':query,'topN':top_n,'entities':entities,
                       'policy':policy,'owner':self._owner()})
        request['requestSignature'] = digest(request)
        validate_request(request)
        try:
            saved = self._owned(run_id)
        except RunNotFound:
            saved = None
        if saved is not None:
            if saved.state['inputs']['requestSignature'] != request['requestSignature']:
                raise CastleJobError('job_request_conflict')
            return self.status(run_id)
        self._harness(run_id,policy).run(request)
        return self.status(run_id)

    def _saved_harness(self, run_id):
        snapshot = self._owned(run_id)
        harness = self._harness(run_id,snapshot.state['inputs']['policy'])
        try:
            return harness,harness.status()
        except ValueError:
            raise CastleJobError('binding_unavailable') from None

    @staticmethod
    def _view(run_id, snapshot):
        state = snapshot.state
        request = state['inputs']
        return {'runId':run_id,'status':state['status'],'reason':state['reason'],'revision':snapshot.revision,
                'kind':request['kind'],'attempts':state['calls'],'deadline':state['deadline'],
                'requestSignature':request['requestSignature'],'candidatesSha256':digest(request['candidates']),
                'sources':[{'sourceId':s['sourceId'],'revision':s['revision'],'reference':s['reference'],
                            'textSha256':s['textSha256']} for s in request['candidates']]}

    def status(self, run_id):
        _,snapshot = self._saved_harness(run_id)
        return self._view(run_id,snapshot)

    def resume(self, run_id, *, expected_revision, choice=None):
        if not self.settings.enabled:
            raise CastleJobError('castle_jobs_disabled')
        if choice is not None and choice not in {'continue','reject'}:
            raise CastleJobError('invalid_job_choice')
        harness,_ = self._saved_harness(run_id)
        # Do not expose retry_interrupted. Only public Harness receipt adoption
        # may finish a pending call; uncertain execution never permits redispatch.
        harness.resume(expected_revision=expected_revision,choice=choice)
        return self.status(run_id)

    def report(self, run_id):
        _,snapshot = self._saved_harness(run_id)
        state = snapshot.state
        output = state['outputs'].get('job')
        raw = output['rawResponse'] if output is not None else None
        failure = None if output is not None else (state['reason'] or state['status'])
        report = interpret(state['inputs'],raw,failure=failure)
        report['audit']['receiptSha256'] = state['invocations'][-1]['receipt_sha256'] if state['invocations'] else None
        usage = [v['token_usage'] for v in state['invocations']]
        return {**self._view(run_id,snapshot),**report,'reportedTokens':sum(v for v in usage if v is not None),
                'usageComplete':all(v is not None for v in usage)}
