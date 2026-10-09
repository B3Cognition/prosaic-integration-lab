"""Owner-authenticated recovery with explicit revision/action and no retry loop."""
from decimal import Decimal,InvalidOperation
import json
import os
import re
import ssl
from urllib.parse import urlsplit
import httpx

class RecoveryError(ValueError): pass

def plan_action(snapshot,action,revision,acknowledge):
    if snapshot.get('status') == 'start_uncertain':
        raise RecoveryError('operator_reconciliation_required')
    if not revision or snapshot.get('revision') != revision:
        raise RecoveryError('revision_conflict')
    if action in {'approve','reject'}:
        review = snapshot.get('review')
        if not review: raise RecoveryError('approval_view_unavailable')
        if review.get('revision') != revision: raise RecoveryError('revision_conflict')
        if snapshot.get('status') != 'waiting' or action not in snapshot.get('choices',[]):
            raise RecoveryError('no_recovery_action')
        return {'expected_revision':revision,'choice':action}
    if action == 'retry':
        if snapshot.get('recovery_status') != 'retry_consent_required':
            raise RecoveryError('no_recovery_action')
        if not acknowledge: raise RecoveryError('effect_risk_acknowledgement_required')
        return {'expected_revision':revision,'retry_interrupted':True}
    if action == 'resume':
        reason = snapshot.get('recovery_status')
        if reason is not None: raise RecoveryError(reason)
        if snapshot.get('status') != 'running': raise RecoveryError('no_recovery_action')
        return {'expected_revision':revision}
    raise RecoveryError('no_recovery_action')

def run_view(data,run_id):
    statuses = {'running','waiting','blocked','completed','start_uncertain'}
    if (not isinstance(data,dict) or data.get('run_id') != run_id or data.get('status') not in statuses or
        (data.get('revision') is not None and (type(data['revision']) is not str or not 1 <= len(data['revision']) <= 512))):
        raise RecoveryError('malformed_response')
    reason = data.get('recovery_status')
    if reason not in {None,'retry_consent_required','operator_reconciliation_required',
                      'usage_reconciliation_required','budget_exhausted'}:
        raise RecoveryError('malformed_response')
    result = {'run_id':run_id,'status':data['status'],'revision':data.get('revision'),'recovery_status':reason}
    result['choices'] = [choice for choice in data.get('choices',[]) if choice in {'approve','reject'}]
    review = data.get('review')
    if review is not None:
        if (not isinstance(review,dict) or review.get('revision') != result['revision'] or
            review.get('question') not in {'Approve this fixture output?','Approve this fixture request?'}):
            raise RecoveryError('malformed_response')
        output = review.get('result')
        if output is not None and (not isinstance(output,dict) or set(output) != {'result'} or
            type(output['result']) is not str or len(output['result']) > 256):
            raise RecoveryError('malformed_response')
        result['review'] = {'revision':review['revision'],'question':review['question'],'result':output}
    return result

def usage_view(data):
    if not isinstance(data,dict): raise RecoveryError('malformed_response')
    result = {}
    for name in ('total_calls','complete_calls','unresolved_calls','quarantined_calls','unsupported_calls',
                 'partial_calls','unavailable_assessment_calls'):
        if type(data.get(name)) is not int or data[name] < 0: raise RecoveryError('malformed_response')
        result[name] = data[name]
    for name in ('fully_costed','billing_eligible'):
        if type(data.get(name)) is not bool: raise RecoveryError('malformed_response')
        result[name] = data[name]
    amounts = data.get('estimated_amounts')
    if not isinstance(amounts,dict) or len(amounts) > 16: raise RecoveryError('malformed_response')
    result['estimated_amounts'] = {}
    for currency,amount in amounts.items():
        if type(currency) is not str or not re.fullmatch('[A-Z]{3}',currency) or type(amount) is not str or len(amount) > 64:
            raise RecoveryError('malformed_response')
        try: value = Decimal(amount)
        except InvalidOperation: raise RecoveryError('malformed_response') from None
        if not value.is_finite() or value < 0: raise RecoveryError('malformed_response')
        result['estimated_amounts'][currency] = amount
    return result

def request(client,method,path,**kwargs):
    with client.stream(method,path,**kwargs) as response:
        if response.status_code != 200:
            raise RecoveryError('http_'+str(response.status_code))
        content = bytearray()
        for chunk in response.iter_bytes():
            if len(content)+len(chunk) > 65536: raise RecoveryError('malformed_response')
            content.extend(chunk)
        try: return json.loads(content)
        except (ValueError,UnicodeError): raise RecoveryError('malformed_response') from None

def cli(args):
    mutation_attempted = False
    mutation_confirmed = False
    try:
        parsed = urlsplit(args.url or '')
        if parsed.scheme != 'https':
            if not args.lab_http or parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1','localhost','::1'}:
                raise RecoveryError('https_required')
        if not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
            raise RecoveryError('invalid_origin')
        if type(args.run_id) is not str or not re.fullmatch('[0-9a-f]{32}',args.run_id):
            raise RecoveryError('invalid_run_id')
        token = os.environ.get(args.token_env)
        if not token: raise RecoveryError('token_environment_missing')
        context = ssl.create_default_context(cafile=args.ca_file)
        with httpx.Client(base_url=args.url.rstrip('/')+'/',headers={'Authorization':'Bearer '+token},
                verify=context,trust_env=False,timeout=10,follow_redirects=False) as client:
            path = 'runs/'+args.run_id
            snapshot = run_view(request(client,'GET',path),args.run_id)
            if args.action != 'inspect':
                payload = plan_action(snapshot,args.action,args.expected_revision,args.acknowledge_effect_risk)
                mutation_attempted = True
                snapshot = run_view(request(client,'POST',path+'/resume',json=payload),args.run_id)
                mutation_confirmed = True
            usage = usage_view(request(client,'GET',path+'/usage'))
        print(json.dumps({'event':'recovery_'+('inspected' if args.action == 'inspect' else 'applied'),
                          'run':snapshot,'usage':usage}))
        return 0
    except RecoveryError as error:
        result = {'event':'recovery_failed','reason':str(error)}
        if mutation_attempted:
            result['mutation_outcome'] = 'confirmed' if mutation_confirmed else 'unknown'
        print(json.dumps(result))
        return 1
    except Exception:
        result = {'event':'recovery_failed','reason':'transport_or_protocol_failure'}
        if mutation_attempted:
            result['mutation_outcome'] = 'confirmed' if mutation_confirmed else 'unknown'
        print(json.dumps(result))
        return 1
