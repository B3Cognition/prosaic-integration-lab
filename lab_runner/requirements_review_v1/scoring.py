"""Host-only exact known-issue checks, not a natural-language entailment judge."""

from jsonschema import Draft202012Validator

from prosaic_integration_lab.sue_review.sources import freeze_documents

from . import SCORER_VERSION, SUITE_VERSION
from .contracts import FINAL_SCHEMA, digest


def grade(case, key, response):
    if key['caseSha256'] != digest(case):
        raise ValueError('case/key identity mismatch')
    frozen = freeze_documents(case['sources'])
    sources = {source['sourceId']:source for source in frozen['sources']}
    checks = dict.fromkeys(('schema','case','assessment','issues','citations'),False)
    report = dict(suiteVersion=SUITE_VERSION,scorerVersion=SCORER_VERSION,caseId=case['caseId'],
        caseSha256=digest(case),sourcesSha256=frozen['sourcesSha256'],passed=False,checks=checks)
    if not Draft202012Validator(FINAL_SCHEMA).is_valid(response):
        return report
    checks['schema'] = True
    checks['case'] = response['caseId']==case['caseId']
    checks['assessment'] = response['assessment']==key['assessment']
    checks['issues'] = set(response['issues'])==set(key['issues'])
    expected = {tuple(sorted(item.items())) for item in key['support']}
    actual, valid = set(), True
    for citation in response['citations']:
        source = sources.get(citation['sourceId'])
        if (source is None or citation['textSha256'] != source['textSha256']
                or not 1 <= citation['startLine'] <= citation['endLine'] <= len(source['text'].splitlines())):
            valid = False
        actual.add(tuple(sorted((k,v) for k,v in citation.items() if k!='textSha256')))
    checks['citations'] = valid and actual==expected
    report['passed'] = all(checks.values())
    return report
