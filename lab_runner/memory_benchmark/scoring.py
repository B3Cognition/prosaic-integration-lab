"""Explicit external semantic judgments; citations alone never establish quality."""
from pathlib import Path

from .dataset import load_frozen, load_key
from .runner import replay
from .storage import read, require, sha, shape


def _material(frozen,output):
    execution=replay(frozen,output);bundle=load_frozen(frozen);key=load_key(frozen)
    rows=[read(Path(output)/item['path'],67108864) for item in execution['samples']]
    return execution,bundle,key,rows


def _answers(rows):
    for row in rows:
        for stage in ('base','review'):
            result=row.get(stage)
            if not result or result.get('candidate') is None:continue
            value=result['qualifiedCandidate']
            for rendering,field in (('base','baseFirstAnswer'),('full','firstAnswer')):
                yield (row['id'],stage,rendering),row,value[field],result['candidate']


def grade_template(frozen,output):
    execution,bundle,key,rows=_material(frozen,output)
    require(key is not None,'semantic scoring needs a frozen independent key')
    keys={c['id']:c for c in key['cases']}
    judgments=[]
    for (sample,stage,rendering),row,answer,candidate in _answers(rows):
        judgments.append(dict(sampleId=sample,stage=stage,rendering=rendering,answerSha256=sha(answer.encode()),
            contradiction=None,unsupportedClaims=None,abstentionCorrect=None,
            facets=[dict(id=f['id'],satisfied=None,reason='',answerQuotes=[],evidenceQuotes=[]) for f in keys[row['caseId']]['facets']]))
    return dict(version=1,runBinding=execution['binding'],resultsSealSha256=sha(read(Path(output)/'results-seal.json')),
        keySha256=sha(key),reviewer='REPLACE_WITH_ADJUDICATOR_ID',judgments=judgments)


def _exact(quote,text):
    shape(quote,('start','end','quote'))
    require(type(quote['start']) is int and type(quote['end']) is int
        and 0<=quote['start']<quote['end']<=len(text) and quote['quote']==text[quote['start']:quote['end']],
        'adjudication exact answer quotation')


def _checked(verdict,template,rows,key):
    shape(verdict,tuple(template))
    for field in ('version','runBinding','resultsSealSha256','keySha256'):
        require(verdict[field]==template[field],'verdict binding mismatch')
    require(type(verdict['reviewer']) is str and 0<len(verdict['reviewer'])<=256
        and verdict['reviewer']!='REPLACE_WITH_ADJUDICATOR_ID','named external adjudicator required')
    require(type(verdict['judgments']) is list and len(verdict['judgments'])==len(template['judgments']), 'judgment denominator')
    answers={address:(row,text,candidate) for address,row,text,candidate in _answers(rows)}
    keys={c['id']:c for c in key['cases']};checked={}
    for item in verdict['judgments']:
        shape(item,('sampleId','stage','rendering','answerSha256','contradiction','unsupportedClaims','abstentionCorrect','facets'))
        address=(item['sampleId'],item['stage'],item['rendering'])
        require(address in answers and address not in checked,'duplicate or foreign adjudication')
        row,text,candidate=answers[address]
        require(sha(text.encode())==item['answerSha256'],'adjudication answer changed')
        for flag in ('contradiction','unsupportedClaims','abstentionCorrect'):
            require(type(item[flag]) is bool,'explicit semantic decisions required')
        correct_status=(candidate['status']=='abstained')==keys[row['caseId']]['expectedAbstention']
        require(not item['abstentionCorrect'] or correct_status,'abstention verdict conflicts with status')
        facets=keys[row['caseId']]['facets'];require(type(item['facets']) is list and len(item['facets'])==len(facets),'facet denominator')
        expected={f['id'] for f in facets};seen=set()
        for facet in item['facets']:
            shape(facet,('id','satisfied','reason','answerQuotes','evidenceQuotes'))
            require(facet['id'] in expected and facet['id'] not in seen,'facet identity');seen.add(facet['id'])
            require(type(facet['satisfied']) is bool and type(facet['reason']) is str and facet['reason'].strip()
                and type(facet['answerQuotes']) is list and type(facet['evidenceQuotes']) is list,'facet decision/proofs required')
            require(not facet['satisfied'] or facet['answerQuotes'],'positive answer entailment proof required')
            require(not facet['satisfied'] or keys[row['caseId']]['expectedAbstention'] or facet['evidenceQuotes'],
                    'positive source support proof required')
            for quote in facet['answerQuotes']:_exact(quote,text)
            for proof in facet['evidenceQuotes']:
                shape(proof,('frameId','displaySha256','start','end','quote'))
                frames=row['retrieval']['frames'];require(proof['frameId'] in frames,'adjudication frame identity')
                frame=frames[proof['frameId']];require(proof['displaySha256']==sha(frame['display'].encode()),'adjudication display hash')
                _exact({k:proof[k] for k in ('start','end','quote')},frame['display'])
                require(any(span['start']<=proof['start']<proof['end']<=span['end'] for span in frame['bodySpans']),
                        'adjudication quote outside displayed source body')
        checked[address]=dict(complete=all(f['satisfied'] for f in item['facets']) and not item['contradiction']
            and not item['unsupportedClaims'] and item['abstentionCorrect'],satisfiedFacets=sum(f['satisfied'] for f in item['facets']),
            facetDenominator=len(facets),contradiction=item['contradiction'],unsupportedClaims=item['unsupportedClaims'])
    require(set(checked)==set(answers),'all accepted answers/renderings require adjudication')
    return checked


def report(frozen,output,*,verdict_path=None):
    execution,bundle,key,rows=_material(frozen,output);checked=None
    if verdict_path is not None:
        require(key is not None,'independent key required')
        checked=_checked(read(verdict_path),grade_template(frozen,output),rows,key)
    arms={}
    for arm in ('manual','strict','expanded'):
        relevant=[r for r in rows if r['arm']==arm];arms[arm]={}
        for rendering in ('base','full'):
            selected=[] if checked is None else [checked[(r['id'],'base',rendering)] for r in relevant
                if (r['id'],'base',rendering) in checked]
            reviewed=[] if checked is None else [checked[(r['id'],'review',rendering)] for r in relevant
                if (r['id'],'review',rendering) in checked]
            arms[arm][rendering]=dict(denominator=len(bundle['cases']),accepted=len([r for r in relevant if (r.get('base') or {}).get('candidate')]),
                graded=len(selected),complete=None if not selected else sum(s['complete'] for s in selected),
                reviewedGraded=len(reviewed),reviewedComplete=None if not reviewed else sum(s['complete'] for s in reviewed))
    return dict(version=1,execution=execution,semanticQuality='unmeasured' if not checked else 'externally_adjudicated',
        keyPresent=key is not None,reviewCandidateQuality='unmeasured' if checked is None or not execution['acceptedReviews'] else 'externally_adjudicated',
        origin=execution['origin'],arms=arms,scoringMethod='External semantic decisions with exact answer and displayed-source proofs; mechanical validity is separate.',
        limitations=['Fixture transport does not measure model quality.','Constructed source-familiar cases do not establish generalization or human productivity.',
            'Failed/blocked cases remain in the scheduled denominator.','Fallback originals are not accepted reviews.'])
