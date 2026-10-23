def test_installed_cli_quota_rejections_fall_back_and_partial_work_never_replays():
    from lab_runner.native_eval.unified_fallback import run_fallback_acceptance
    report=run_fallback_acceptance()
    assert report['passed'],report
    assert report['origin']=='simulated_provider_rejections'
    assert report['liveInvocations']==0 and report['cleanup']=='verified'
    scenarios={row['scenario']:row for row in report['scenarios']}
    assert set(scenarios)=={'double-quota','persisted-cooldown','claude-tool-partial',
        'codex-tool-partial','claude-text-partial','codex-text-partial','api-tool-partial'}
    clean=scenarios['double-quota']
    assert clean['attempts']==['claude','codex','local']
    assert clean['safeToFallback']==[True,True,False]
    assert clean['fallbacks']==['claude','codex']
    assert clean['nativeCalls']=={'claude':1,'codex':1} and clean['apiRequests']==2
    assert clean['completed'] and clean['taskPassed'] and not clean['partialFile']
    assert scenarios['persisted-cooldown']['nativeCalls']=={'claude':0,'codex':0}
    for name in ('claude-tool-partial','codex-tool-partial','claude-text-partial','codex-text-partial'):
        row=scenarios[name]
        assert not row['completed'] and row['recoveryRequired'] and row['apiRequests']==0
        assert row['safeToFallback'][-1] is False
        assert row['partialFile']==('tool' in name)
        assert row['originalTaskOutput']
    assert scenarios['claude-tool-partial']['nativeCalls']=={'claude':1,'codex':0}
    assert scenarios['codex-tool-partial']['nativeCalls']=={'claude':1,'codex':1}
    assert scenarios['api-tool-partial']['nativeCalls']=={'claude':0,'codex':0}
    assert scenarios['api-tool-partial']['apiRequests']==2
    assert scenarios['api-tool-partial']['recoveryRequired']
