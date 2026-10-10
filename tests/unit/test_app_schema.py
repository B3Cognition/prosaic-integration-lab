from copy import deepcopy
import pytest
from prosaic_integration_lab import app_schema


def catalog():
    tables = [('schema_version','p','r'),('runs','p','r')]
    fields = ['run_id','tenant_id','actor_id','billing_account_id','idempotency_key','request_hash',
              'request','workflow','assets_hash','phase','namespace','environment']
    columns = [('schema_version','version','integer',True)] + [
        ('runs',name,'jsonb' if name == 'request' else 'text',True) for name in fields]
    constraints = [('schema_version','PRIMARY KEY (version)',True,'p'),
        ('runs','PRIMARY KEY (run_id)',True,'p'),
        ('runs','UNIQUE (tenant_id, actor_id, idempotency_key)',True,'u'),
        ('runs',"CHECK ((phase = ANY (ARRAY['reserved'::text, 'starting'::text, 'started'::text])))",True,'c')]
    return tables, columns, constraints


def test_archived_application_contract_requires_explicit_version():
    app_schema.validate_catalog(*catalog(), version=2)
    with pytest.raises(ValueError):
        app_schema.validate_catalog(*catalog())


@pytest.mark.parametrize('fault', ['unique','nullability','type','unlogged','phase','unvalidated'])
def test_wrong_application_contract_fails_without_echoing_values(fault):
    tables, columns, constraints = deepcopy(catalog())
    if fault == 'unique': constraints.pop(2)
    elif fault == 'nullability': columns[1] = ('runs','run_id','text',False)
    elif fault == 'type': columns[1] = ('runs','run_id','PRIVATE_TYPE',True)
    elif fault == 'unlogged': tables[1] = ('runs','u','r')
    elif fault == 'phase': constraints[-1] = ('runs','CHECK (TRUE)',True,'c')
    else: constraints[0] = ('schema_version','PRIMARY KEY (version)',False,'p')
    with pytest.raises(ValueError) as error:
        app_schema.validate_catalog(tables,columns,constraints,version=2)
    assert 'PRIVATE_TYPE' not in str(error.value)
