"""Finite event delivery with exact duplicate recovery and fenced acknowledgements."""
from datetime import datetime,timezone
from decimal import Decimal
from urllib.parse import quote,urlparse
import httpx
import time


class DeliveryError(RuntimeError):
    def __init__(self,category,retry=False):
        super().__init__(category)
        self.category,self.retry = category,retry


def timestamp(value):
    try:
        return Decimal(str(value))
    except Exception:
        t = datetime.fromisoformat(value.replace('Z','+00:00'))
        if t.tzinfo is None: raise ValueError('timestamp timezone missing')
        d = t.astimezone(timezone.utc)-datetime(1970,1,1,tzinfo=timezone.utc)
        return Decimal(d.days*86400+d.seconds)+Decimal(d.microseconds)/Decimal(1000000)


class LagoClient:
    def __init__(self,url,key,http):
        parsed = urlparse(url)
        if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.username or parsed.password:
            raise ValueError('Lago fixture must use loopback HTTP')
        self.url,self.key,self.http = url.rstrip('/'),key,http
        self.periods = {}

    def request(self,method,path,**kwargs):
        try:
            response = self.http.request(method,self.url+path,
                headers={'Authorization':'Bearer '+self.key},timeout=5,follow_redirects=False,**kwargs)
        except httpx.HTTPError:
            raise DeliveryError('transport',True) from None
        if response.status_code in (401,403): raise DeliveryError('authentication')
        if response.status_code == 429: raise DeliveryError('throttled',True)
        if response.status_code >= 500: raise DeliveryError('server',True)
        return response

    def ensure_period(self,mapping,event):
        try:
            lower,upper = timestamp(mapping['period_from']),timestamp(mapping['period_to'])
            when = timestamp(event['timestamp'])
            if not lower <= when <= upper or timestamp(datetime.now(timezone.utc).isoformat()) > upper:
                raise DeliveryError('period')
            key = mapping['subscription']
            cached = self.periods.get(key)
            if cached is None or cached[0] < time.monotonic():
                response = self.request('GET','/customers/'+quote(mapping['customer'],safe='')+'/current_usage',
                    params={'external_subscription_id':key,'apply_taxes':'false'})
                if response.status_code != 200: raise DeliveryError('validation')
                usage = response.json()['customer_usage']
                actual = (timestamp(usage['from_datetime']),timestamp(usage['to_datetime']))
                cached = (time.monotonic()+1,actual)
                self.periods[key] = cached
            if cached[1] != (lower,upper): raise DeliveryError('period')
        except DeliveryError: raise
        except Exception: raise DeliveryError('period') from None

    def send(self,event):
        response = self.request('POST','/events',json={'event':event})
        if 200 <= response.status_code < 300: return
        try:
            duplicate = response.status_code == 422 and 'value_already_exist' in response.json().get('error_details',{}).get('transaction_id',[])
        except Exception: duplicate = False
        if not duplicate: raise DeliveryError('validation')
        response = self.request('GET','/events/'+quote(event['transaction_id'],safe=''),
            params={'external_subscription_id':event['external_subscription_id']})
        if response.status_code != 200: raise DeliveryError('validation')
        try:
            remote = response.json()['event']
            matches = all(remote[k] == event[k] for k in ('transaction_id','external_subscription_id','code','properties'))
            matches = matches and timestamp(remote['timestamp']) == timestamp(event['timestamp'])
        except Exception: matches = False
        if not matches: raise DeliveryError('conflict')


def deliver(store,client,limit=30,*,scope=None,verify=None):
    processed = 0
    # One claim per HTTP call avoids expiring later rows in a slow local batch.
    for _ in range(limit):
        rows = store.claim(1,30,scope=scope)
        if not rows: break
        row = rows[0]
        try:
            if verify:
                verify(row)
            if 'mapping' in row:
                client.ensure_period(row['mapping'],row['payload'])
            client.send(row['payload'])
        except DeliveryError as error:
            delay = min(30,2**min(row['attempts'],5)) if error.retry and row['attempts'] < 6 else None
            category = 'exhausted' if error.retry and delay is None else error.category
            store.fail(row['key'],row['token'],category,delay)
            if error.category in {'authentication','conflict','period'}: break
        else:
            store.ack(row['key'],row['token'])
        processed += 1
    return processed
