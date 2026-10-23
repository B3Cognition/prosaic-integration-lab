"""Answer domains and corrective instructions derived only from public contracts."""
from lab_runner.quality.checks import parse_task
from lab_runner.quality.contracts import decode
from lab_runner.quality.suite import resource
from .context import current_index


def answer_schema(case):
    authority,required,_=parse_task(case['task'])
    index=current_index(case['recordIndex'])
    # Keep missing required labels legal: the model must decide presence itself.
    facts=sorted(set(required)|{r['factId'] for r in index if r['authority']==authority})
    schema=decode(resource('answer.schema.json'))
    schema['properties']['facts']['items']['enum']=facts
    schema['properties']['facts']['description']='factId labels only; never recordId strings. Include only available current required-authority facts verified by this lookup.'
    citation=schema['properties']['citations']['items']['properties']
    citation['factId']['enum']=facts
    citation['recordId']['enum']=sorted(r['recordId'] for r in index)
    citation['recordId']['description']='Current recordId for this fact, with the authority required by the task and its highest revision; never substitute observer evidence.'
    return schema


SOURCE_RULE='Filter by the required authority before revision; select at most one highest-revision record per fact. Observer records never replace required-authority facts.'
ABSENCE_RULE='Check required-authority absence before numeric conditions; missing required facts cannot be filled from observers, recalled notes or the index. Apply the public missing-fact rule before testing values.'


def feedback(issues):
    rules=dict(decision=ABSENCE_RULE,
        facts='Use factId labels, not recordId strings, values or statements. Include only current required-authority facts verified in this attempt; omit absent facts.',
        citations=SOURCE_RULE+' Put recordId only in citations and match each citation factId to its fetched record.')
    return 'answerFields '+','.join(issues)+'. '+' '.join(rules[k] for k in issues)
