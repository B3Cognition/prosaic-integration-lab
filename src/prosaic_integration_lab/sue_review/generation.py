"""Generation-only mechanical constraints; canonical validation stays authoritative.

Each alternative is a canonical result/verdict pair. These are necessary, not
sufficient, conditions for an accepted turn. Cross-field quote containment,
premise citation subsets, uniqueness and natural-language support are still
checked independently; responses are never transformed to fit this schema.
"""
from copy import deepcopy
import json

GENERATION_SCHEMA_VERSION = 'sue-grounding-schema-v1'
_SUCCESS = {
    'DEFINE':('ESTABLISHED',['definition','example']),
    'DISTINGUISH':('ESTABLISHED',['distinction']),
    'CAUSE_OR_CRITERION':('ESTABLISHED',['criterion']),
    'DIVIDE':('ESTABLISHED',['case-split']),
    'COUNTEREXAMPLE':('NOT_FOUND',['example','case-split']),
    'FOLLOW_CONSEQUENCE':('CONSISTENT',['consequence']),
    'TEST_OPPOSITE':('EXCLUDED',['consequence']),
    'REVISE':('REVISED',['revision']),
}


def generation_schema(state, canonical, source_line_count):
    """Keep every canonical-valid turn available; rule relationships guide tokens."""
    branches=[]
    line={'type':'integer','minimum':1,'maximum':source_line_count}
    previous=[turn['turn_no'] for turn in state['turns']]
    for result in canonical['properties']['test_result']['enum']:
        # Canonical builders may reuse the same array dictionary for unrelated
        # fields. JSON ownership breaks those aliases before narrowing a field.
        branch=json.loads(json.dumps(canonical)); props=branch['properties']
        verdict={'UNKNOWN':'SILENT','INCOMPLETE':'PARTIAL','CONFLICT':'CONTRADICTED'}.get(result,'SUPPORTED')
        props['test_result']={'type':'string','enum':[result]}
        props['verdict']={'type':'string','enum':[verdict]}
        props['answer']['minLength']=1
        props['addresses']['maxItems']=len(previous)
        if previous:props['addresses']['items']={'type':'integer','enum':previous}
        props['evidence_lines']['items']=deepcopy(line)
        props['evidence']['items']['properties']['line']=deepcopy(line)
        supported_definition=state['operator'] in ('DEFINE','REVISE') and verdict in ('SUPPORTED','PARTIAL')
        props['claim']={'type':'string','minLength':1} if supported_definition else {'type':'null'}
        props['revision_reason']=({'type':'string','minLength':1} if state['operator']=='REVISE' and supported_definition else {'type':'null'})
        success,answer_types=_SUCCESS[state['operator']]
        if result==success:props['answer_type']={'type':'string','enum':answer_types}
        if result in ('FOUND','CONFLICT','POSSIBLE'):
            props['witness']=deepcopy(canonical['properties']['witness']['anyOf'][0])
            for key in ('lines_a','lines_b'):
                props['witness']['properties'][key].update(minItems=1,items=deepcopy(line))
        else:props['witness']={'type':'null'}
        if verdict=='SILENT':
            props['evidence_lines']['maxItems']=0
            props['evidence']['maxItems']=0
            premise=props['premises']['items']['properties']
            premise['kind']={'type':'string','enum':['assumption']}
            premise['evidence_lines']['maxItems']=0
        else:
            for key in ('evidence_lines','evidence','premises'):props[key]['minItems']=1
            premise=props['premises']['items']; alternatives=[]
            for kind in ('stated','inferred','assumption'):
                item=deepcopy(premise);fields=item['properties']
                fields['kind']={'type':'string','enum':[kind]}
                fields['evidence_lines']['items']=deepcopy(line)
                fields['evidence_lines'].update({'maxItems':0} if kind=='assumption' else {'minItems':1})
                alternatives.append(item)
            props['premises']['items']={'anyOf':alternatives}
        branches.append(branch)
    return {'type':'object','anyOf':branches}
