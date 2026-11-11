"""Descriptive host diagnostics, never a replacement scorer or entailment judge."""


def review_diagnostics(grade,advice=None):
    coverage=advice.get('coverage',{}) if advice else {}
    return {'strictPassed':grade['passed'],
        'failedChecks':[k for k,v in grade['checks'].items() if not v],
        'terminal':advice.get('terminal') if advice else None,
        'acceptedTurns':advice.get('acceptedTurns') if advice else None,
        'missingDimensions':coverage.get('missing'),
        'openIssueCount':len(coverage.get('open_issues',[])) if advice else None,
        'examinationComplete':bool(advice and advice['terminal']=='RESOLVED'
            and not coverage.get('missing') and not coverage.get('open_issues')),
        'semanticEntailmentVerified':False,
        'sourcesSha256':advice.get('sourcesSha256') if advice else None}
