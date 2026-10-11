import pytest


def test_separate_schema_requires_exact_logged_contract():
    from prosaic_integration_lab.conversation_schema import COLUMNS,CONSTRAINTS,validate_catalog
    tables=[(table,'p','r') for table in COLUMNS]
    columns=[(table,name,*kind) for table,fields in COLUMNS.items() for name,kind in fields.items()]
    constraints=[(table,definition,True,'c') for table,definitions in CONSTRAINTS.items() for definition in definitions]
    validate_catalog(tables,columns,constraints)
    with pytest.raises(ValueError):validate_catalog([(table,'u','r') for table in COLUMNS],columns,constraints)
    with pytest.raises(ValueError):validate_catalog(tables,columns[:-1],constraints)
    with pytest.raises(ValueError):validate_catalog(tables,columns,constraints[:-1])
    with pytest.raises(ValueError):validate_catalog(tables,columns,[(table,definition,False,kind) for table,definition,_,kind in constraints])


def test_existing_app_schema_contract_stays_version_three():
    from prosaic_integration_lab.app_schema import COLUMNS
    assert 'sessions' not in COLUMNS
    assert set(COLUMNS)=={'schema_version','runs','proposals','native_runs','tool_operations'}
