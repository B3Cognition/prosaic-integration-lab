import httpx
import pytest
from prosaic_integration_lab.billing_delivery import LagoClient, deliver


def event():
    return dict(transaction_id='a'*64,external_subscription_id='sub',code='input_tokens',
                timestamp='1791547200',properties={'tokens':80})


class Store:
    def __init__(self): self.state = 'pending'; self.category = None
    def claim(self,*args,**kwargs):
        if self.state != 'pending' or self.category: return []
        return [dict(key='a'*64,token='fence',payload=event(),attempts=1)]
    def ack(self,key,token): self.state = 'acknowledged'
    def fail(self,key,token,category,delay=None):
        self.state = 'pending' if delay is not None else 'failed'
        self.category = category


@pytest.mark.parametrize('matching',[True,False])
def test_duplicate_requires_exact_remote_evidence(matching):
    def handle(request):
        if request.method == 'POST':
            return httpx.Response(422,json={'error_details':{'transaction_id':['value_already_exist']}})
        stored = {**event(),'timestamp':'2026-10-09T12:00:00Z'}
        if not matching: stored['properties'] = {'tokens':81}
        return httpx.Response(200,json={'event':stored})
    store = Store()
    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        client = LagoClient('http://127.0.0.1:3000/api/v1','fixture-key',http)
        deliver(store,client)
    assert store.state == ('acknowledged' if matching else 'failed')
    assert store.category == (None if matching else 'conflict')


@pytest.mark.parametrize('status,category,retry',[(429,'throttled',True),(503,'server',True),
    (422,'validation',False),(401,'authentication',False)])
def test_failures_preserve_pending_or_visible_failure(status,category,retry):
    store = Store()
    with httpx.Client(transport=httpx.MockTransport(lambda _:httpx.Response(status,json={}))) as http:
        deliver(store,LagoClient('http://127.0.0.1:3000/api/v1','key',http))
    assert store.category == category
    assert store.state == ('pending' if retry else 'failed')


def test_transport_error_is_retryable():
    def handle(request): raise httpx.ConnectError('private-sentinel',request=request)
    store = Store()
    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        deliver(store,LagoClient('http://127.0.0.1:3000/api/v1','key',http))
    assert store.state == 'pending'
    assert store.category == 'transport'


@pytest.mark.parametrize('case',['old-event','changed-period'])
def test_period_gate_rejects_old_usage_and_changed_period(case):
    from prosaic_integration_lab.billing_delivery import DeliveryError
    import time
    now = int(time.time())
    lower,upper = str(now-100),str(now+3600)
    event_time = str(now-101) if case == 'old-event' else str(now)
    remote_from = lower if case == 'old-event' else str(now+100)
    def handle(request):
        return httpx.Response(200,json={'customer_usage':dict(from_datetime=remote_from,to_datetime=upper)})
    mapping = dict(customer='customer',subscription='sub',period_from=lower,period_to=upper)
    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        client = LagoClient('http://127.0.0.1:3000/api/v1','key',http)
        with pytest.raises(DeliveryError,match='period'):
            client.ensure_period(mapping,{**event(),'timestamp':event_time})


def test_authentication_failure_stops_multirow_queue():
    class Queue(Store):
        def claim(self,*args,**kwargs):
            self.claimed += 1
            return [dict(key=str(self.claimed),token='fence',payload=event(),attempts=1)]
    store = Queue();store.claimed = 0
    with httpx.Client(transport=httpx.MockTransport(lambda _:httpx.Response(401,json={}))) as http:
        deliver(store,LagoClient('http://127.0.0.1:3000/api/v1','key',http),limit=5)
    assert store.claimed == 1


def test_retry_exhaustion_is_visible_instead_of_infinite_pending():
    class Exhausted(Store):
        def claim(self,*args,**kwargs):
            if self.category: return []
            return [dict(key='a'*64,token='fence',payload=event(),attempts=6)]
    store = Exhausted()
    with httpx.Client(transport=httpx.MockTransport(lambda _:httpx.Response(503,json={}))) as http:
        deliver(store,LagoClient('http://127.0.0.1:3000/api/v1','key',http))
    assert store.state == 'failed'
    assert store.category == 'exhausted'
