"""A synthetic quality comparison must report lost information honestly."""
def test_context_configuration_keeps_old_tenants_and_adds_explicit_context_bindings():
    from lab_runner.conversation_scenarios import conversation_configuration
    config=conversation_configuration('owned-context',context_assembly=True)
    assert config['tenants']['tenant-a']['binding_version']=='balanced-v1'
    versions={item['version']:item for item in config['bundles']}
    assert versions['context-full-v1']['context_policy']['mode']=='fullHistory'
    assert versions['context-omit-v1']['context_policy']['mode']=='omitOldestTurns'
    assert versions['context-omit-v1']['interpretation_model']=='test-model-strong'
    assert versions['context-omit-v1']['interpretation_context_policy']['counterIdentity']=='lab-synthetic-byte-strong-v1'


def test_quality_classifier_distinguishes_lost_history_and_safe_approval_denial():
    from lab_runner.context_scenarios import classify_quality
    assert classify_quality('older-preference',{'status':'completed','answer':'Preference recorded.'})=='lostContext'
    assert classify_quality('recent-preference',{'status':'completed','answer':'Your city is Prague.'})=='completed'
    assert classify_quality('mandatory-interaction',{'pendingInteraction':{'stepId':'confirm-b'}})=='completed'
    assert classify_quality('historical-injection',{'failureCode':'confirmationRequired'})=='safeDenial'
