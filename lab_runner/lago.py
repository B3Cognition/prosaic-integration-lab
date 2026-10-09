"""Disposable pinned Lago fixture and independent quantity/charge reconciliation."""
from datetime import datetime,timezone,timedelta
from decimal import Decimal,ROUND_HALF_UP
import json
import secrets
import time
from urllib.parse import quote
import httpx
from prosaic_integration_lab.billing_delivery import LagoClient,timestamp
from prosaic_integration_lab.billing_projection import account_scope,digest,DIMENSIONS
from prosaic_integration_lab.billing_store import BillingStore
from .stack import ROOT,command,EngineError

# Deliberately fixture retail rates, unrelated to Runtime's provider-cost estimates.
RATES = {'input_tokens':'0.002','cached_input_tokens':'0.0005','output_tokens':'0.008'}


def endpoint(engine,identifier):
    state = json.loads(command(engine,'inspect',identifier))[0]
    return 'http://127.0.0.1:'+state['NetworkSettings']['Ports']['3000/tcp'][0]['HostPort']+'/api/v1'


def wait_ready(config,deadline_seconds=180):
    deadline = time.monotonic()+deadline_seconds
    with httpx.Client() as http:
        client = LagoClient(config['url'],config['key'],http)
        while time.monotonic() < deadline:
            try:
                if client.request('GET','/billable_metrics').status_code == 200: return
            except Exception: pass
            time.sleep(0.5)
    raise EngineError('Lago readiness timeout')


def start(stack,*,pull=True):
    manifest = json.loads((ROOT/'dependencies/lago.json').read_text())
    image = manifest['image']
    if pull: command(stack.engine,'pull',image)
    name = 'prosaic-lab-'+stack.owner+'-lago'
    key = secrets.token_hex(24)
    env = dict(LAGO_CREATE_ORG='true',LAGO_ORG_USER_EMAIL='fixture@prosaic.invalid',
        LAGO_ORG_USER_PASSWORD=secrets.token_hex(24),LAGO_ORG_NAME='Prosaic fixture',LAGO_ORG_API_KEY=key,
        LAGO_DISABLE_PDF_GENERATION='true',LAGO_DISABLE_SEGMENT='true',
        LAGO_API_URL='http://127.0.0.1:3000',LAGO_FRONT_URL='http://127.0.0.1',API_URL='http://127.0.0.1:3000')
    envfile = stack._secret('lago.env',''.join(k+'='+v+'\n' for k,v in env.items()))
    volume = stack._create('volume',name,'volume','create','--label','io.prosaic.lab.owner='+stack.owner,name)
    identifier = stack._create('container',name,'run','-d','--name',name,'--label',
        'io.prosaic.lab.owner='+stack.owner,'--network',stack.manifest['network_id'],
        '--env-file',str(envfile),'-p','127.0.0.1::3000','-v',volume+':/data',image)
    config = dict(url=endpoint(stack.engine,identifier),key=key,id=identifier,engine=stack.engine)
    stack._secret('lago.json',json.dumps(config))
    stack.manifest['lago_id'] = identifier
    stack.manifest['images']['lago'] = image
    stack.manifest['lago_source_commit'] = manifest['source_commit']
    stack.manifest['endpoints']['lago'] = config['url']
    stack._save()
    wait_ready(config)
    return config


def api(client,method,path,body=None):
    response = client.request(method,path,**({'json':body} if body is not None else {}))
    if not 200 <= response.status_code < 300:
        raise ValueError('Lago fixture API failure '+str(response.status_code))
    return response.json()


def seed(config,reservations,store):
    mappings = {}
    with httpx.Client() as http:
        client = LagoClient(config['url'],config['key'],http)
        metrics = {}
        for code in DIMENSIONS:
            response = client.request('GET','/billable_metrics/'+code)
            if response.status_code == 404:
                metric = api(client,'POST','/billable_metrics',{'billable_metric':dict(
                    name=code,code=code,aggregation_type='sum_agg',field_name='tokens')})['billable_metric']
            elif response.status_code == 200: metric = response.json()['billable_metric']
            else: raise ValueError('Lago metric lookup failed')
            metrics[code] = metric['lago_id']
        response = client.request('GET','/plans/prosaic-fixture-v1')
        if response.status_code == 404:
            api(client,'POST','/plans',{'plan':dict(name='Prosaic fixture',code='prosaic-fixture-v1',
                interval='monthly',amount_cents=0,amount_currency='USD',pay_in_advance=False,
                charges=[dict(billable_metric_id=metrics[code],charge_model='standard',pay_in_advance=False,
                    properties={'amount':RATES[code]}) for code in DIMENSIONS])})
        elif response.status_code != 200: raise ValueError('Lago plan lookup failed')
        for r in reservations:
            key = (r['namespace'],r['environment'],r['tenant_id'],r['billing_account_id'])
            if key in mappings: continue
            scope = digest(account_scope(r))
            customer,subscription = 'customer-'+scope,'sub-'+scope
            existing = client.request('GET','/subscriptions/'+subscription)
            if existing.status_code == 404:
                api(client,'POST','/customers',{'customer':dict(external_id=customer,name='Fixture account',
                    currency='USD',timezone='UTC')})
                api(client,'POST','/subscriptions',{'subscription':dict(external_customer_id=customer,
                    external_id=subscription,plan_code='prosaic-fixture-v1',billing_time='anniversary',
                    subscription_at=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat())})
            elif existing.status_code != 200: raise ValueError('Lago subscription lookup failed')
            usage = api(client,'GET','/customers/'+customer+'/current_usage?external_subscription_id='+subscription+'&apply_taxes=false')['customer_usage']
            mapping = dict(customer=customer,subscription=subscription,revision='fixture-v1',
                period_from=str(timestamp(usage['from_datetime'])),period_to=str(timestamp(usage['to_datetime'])))
            mappings[key] = store.mapping(scope,mapping)
    return mappings


def reconcile(config,mapping,quantities,timeout=30):
    expected_cents = sum((Decimal(quantities[c])*Decimal(RATES[c])*100).quantize(Decimal(1),rounding=ROUND_HALF_UP)
                         for c in DIMENSIONS)
    deadline = time.monotonic()+timeout
    with httpx.Client() as http:
        client = LagoClient(config['url'],config['key'],http)
        while time.monotonic() < deadline:
            response = client.request('GET','/customers/'+quote(mapping['customer'],safe='')+'/current_usage',
                params={'external_subscription_id':mapping['subscription'],'apply_taxes':'false'})
            if response.status_code != 200: raise ValueError('Lago usage lookup failed')
            usage = response.json()['customer_usage']
            if ((timestamp(usage['from_datetime']),timestamp(usage['to_datetime'])) !=
                    (timestamp(mapping['period_from']),timestamp(mapping['period_to']))):
                raise ValueError('Lago fixture period changed')
            actual = {c:Decimal(0) for c in DIMENSIONS}
            for charge in usage['charges_usage']:
                code = charge['billable_metric']['code']
                if code in actual: actual[code] += Decimal(charge['units'])
            if actual == {c:Decimal(quantities[c]) for c in DIMENSIONS}:
                if Decimal(usage['amount_cents']) != expected_cents or usage['currency'] != 'USD':
                    raise ValueError('Lago charge reconciliation failed')
                return {'quantities':{c:str(actual[c]) for c in DIMENSIONS},'amount_cents':str(expected_cents)}
            time.sleep(0.3)
    raise ValueError('Lago quantity reconciliation timeout')
