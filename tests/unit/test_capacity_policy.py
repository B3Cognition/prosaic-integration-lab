import pytest
from prosaic_integration_lab.capacity import policy

def test_capacity_default_is_bounded_and_preserves_current_pool_ceiling():
    assert policy({})=={'writes':2,'reads':4,'per_tenant':2,'max_runs':10000,'max_tenant_runs':10000}

def test_lowered_global_limits_have_coherent_default_tenant_limits():
    result=policy({'writes':1,'max_runs':3})
    assert result['per_tenant']==1 and result['max_tenant_runs']==3

@pytest.mark.parametrize('value',[{'writes':3},{'reads':5},{'per_tenant':3},
    {'writes':True},{'max_runs':10001},{'max_runs':2,'max_tenant_runs':3},{'unknown':1}])
def test_untested_or_incoherent_capacity_is_rejected_before_resources(value):
    with pytest.raises(ValueError): policy(value)

def test_configurable_tenant_quota_can_reserve_capacity_for_other_tenants():
    import threading
    from fastapi import HTTPException
    from prosaic_integration_lab.admission import Admission
    gate=threading.Event(); admission=Admission(2,per_tenant=1)
    try:
        first=admission.submit(lambda:gate.wait(2),key=('tenant-a','alice'))
        with pytest.raises(HTTPException): admission.submit(lambda:None,key=('tenant-a','bob'))
        second=admission.submit(lambda:gate.wait(2),key=('tenant-b','carol'))
        assert len(admission.owners)==2
    finally: gate.set(); admission.close()
