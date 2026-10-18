"""Consumer correction policy only: no execution, source grants or call consent."""
from lab_runner.quality.contracts import digest, encode, decode, identifier, sha
from lab_runner.role_qualification import FieldCheck, LIMITS


def correction_feedback(*, assignment_id, draft, evidence, diagnostics, issue_paths, critic_advice=None):
    """Project trusted field diagnostics; never forward raw critique or gold."""
    sha(assignment_id);diagnostics=decode(encode(diagnostics,maximum=65536))
    if type(diagnostics) is not list or not 1<=len(diagnostics)<=64:raise ValueError('correction needs field failures')
    fields=set()
    for row in diagnostics:
        if (type(row) is not dict or set(row)!= {'code','field','evidenceRefs'}
                or row['code']!='field_mismatch' or not row['field'] or type(row['evidenceRefs']) is not list):
            raise ValueError('only closed host field diagnostics are correctable')
        FieldCheck(row['field'],None,evidence_refs=tuple(row['evidenceRefs']))
        fields.add(row['field'])
    for issue,path in issue_paths.items():identifier(issue);FieldCheck(path,None)
    advice=None
    if critic_advice is not None:
        issues=critic_advice.get('issues',[]) if type(critic_advice) is dict else []
        if type(issues) is not list or any(type(v) is not str for v in issues):issues=[]
        advice=dict(supportedIssues=sorted({v for v in issues if v in issue_paths and issue_paths[v] in fields}))
    return dict(version=1,assignmentId=assignment_id,draftDigest=digest(draft),evidenceDigest=digest(evidence),
                maxCorrections=1,diagnostics=diagnostics,criticAdvice=advice)


def compare_corrections(baseline, critic):
    """Compare host-scored arms only after matching their frozen starting point."""
    if baseline.get('arm')!='no-critic' or critic.get('arm')!='critic':raise ValueError('baseline/critic arms required')
    keys={'taskDigest','profileFingerprint','workerContractDigest','correctorContractDigest',
          'initialDraftDigest','evidenceDigest','diagnosticsDigest','policyRevision','limits'}
    a=baseline.get('match');b=critic.get('match')
    if type(a) is not dict or set(a)!=keys:raise ValueError('incomplete match binding')
    for key in keys-{'policyRevision','limits'}:sha(a[key])
    if type(a['policyRevision']) is not str or not a['policyRevision'] or encode(a['limits'])!=encode(LIMITS):
        raise ValueError('invalid matched policy/limits')
    matched=(encode(a)==encode(b)
             and baseline.get('initialArtifactCorrect') is critic.get('initialArtifactCorrect'))
    empty=dict(matched=matched,accountingKnown=False,marginalCounts=None,answerGain=None,
               artifactGain=None,causalModelBenefitEstablished=False)
    if not matched:return empty
    known=True
    for row in (baseline,critic):
        for key in ('finalArtifactCorrect','taskAccepted','safe','initialArtifactCorrect'):
            if type(row.get(key)) is not bool:raise ValueError('invalid host score')
        counts=row.get('counts')
        if type(counts) is not dict or set(counts)!= {'providerRequests','toolCalls','reportedTokens'}:
            raise ValueError('incomplete accounting')
        for key,value in counts.items():
            if value is None and key=='reportedTokens':known=False;continue
            if type(value) is not int or not 0<=value<=LIMITS[key]:raise ValueError('invalid or exceeded counts')
    empty['accountingKnown']=known
    if known:
        empty['marginalCounts']={k:critic['counts'][k]-baseline['counts'][k] for k in baseline['counts']}
        if baseline['safe'] and critic['safe']:
            empty['answerGain']=int(critic['taskAccepted'])-int(baseline['taskAccepted'])
            empty['artifactGain']=int(critic['finalArtifactCorrect'])-int(baseline['finalArtifactCorrect'])
    return empty
