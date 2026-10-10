"""A bounded synthetic client walkthrough of the public native HTTP protocol.

The owned runner supplies private authentication and bindings. This client
submits logical references and user inputs, then retains only checked fixture
fields. It does not retry uncertain operations or export host configuration.
"""
from copy import deepcopy
import re
import uuid

import httpx

from .native_scenarios import approved_proposal


DECISION = {'type':'object','properties':{'confirmed':{'type':'boolean'}},
            'required':['confirmed'],'additionalProperties':False}
REVIEW = {'review':{'entity_id':'sample-1','approved':True}}


def capture_native(config):
    """Discover, admit, start on A, inspect and approve on B; no paid calls."""
    headers = {}
    for actor in ('alice','bob'):
        token = next(token for token, principal in config['principals'].items()
                     if principal['actor_id'] == actor)
        headers[actor] = {'Authorization':'Bearer '+token}

    def require(condition):
        if not condition:
            raise ValueError('native demonstration evidence mismatch')

    def identifier(value, size):
        require(type(value) is str and re.fullmatch('[0-9a-f]{'+str(size)+'}',value) is not None)
        return value

    with httpx.Client(timeout=35) as client:
        def request(method, path, *, worker='a', actor='alice', status=200, key=None, body=None):
            authentication = dict(headers[actor])
            if key is not None:
                authentication['Idempotency-Key'] = key
            response = client.request(method,config[worker]+path,headers=authentication,json=body)
            require(response.status_code == status)
            return response.json()

        def calls():
            response = client.get(config['model']+'/stats')
            response.raise_for_status()
            count = response.json()['calls']
            require(type(count) is int and count >= 0)
            return count

        before = calls()
        try:
            client.post(config['model']+'/control',json={'scenario':'native','maximum_calls':2}).raise_for_status()
            catalogue = request('GET','/workflow-catalogue')
            manifest = catalogue['manifest']
            require(manifest.get('allowAgentComposition') is True)
            require({'finder','reviewer'} <= set(manifest['agents']))
            require({'found','reviewed','decision'} <= set(manifest['schemas']))
            require('approved' in manifest['validators'])
            require(type(catalogue['proposal_schema']) is dict)

            proposal_key = uuid.uuid4().hex
            proposal_body = approved_proposal()
            proposal = request('POST','/workflow-proposals',key=proposal_key,body=proposal_body)
            require(request('POST','/workflow-proposals',worker='b',key=proposal_key,body=proposal_body) == proposal)
            proposal_id = identifier(proposal['proposal_id'],32)
            require(calls() == before)

            run_key = uuid.uuid4().hex
            run_body = {'proposal_id':proposal_id,'inputs':{'entity_id':'sample-1'}}
            run = request('POST','/native-runs',key=run_key,body=run_body)
            require(run['status'] == 'waiting')
            run_id = identifier(run['run_id'],32)
            revision = identifier(run['revision'],64)
            route = '/runs/'+run_id
            interaction = run['interaction']
            require(interaction['runId'] == run_id and interaction['revision'] == revision)
            require(interaction['stepId'] == 'confirm' and set(interaction['choices']) == {'accept','reject'})
            require(interaction['question'] == 'Accept the synthetic review?')
            require(interaction['reviewOutputs'] == REVIEW and interaction['responseSchema'] == DECISION)
            schema_digest = identifier(interaction['responseSchemaDigest'],64)
            require(calls() == before+2)
            require(request('POST','/native-runs',worker='b',key=run_key,body=run_body) == run)
            require(request('GET',route,worker='b') == run)
            require(calls() == before+2)

            response = {'expected_revision':revision,'choice':'accept','response':{'confirmed':True}}
            request('POST',route+'/resume',worker='b',status=422,
                    body={**response,'response':{'confirmed':'invalid'}})
            require(request('GET',route,worker='b') == run and calls() == before+2)
            request('POST',route+'/resume',worker='b',status=409,
                    body={**response,'expected_revision':'stale'})
            require(request('GET',route,worker='b') == run and calls() == before+2)

            # Bob belongs to the same tenant, but cannot use Alice's proposal,
            # reservation, interaction or usage. The host derives ownership.
            request('POST','/native-runs',worker='b',actor='bob',status=404,
                    key=uuid.uuid4().hex,body=run_body)
            for suffix in ('','/usage'):
                request('GET',route+suffix,worker='b',actor='bob',status=404)
            request('POST',route+'/resume',worker='b',actor='bob',status=404,body=response)
            require(calls() == before+2)

            completed = request('POST',route+'/resume',worker='b',body=response)
            require(completed['run_id'] == run_id and completed['status'] == 'completed')
            identifier(completed['revision'],64)
            usage = request('GET',route+'/usage',worker='b')
            require(type(usage.get('total_calls')) is int and usage['total_calls'] == 2)
            require(type(usage.get('complete_calls')) is int and usage['complete_calls'] == 2)
            require(type(usage.get('unresolved_calls')) is int and usage['unresolved_calls'] == 0)
            require(usage.get('billing_eligible') is False and calls() == before+2)
        finally:
            client.post(config['model']+'/control',json={}).raise_for_status()
        require(calls() == before+2)

    # Curate from validated synthetic values. Never serialize raw replies,
    # provider messages, references, run state or private host configuration.
    return {'version':1,'fixture':'native-workflow','status':'completed',
        'catalogue':{'agents':['finder','reviewer'],'schemas':['decision','found','reviewed'],
                     'validators':['approved']},
        'steps':[{'id':name,'kind':step['kind'],**{key:step[key] for key in ('agent','schema','response_schema') if key in step}}
                 for name,step in proposal_body['definition']['steps'].items()],
        'proposal_id':proposal_id,'run_id':run_id,
        'interaction':{'runId':run_id,'revision':revision,'stepId':'confirm',
            'question':'Accept the synthetic review?','choices':['accept','reject'],
            'responseSchemaDigest':schema_digest,'responseSchema':deepcopy(DECISION),
            'reviewOutputs':deepcopy(REVIEW)},
        'checks':{'admission_without_model_calls':True,'proposal_replay':True,'start_replay':True,
            'invalid_response_unchanged':True,'stale_revision_unchanged':True,
            'owner_isolation':True,'resume_without_model_calls':True},
        'usage':{'total_calls':2,'complete_calls':2,'unresolved_calls':0,'billing_eligible':False},
        'independent_model_calls':2}
