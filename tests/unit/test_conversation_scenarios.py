import subprocess
import sys


def test_runner_configuration_separates_tiers_and_host_authority():
    from lab_runner.conversation_scenarios import conversation_configuration
    settings=conversation_configuration('owned-fixture')
    assert settings['max_sessions']==128 and settings['max_owner_sessions']==16
    assert settings['tenants']['tenant-a']['enabled'] is True
    assert settings['tenants']['tenant-b']['enabled'] is True
    assert {bundle['model_tier'] for bundle in settings['bundles']}=={'balanced','strong'}
    assert len({bundle['model'] for bundle in settings['bundles']})==2
    assert all(bundle['fixture_effects'] is True for bundle in settings['bundles'])
    assert len({bundle['operation_namespace'] for bundle in settings['bundles']})==2
    assert all(len(bundle['operation_namespace'].encode())<=128 for bundle in settings['bundles'])


def test_runner_lists_explicit_conversation_mode():
    result=subprocess.run([sys.executable,'-m','lab_runner','--help'],capture_output=True,text=True,timeout=15)
    assert result.returncode==0 and 'conversation' in result.stdout


def test_candidate_conversation_lane_requires_explicit_manifest_before_engine():
    result=subprocess.run([sys.executable,'-m','lab_runner','test','--mode','conversation','--candidate'],
        capture_output=True,text=True,timeout=15)
    assert result.returncode==2 and 'explicit complete SDK manifest' in result.stderr
