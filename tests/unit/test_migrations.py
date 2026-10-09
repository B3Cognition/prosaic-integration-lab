import pytest
from prosaic_integration_lab.migrations import scope_plan

RUN = 'a'*32

def test_scope_plan_requires_each_existing_run_exactly_once():
    assert scope_plan([RUN],[{'run_id':RUN,'namespace':'archived-deployment','environment':'sandbox'}]) == {
        RUN:('archived-deployment','sandbox')}

def test_empty_legacy_database_requires_no_inferred_scope():
    assert scope_plan([],None) == {}

@pytest.mark.parametrize('records',[None,[],
    [{'run_id':'b'*32,'namespace':'other','environment':'sandbox'}],
    [{'run_id':RUN,'namespace':'x','environment':'sandbox'}]*2,
    [{'run_id':RUN,'namespace':'x','environment':'sandbox','billing_account_id':'SPOOF'}],
    [{'run_id':RUN,'namespace':'../x','environment':'sandbox'}],
    [{'run_id':RUN,'namespace':'x','environment':'unknown'}]])
def test_scope_plan_refuses_ambiguous_or_identity_mutating_backfill(records):
    with pytest.raises(ValueError,match='scope'):
        scope_plan([RUN],records)
