import pytest
import os


@pytest.fixture(autouse=True)
def available_context_pack_sdk(request):
    if request.function.__name__ in {'test_context_pack_sdk_is_explicitly_required',
            'test_candidate_host_payload_cannot_silently_differ','test_required_lane_is_candidate_only'}:return
    from prosaic_integration_lab.context_packs import require_context_pack_sdk
    try:require_context_pack_sdk()
    except (ImportError,ValueError):
        if os.environ.get('CONTEXT_PACKS_REQUIRE_CANDIDATE')=='1':pytest.fail('required context-pack candidate SDK is unavailable')
        pytest.skip('released baseline has no context-pack capability; required candidate lane runs this case')


def test_context_pack_sdk_is_explicitly_required():
    from prosaic_integration_lab.context_packs import require_context_pack_sdk
    from prosaic_runtime import ProsaicRuntime
    if 'frozen_turn_inputs_v1' in ProsaicRuntime.capabilities:require_context_pack_sdk()
    else:
        with pytest.raises(ValueError,match='capability unavailable'):require_context_pack_sdk()


def test_candidate_host_payload_cannot_silently_differ(tmp_path):
    from lab_runner.context_packs import require_candidate_install
    with pytest.raises((ValueError,FileNotFoundError)):require_candidate_install(tmp_path/'absent.json')


def test_scenario_declares_only_selected_sources():
    from prosaic_integration_lab.context_packs import scenario
    bindings, candidates = scenario('service-impact')
    assert {item.source_alias for item in candidates.snapshot.items} == {'task','lookup'}
    assert {slot.source for slot in bindings.specs['impact'].slots} == {'task','lookup'}
    assert 'UNDECLARED-819' not in str(candidates.to_dict())


@pytest.mark.parametrize('outcome,allowed', [('complete',False),('partial',True)])
def test_explicit_completeness_is_preserved(outcome, allowed):
    from prosaic_integration_lab.context_packs import scenario
    _, candidates = scenario('service-impact', outcome=outcome, allow_partial=allowed)
    assert next(source.outcome for source in candidates.snapshot.sources if source.alias=='lookup') == outcome


@pytest.mark.parametrize('outcome', ['partial','unavailable'])
def test_required_incomplete_context_is_refused(outcome):
    from prosaic_integration_lab.context_packs import scenario
    from prosaic_harness import ContextPackError
    with pytest.raises(ContextPackError): scenario('service-impact', outcome=outcome)


def test_conflicting_observations_remain_visible():
    from prosaic_integration_lab.context_packs import scenario
    _, candidates = scenario('service-impact', conflict=True)
    body = str(candidates.variants[-1])
    assert 'revision-a' in body and 'revision-b' in body


def test_required_lane_is_candidate_only():
    from lab_runner.gates import required_modes,CONTEXT_PACK_TRAIN
    import json
    from pathlib import Path
    baseline=json.loads((Path(__file__).resolve().parents[2]/'dependencies/releases.json').read_text())
    candidate={'artifacts':[{'distribution':key,'version':value} for key,value in CONTEXT_PACK_TRAIN.items()]}
    assert 'context-packs' in required_modes(candidate=True,manifest=candidate)
    assert 'context-packs' not in required_modes(candidate=True,manifest=baseline)
    assert 'context-packs' not in required_modes(candidate=False,manifest=baseline)


def test_context_pack_runner_selects_required_tests_and_cleans_owned_stack(tmp_path,monkeypatch):
    import json
    import sys
    from types import SimpleNamespace
    from lab_runner import __main__ as cli
    import lab_runner.context_packs as driver
    from lab_runner.gates import FAILURE_CASES,COUNTS
    selected=[]
    class Stack:
        def __init__(self,*args,**kwargs):
            selected.append(kwargs);self.owner='a'*32;self.directory=tmp_path;self.secrets=tmp_path/'secrets';self.secrets.mkdir()
            (self.secrets/'host.json').write_text('{}');self.baseline_image=None
            self.manifest={'endpoints':{},'images':{},'payload_audit':'verified','candidate_lineage_sha256':'a'*64}
        def start(self):pass
        def start_model(self):raise AssertionError('paid/shared model must not be started')
        def start_replica(self,*args,**kwargs):raise AssertionError('unrelated HTTP replica must not be started')
        def stop(self):selected.append('cleanup')
    def run(command,**kwargs):
        assert 'tests/acceptance/test_context_packs.py' in command
        assert kwargs['env']['LAB_ACCEPTANCE_CONFIG']==str(tmp_path/'secrets/host.json')
        (tmp_path/'junit.xml').write_text('<testsuites><testsuite>'+''.join(
            '<testcase name="'+name+'"/>' for name in FAILURE_CASES['context-packs'])+'</testsuite></testsuites>')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(cli,'OwnedStack',Stack);monkeypatch.setattr(cli.subprocess,'run',run)
    monkeypatch.setattr(driver,'require_candidate_install',lambda manifest:None)
    monkeypatch.setattr(sys,'argv',['lab_runner','test','--mode','context-packs','--candidate','--candidate-manifest',str(tmp_path/'manifest.json')])
    assert cli.main()==0
    assert selected[0]['context_packs'] is True and selected[0]['conversation'] is True and selected[-1]=='cleanup'
    assert COUNTS['context-packs']==12
    assert json.loads((tmp_path/'result.json').read_text())['qualification']=='qualified'
