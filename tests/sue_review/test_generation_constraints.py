"""Generation narrows mechanical combinations, never canonical-valid answers."""
from copy import deepcopy

import castle_sue as engine
from jsonschema import Draft202012Validator
import pytest

from tests.sue_review.test_execution import CLAIM, SOURCE, TYPES, RESULTS, answer

WITNESS={'situation':'An export request.','reading_a':'Export is permitted.','reading_b':'Export is forbidden.',
         'why_incompatible':'The same request cannot both be permitted and forbidden.','lines_a':[1],'lines_b':[1]}


def generation_schema(*args):
    from prosaic_integration_lab.sue_review.generation import generation_schema as build
    return build(*args)


@pytest.mark.parametrize('operator',list(TYPES))
def test_all_canonical_results_remain_generatable(operator):
    state=engine.initial_state(CLAIM);state['operator']=operator
    canonical=engine.schema(state);original=deepcopy(canonical)
    schema=generation_schema(state,canonical,len(SOURCE.splitlines()))
    Draft202012Validator.check_schema(schema)
    for result in canonical['properties']['test_result']['enum']:
        value=answer(operator);verdict={'UNKNOWN':'SILENT','INCOMPLETE':'PARTIAL','CONFLICT':'CONTRADICTED'}.get(result,'SUPPORTED')
        value.update(test_result=result,verdict=verdict)
        value['claim']=CLAIM if operator in ('DEFINE','REVISE') and verdict in ('SUPPORTED','PARTIAL') else None
        if result=='UNKNOWN':value.update(evidence=[],evidence_lines=[],premises=[])
        if result in ('FOUND','CONFLICT','POSSIBLE'):value['witness']=deepcopy(WITNESS)
        if operator=='REVISE' and verdict in ('SUPPORTED','PARTIAL'):value['revision_reason']='No prior commitments exist; this is the proposed interpretation.'
        assert engine.advance(state,value,SOURCE.splitlines())[1] is None
        assert Draft202012Validator(canonical).is_valid(value)
        assert Draft202012Validator(schema).is_valid(value),(operator,result)
        if result=='UNKNOWN':
            value['premises']=[{'statement':'A disclosed unsupported possibility.','kind':'assumption','evidence_lines':[]}]
            assert engine.advance(state,value,SOURCE.splitlines())[1] is None
            assert Draft202012Validator(schema).is_valid(value)
    assert canonical==original


@pytest.mark.parametrize('mutation',['silent_answer_citations','silent_grounded_premise','missing_claim','wrong_success_type','future_turn','out_of_range_line','missing_witness','invalid_verdict_pair','claim_outside_define'])
def test_generation_blocks_observed_invalid_field_combinations(mutation):
    state=engine.initial_state(CLAIM);value=answer('DEFINE')
    if mutation.startswith('silent'):
        value.update(test_result='UNKNOWN',verdict='SILENT',claim=None)
        if mutation=='silent_grounded_premise':value.update(evidence=[],evidence_lines=[])
    elif mutation=='missing_claim':value['claim']=None
    elif mutation=='wrong_success_type':state['operator']='DISTINGUISH';value['claim']=None
    elif mutation=='future_turn':value['addresses']=[1]
    elif mutation=='out_of_range_line':value['evidence_lines']=[3]
    elif mutation=='missing_witness':value.update(test_result='CONFLICT',verdict='CONTRADICTED',claim=None)
    elif mutation=='invalid_verdict_pair':value['verdict']='PARTIAL'
    else:state['operator']='DISTINGUISH';value['answer_type']='distinction'
    canonical=engine.schema(state)
    assert Draft202012Validator(canonical).is_valid(value)
    assert engine.advance(state,value,SOURCE.splitlines())[1]=='invalid_turn'
    assert not Draft202012Validator(generation_schema(state,canonical,2)).is_valid(value)


def test_generation_does_not_replace_exact_quote_and_provenance_validation():
    state=engine.initial_state(CLAIM);canonical=engine.schema(state)
    schema=generation_schema(state,canonical,2)
    for mutation in ('false_quote','premise_subset','stated_paraphrase'):
        value=answer('DEFINE')
        if mutation=='false_quote':value['evidence'][0]['quote']='Fabricated text.'
        elif mutation=='premise_subset':value['premises'][0]['evidence_lines']=[2]
        else:value['premises'][0]['statement']='Only admins can export.'
        assert Draft202012Validator(schema).is_valid(value)
        assert engine.advance(state,value,SOURCE.splitlines())[1]=='invalid_turn'
    value=answer('DEFINE');value['evidence'][0]['quote']='administrators may export'
    value['premises'][0]['statement']='administrators may export'
    assert engine.advance(state,value,SOURCE.splitlines())[1] is None
    assert Draft202012Validator(schema).is_valid(value)

