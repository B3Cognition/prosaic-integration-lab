"""New synthetic Castle-source composition; frozen hackathon v1 stays unchanged.

This module is a consumer, not a model-quality experiment. The historical scorer
receives an explicit reversible source-ID projection, with exact text/hash/line
bounds checked before execution. No historical source lock is rewritten.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import uuid


def project_case(case_id, frozen):
    from .requirements_review_v1.cases import load_cases
    from .requirements_review_v1.host_keys import fixture_answer, load_keys

    case = load_cases()[case_id]
    if len(frozen['sources']) != 1:
        raise ValueError('one exact synthetic specification required')
    source = frozen['sources'][0]
    original = case['sources'][0]
    if (source['text'] != original['text'] or source['revision'] != original['revision']
            or hashlib.sha256(source['text'].encode()).hexdigest() != source['textSha256']):
        raise ValueError('frozen specification differs from historical case')
    projected = deepcopy(case)
    projected['sources'][0]['sourceId'] = source['sourceId']
    answer = fixture_answer(case, load_keys()[case_id])
    for citation in answer['citations']:
        citation['sourceId'] = source['sourceId']

    def restore(value):
        result = deepcopy(value)
        for citation in result['citations']:
            if citation['sourceId'] != source['sourceId'] or citation['textSha256'] != source['textSha256']:
                raise ValueError('unbound source citation')
            citation['sourceId'] = original['sourceId']
        return result

    return projected, answer, restore


PREPARE = r'''
import json,sys
from pathlib import Path
from cognitive_castle.config import CognitiveCastleConfig
from cognitive_castle.backends.lancedb_backend import LanceDBBackend
from cognitive_castle.context import PalacePaths
from cognitive_castle.provider_setup import prepare_provider
root=Path(sys.argv[1]); source=json.loads(sys.argv[2]); namespace=sys.argv[3]
cfgdir=root/'config';cfgdir.mkdir(parents=True)
(cfgdir/'config.json').write_text(json.dumps({'embedder_dim':4,'embedder_model':'synthetic','embedding_device':'cpu'}))
cfg=CognitiveCastleConfig(config_dir=cfgdir);backend=LanceDBBackend(cfg=cfg)
col=backend.get_collection(str(root/'palace'),collection_name='castle_drawers',create=True)
col.upsert(ids=['spec','foreign','partial'],documents=[source['text'],source['text'],source['text']],
 metadatas=[{'wing':'approved','source_file':'fixture://requirements','source_revision':source['revision']},
 {'wing':'denied'},{'wing':'approved','ingest_complete':False}],embeddings=[[0.0]*4]*3)
backend.close();prepare_provider(PalacePaths.resolve(root/'palace'),namespace=namespace,config=cfg)
'''


def capture_case(case_id, *, worker_python, root, principal, namespace):
    """Actual installed lean worker, exact source expectation and trusted scope."""
    from .requirements_review_v1.cases import load_cases
    from prosaic_integration_lab.memory_provider import MemoryProviders
    from prosaic_integration_lab.sue_review.sources import freeze_castle_snapshot

    root = Path(root).resolve()
    source = load_cases()[case_id]['sources'][0]
    run = subprocess.run([worker_python, '-I', '-c', PREPARE, str(root), json.dumps(source), namespace],
                         capture_output=True, timeout=45)
    if run.returncode:
        raise RuntimeError('synthetic Castle preparation failed: ' + run.stderr.decode()[-1000:])
    binding = dict(vars(principal), namespace=namespace, palace_path=str(root/'palace'),
                   config_path=str(root/'config/config.json'),
                   worker_command=[worker_python, '-I', '-m', 'prosaic_castle.provider_worker'],
                   allowed_wings=['approved'], profile='memory-fts-v1', recency_boost=False,
                   startup_timeout=30, operation_timeout=10)
    expected_scope = {name: binding[name] for name in ('tenant_id','actor_id','billing_account_id','namespace')}
    expected_scope.update(binding_sha256=hashlib.sha256(json.dumps(binding, sort_keys=True,
        separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),allowed_wings=['approved'])
    providers = MemoryProviders({'enabled':True,'bindings':[binding]})
    try:
        captured = providers.capture_selected(principal, [{'record_id':'spec',
            'text_sha256':hashlib.sha256(source['text'].encode()).hexdigest(),'revision':source['revision']}])
        frozen = freeze_castle_snapshot(captured,expected_scope=expected_scope)
    finally:
        providers.close()
    return frozen


def execute_frozen_case(case_id, strategy, *, frozen, config, store, principal, namespace, accounting=None):
    """One explicit fixture job; caller supplies admitted frozen Castle evidence."""
    from prosaic_harness import Harness
    from prosaic_runtime import ExecutionBudget, ExecutionContext
    from prosaic_integration_lab.sue_review.session import SueReviewSession
    from prosaic_integration_lab.sue_review.sources import verify_frozen
    from .requirements_review_v1.cases import load_cases, public_task
    from .requirements_review_v1.contracts import LIMITS, STRATEGIES, digest
    from .requirements_review_v1.execution import _admit, _workflow, sue_settings
    from .requirements_review_v1.host_keys import load_keys
    from .requirements_review_v1.scoring import grade

    if strategy not in STRATEGIES:
        raise ValueError('unknown strategy')
    _admit(config)
    frozen = verify_frozen(frozen)
    capture = frozen['capture']
    expected_owner = {**vars(principal),'namespace':namespace}
    if capture is None or any(capture.get(key) != value for key,value in expected_owner.items()):
        raise PermissionError('source_scope_mismatch')
    case, _, restore = project_case(case_id, frozen)
    task = public_task(case)
    task['evidence'] = deepcopy(frozen)
    sample = uuid.uuid4().hex
    budget = ExecutionBudget(timeout_s=120,max_provider_requests=30,max_reported_tokens=65536,max_tool_calls=0)
    advice = None
    saved_runs = []
    with budget.activate():
        if strategy == 'sue':
            flow = SueReviewSession(sue_settings(LIMITS),store,config,principal,namespace,accounting)
            waiting = flow.start(sample,seed=case['claim'],sources=frozen)
            if waiting['status'] != 'waiting' or budget.provider_requests:
                raise ValueError('SUE admission dispatched unexpectedly')
            done = flow.resume(sample,expected_revision=waiting['revision'],choice='continue')
            if done['status'] != 'completed':
                raise ValueError('SUE fixture did not complete')
            advice = flow.report(sample)
            before = budget.provider_requests
            flow.resume(sample,expected_revision=done['revision'])
            if budget.provider_requests != before:
                raise ValueError('completed SUE redispatched')
            saved = store.load_run(sample)
            if saved.state['inputs']['evidence'] != frozen:
                raise ValueError('SUE source drift')
            saved_runs.append((sample,saved.state))
        run_id = uuid.uuid4().hex
        harness = Harness(_workflow(config,strategy,LIMITS),store=store,run_id=run_id,accounting=accounting,
            context=ExecutionContext(application_id='castle-requirements-v1',project_id=namespace,
                tenant_id=principal.tenant_id,actor_id=principal.actor_id,
                billing_account_id=principal.billing_account_id,request_id=sample))
        harness.run({'publicTask':task,'strategyAdvice':advice})
        state = harness.status().state
        if state['status'] != 'completed':
            raise ValueError('final fixture did not complete')
        before = budget.provider_requests
        harness.resume()
        if budget.provider_requests != before:
            raise ValueError('completed final redispatched')
        if state['inputs']['publicTask']['evidence'] != frozen:
            raise ValueError('final source drift')
        saved_runs.append((run_id,state))
    for saved_id, state in saved_runs:
        for invocation in state['invocations']:
            if store.load_receipt(saved_id,invocation['id']) is None:
                raise ValueError('missing receipt')
    original = load_cases()[case_id]
    score = grade(original,load_keys()[case_id],restore(state['outputs']['final']))
    return dict(profile='castle-requirements-v1',origin='scripted_fixture',caseId=case_id,strategy=strategy,
        caseSha256=digest(original),sourcesSha256=frozen['sourcesSha256'],snapshotDigest=frozen['snapshotDigest'],
        score=score,providerRequests=budget.provider_requests,reportedTokens=budget.reported_tokens,
        usageComplete=budget.usage_complete,replayAdditionalRequests=0,
        runIds=[run for run,_ in saved_runs],
        checkpointSha256=[digest(value) for _,value in saved_runs],
        meaning='Synthetic composition and unchanged-scorer regression only; review quality remains unproven.')
