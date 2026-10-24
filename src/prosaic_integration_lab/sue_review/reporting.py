"""Owner-facing advisory reports, separate from raw private invocation evidence."""

import html
import json


def render_review(request, state, attempt_summary):
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
            'meaning':'Dimensions examined is not truth, implementation correctness, or release approval.'}


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
