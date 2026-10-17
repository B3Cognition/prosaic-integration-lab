import json
import pytest


def arguments(feedback):
    return json.dumps(dict(request=dict(caseId='control',task='competing task',draft={'decision':'approve'},
        recordIndex=[{'recordId':'one'}]),artifacts={'critic':{'approved':True,'issues':[]}},
        validation_feedback=feedback))


def test_projection_only_applies_to_the_corrector_and_preserves_other_arguments():
    from lab_runner.quality.execution import project_correction_arguments
    raw='arbitrary original input'
    assert project_correction_arguments('quality-author',raw)==raw


@pytest.mark.parametrize('feedback',[None,'other feedback','publicCheck {"missingRecords":["one"]}',
    'publicCheck {"error":"unsupportedEvidence"}'])
def test_no_host_target_preserves_full_context_for_evidence_recovery(feedback):
    from lab_runner.quality.execution import project_correction_arguments
    raw=arguments(feedback)
    assert project_correction_arguments('quality-review-corrector',raw)==raw


@pytest.mark.parametrize('target',[{'approved':True,'issues':['decision']},
    {'approved':'false','issues':[]},{'approved':False,'issues':['invented']},
    {'approved':False,'issues':['decision','decision']}])
def test_invalid_or_inconsistent_target_is_rejected(target):
    from lab_runner.quality.execution import project_correction_arguments
    with pytest.raises(ValueError):
        project_correction_arguments('quality-review-corrector',arguments('publicCheck '+json.dumps({'target':target})))


def test_projection_keeps_a_correct_draft_target_without_forcing_false():
    from lab_runner.quality.execution import project_correction_arguments
    value=json.loads(project_correction_arguments('quality-review-corrector',arguments(
        'publicCheck {"target":{"approved":true,"issues":[]}}')))
    assert value=={'caseId':'control','correctionTarget':{'approved':True,'issues':[]},'recordIndex':[{'recordId':'one'}]}
