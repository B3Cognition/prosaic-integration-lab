def test_recovery_does_not_redispatch_or_reexecute(tmp_path):
    from lab_runner.quality.recovery import run_recovery_cases
    results=run_recovery_cases(tmp_path)
    assert [r['caseId'] for r in results]==['saved-receipt','missing-receipt','schema-failure']
    assert all(r['passed'] for r in results),results
    assert all(r['additionalProviderRequests']==0 for r in results)
    assert all(r['additionalToolCalls']==0 for r in results)


def test_rebuilt_materials_validate_saved_receipt_from_persisted_journal(tmp_path):
    from lab_runner.quality.recovery import FaultStore,InjectedInterruption
    from lab_runner.quality.execution import materials,CASE_LIMITS
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.suite import load_suite,public_case
    from prosaic_harness import Harness,FileRunStore
    case=load_suite()['cases'][0];journal_path=tmp_path/'journal.json'
    with fixture_provider() as provider:
        workflow,_,on_event=materials(case,provider.config,'fixture','rebuilt',CASE_LIMITS,journal_path=journal_path)
        store=FileRunStore(tmp_path/'store',namespace='rebuilt');store.initialize()
        try:
            first=Harness(workflow,store=FaultStore(store,'after'),run_id='d'*32,on_event=on_event)
            try:first.run(public_case(case))
            except InjectedInterruption:pass
            before=provider.requests
            rebuilt,_,events=materials(case,provider.config,'fixture','rebuilt',CASE_LIMITS,journal_path=journal_path)
            state=Harness(rebuilt,store=store,run_id='d'*32,on_event=events).resume()
            assert state['status']=='completed'
            assert provider.requests==before==2
        finally:store.close()
