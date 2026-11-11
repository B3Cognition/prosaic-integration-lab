from copy import deepcopy

from markdown_it import MarkdownIt

from prosaic_integration_lab.sue_review.reporting import render_markdown, render_review
from prosaic_integration_lab.sue_review.sources import freeze_documents


def test_advisory_markdown_neutralizes_source_and_model_markup():
    attack = '[open](https://evil.example) ![image](https://evil.example/i)\n# forged\n<script>alert(1)</script>'
    report = dict(meaning=attack, terminal=attack, claim=attack, acceptedTurns=1,
        attempts=2, reportedTokens=30, usageComplete=False, sourcesSha256='a'*64,
        coverage={'examined':[attack], 'missing':[attack]},
        citations=[dict(sourceId=attack,sourceLine=1,quote=attack,turn=1)],
        premises=[dict(statement=attack,kind='assumed',evidence_lines=[])],
        witnesses=[dict(example=attack)],openQuestions=[attack],
        sources=[dict(sourceId=attack,textSha256='b'*64,revision=attack,reference=attack)])
    before = deepcopy(report)
    markdown = render_markdown(report)
    rendered = MarkdownIt().render(markdown)
    assert '<a href=' not in rendered and '<img' not in rendered and '<script>' not in rendered
    assert '<h1>forged' not in rendered
    for label in ('Coverage', 'Premises', 'Witnesses', 'Open questions', 'Attempts', 'Reported tokens', 'Usage complete'):
        assert label in markdown
    assert report == before


def test_review_retains_source_local_citations_coverage_and_usage():
    frozen = freeze_documents([dict(sourceId='first',text='First.\r\n'),
        dict(sourceId='second',text='Second.\r\n',revision='r2',reference='host-reference')])
    state = dict(terminal='RESOLVED',claim='A reviewed claim',turns=[dict(turn_no=1,
        evidence=[dict(line=2,quote='Second.')],premises=[dict(statement='Assumption',kind='assumed')],
        witness={'example':'Counterexample'},open_questions=['Still open?'])])
    coverage = {'examined':['definition'],'missing':['consistency']}
    report = render_review({'evidence':frozen},state,dict(coverage=coverage,attempts=2,
        reportedTokens=30,usageComplete=True))
    assert report['advisory'] is True and report['terminal']=='RESOLVED'
    assert report['coverage']==coverage and report['attempts']==2 and report['acceptedTurns']==1
    assert report['citations']==[dict(sourceId='second',sourceLine=1,quote='Second.',turn=1)]
    assert report['premises']==[dict(statement='Assumption',kind='assumed')]
    assert report['witnesses']==[{'example':'Counterexample'}]
    assert report['openQuestions']==['Still open?']
    assert report['reportedTokens']==30 and report['usageComplete'] is True
    assert 'not truth' in report['meaning'] and 'approval' in report['meaning']
