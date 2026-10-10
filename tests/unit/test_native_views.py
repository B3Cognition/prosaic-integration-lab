def test_native_interaction_filters_selected_fields_and_schema_opt_in():
    from prosaic_integration_lab.views import public_native_interaction
    source = {'version':1,'runId':'r','revision':'v','stepId':'confirm','question':'Accept?',
        'choices':['accept'],'deadline':None,'responseSchemaDigest':'digest',
        'responseSchema':{'type':'object'},'reviewOutputs':{'review':{'entity_id':'synthetic',
        'approved':True,'private':'PRIVATE_OUTPUT'},'find':{'entity_id':'PRIVATE_FIND'}}}
    view = public_native_interaction(source, include_response_schema=False)
    assert view['reviewOutputs'] == {'review':{'entity_id':'synthetic','approved':True}}
    assert 'responseSchema' not in view
    assert 'PRIVATE' not in str(view)
    assert public_native_interaction(source,include_response_schema=True)['responseSchema'] == {'type':'object'}
