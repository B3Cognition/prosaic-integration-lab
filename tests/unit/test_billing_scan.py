from prosaic_integration_lab.billing_scan import scan
from test_billing_projection import fixture


def test_pagination_and_late_observation_rescan():
    call,reservation,mapping = fixture()
    class Metadata:
        def billing_reservations(self): return [reservation]
    class Recorder:
        def calls(self,limit,offset,**filters):
            assert filters == dict(application_id='integration-lab',tenant_id='tenant-a',actor_id='alice',
                billing_account_id='account',request_id='run-a',run_id='run-a')
            rows = []
            for i in range(offset,min(offset+limit,1001)):
                c = {**call,'intent':{**call['intent'],'provider_call_id':str(i)}}
                if i == 0 and not observed[0]: c = {**c,'measurement_state':'unresolved','observation':None}
                rows.append(c)
            return rows
    class Store:
        def enqueue(self,p):
            values[p['source']] = p
    observed,values = [False],{}
    factory = lambda namespace,environment: Recorder()
    mappings = {('lab-x','sandbox','tenant-a','account'):mapping}
    scan(Metadata(),factory,Store(),mappings)
    assert len(values) == 1001
    assert sum(p['exclusion'] == 'unresolved' for p in values.values()) == 1
    observed[0] = True
    scan(Metadata(),factory,Store(),mappings)
    assert len(values) == 1001
    assert sum(len(p['events']) for p in values.values()) == 3003
