"""Owner-facing advisory reports, separate from raw private invocation evidence."""

import html
import json
from copy import deepcopy

from .contracts import encoded, own


def compact_advice(report):
    """Lossless distinct advisory content; raw reports remain in host evidence."""
    if report is None:
        return None
    report = own(report,262144)

    def unique(items, with_turns=False):
        grouped={}
        for original in items:
            item=deepcopy(original)
            turn=item.pop('turn') if with_turns else None
            key=encoded(item)
            if key not in grouped:
                grouped[key]={**item,'turns':[]} if with_turns else item
            if with_turns and turn not in grouped[key]['turns']:
                grouped[key]['turns'].append(turn)
        return list(grouped.values())

    fields=('advisory','terminal','claim','acceptedTurns','meaning','sourcesSha256','sources')
    result={k:report[k] for k in fields}
    coverage=report['coverage']
    result['coverage']={k:v for k,v in coverage.items() if k not in {'issues','open_issues'}}
    result['coverage']['issues']=unique(coverage.get('issues',[]),True)
    result['citations']=unique(report['citations'],True)
    for name in ('premises','witnesses'):
        result[name]=unique(report[name])
    result['openQuestions']=list(dict.fromkeys(report['openQuestions']))
    if 'turnEvidence' in report:
        for name,field in [('premiseOrigins','premises'),('questionOrigins','openQuestions'),
                           ('witnessOrigins','witnesses')]:
            result[name]=unique([{'value':value,'turn':t['turn']}
                for t in report['turnEvidence'] for value in t[field]],True)
    return result


def render_review(request, state, attempt_summary, *, include_turns=False):
    frozen = request['evidence']
    citations = []
    for turn in state['turns']:
        for item in turn.get('evidence',[]):
            mapping = frozen['lineMap'][item['line']-1]
            citations.append({**mapping,'quote':item['quote'],'turn':turn['turn_no']})
    return {'advisory':True,'terminal':state['terminal'],'claim':state['claim'],
            'acceptedTurns':len(state['turns']),'coverage':attempt_summary['coverage'],
            'citations':citations,'sourcesSha256':frozen['sourcesSha256'],
            'sources':[{'sourceId':s['sourceId'],'textSha256':s['textSha256'],'revision':s['revision'],'reference':s['reference']} for s in frozen['sources']],
            'premises':[p for t in state['turns'] for p in t.get('premises',[])],
            'openQuestions':[q for t in state['turns'] for q in t.get('open_questions',[])],
            'witnesses':[t['witness'] for t in state['turns'] if t.get('witness')],
            'attempts':attempt_summary['attempts'],'reportedTokens':attempt_summary['reportedTokens'],
            'usageComplete':attempt_summary['usageComplete'],
            'meaning':'Dimensions examined is not truth, implementation correctness, or release approval.',
            **({'turnEvidence':[{'turn':t['turn_no'],'premises':t.get('premises',[]),
                 'openQuestions':t.get('open_questions',[]),
                 'witnesses':[t['witness']] if t.get('witness') else []}
                 for t in state['turns']]} if include_turns else {})}


def render_markdown(report):
    # Entities are interpreted as text after Markdown structure is parsed. This
    # prevents links, images, fences and new blocks in untrusted source/model text.
    def text(value):
        if type(value) in (dict, list):
            value = json.dumps(value, ensure_ascii=False, allow_nan=False)
        escaped = html.escape(str(value), quote=True)
        return ''.join(f'&#{ord(char)};' if char in '\\`*_{}[]()#+-.!|~:=/\r\n' else char
                       for char in escaped)

    lines = ['# Advisory SUE review','',text(report['meaning']),'',
             'Terminal: '+text(report['terminal']),'',text(report['claim']),'',
             'Accepted turns: '+text(report['acceptedTurns']),
             'Attempts: '+text(report['attempts']),
             'Reported tokens: '+text(report['reportedTokens']),
             'Usage complete: '+text(report['usageComplete']),'',
             '## Coverage','',text(report['coverage']),'', '## Sources','']
    for source in report['sources']:
        lines.append('- '+text(source))
    lines.extend(['','Source set SHA256: '+text(report['sourcesSha256']),'','## Citations',''])
    for citation in report['citations']:
        lines.append('- '+text(citation['sourceId'])+':'+text(citation['sourceLine'])
                     +' — '+text(citation['quote'])+' (turn '+text(citation['turn'])+')')
    for heading, key in (('Premises','premises'),('Witnesses','witnesses'),('Open questions','openQuestions')):
        lines.extend(['','## '+heading,''])
        lines.extend('- '+text(value) for value in report[key])
        if not report[key]:
            lines.append('None recorded.')
    return '\n'.join(lines)+'\n'
