"""Keep mandatory evidence; fit optional whole recall within every planned call."""
from lab_runner.quality.contracts import decode,encode,digest
from .budget import make_plan


def assemble_context(mandatory,retrieval,*,quote_inputs,counter_descriptor,quote_identity,
                     max_requests,output_tokens,token_ceiling,reported_tokens=0,inflight_tokens=0):
    mandatory=decode(encode(mandatory,65536),65536)
    retrieval=decode(encode(retrieval,65536),65536)
    if type(mandatory) is not dict or 'recalledEpisodes' in mandatory or not callable(quote_inputs):
        raise ValueError('owned mandatory context and trusted quotation required')
    if type(retrieval) is not dict or type(retrieval.get('episodes')) is not list:
        raise ValueError('trusted retrieval required')
    episodes=retrieval['episodes']
    if (len(episodes)>3 or any(type(e) is not dict or type(e.get('episodeId')) is not str for e in episodes) or
            len({e['episodeId'] for e in episodes})!=len(episodes) or
            retrieval.get('resultSha256')!=digest(episodes) or
            retrieval.get('resultBytes')!=len(encode(episodes)) or len(encode(episodes))>4096):
        raise ValueError('retrieval ownership or bounds mismatch')
    # Clone descriptor now too: callbacks never receive mutable policy authority.
    counter_descriptor=decode(encode(counter_descriptor,16384),16384)
    def quote(selected):
        request=dict(mandatory,recalledEpisodes=selected)
        try:bounds=quote_inputs(decode(encode(request,65536),65536))
        except Exception:raise ValueError('context quotation failed') from None
        plan=make_plan(counter_descriptor=counter_descriptor,quote_identity=quote_identity,
            request_sha256=digest(request),input_bounds=bounds,max_requests=max_requests,
            output_tokens=output_tokens,token_ceiling=token_ceiling,
            reported_tokens=reported_tokens,inflight_tokens=inflight_tokens)
        return request,plan
    selected=[];decisions=[];request,plan=quote(selected)
    mandatory_admitted=plan['admitted']
    for episode in episodes:
        reason='mandatoryRejected'
        if mandatory_admitted:
            candidate_request,candidate_plan=quote(selected+[episode])
            if candidate_plan['admitted']:
                selected.append(episode);request,plan=candidate_request,candidate_plan;reason='selected'
            else:reason='contextCapacity' if any(b+output_tokens>counter_descriptor['contextCapacityTokens']
                for b in candidate_plan['inputBounds']) else 'trajectoryBudget'
        decisions.append(dict(episodeId=episode['episodeId'],reason=reason))
    reasons={d['episodeId']:d['reason'] for d in decisions}
    retrieval.update(episodes=selected,resultSha256=digest(selected),resultBytes=len(encode(selected)))
    if 'decisions' in retrieval:
        retrieval['decisions']=[dict(d,reason=reasons.get(d['episodeId'],d['reason'])) for d in retrieval['decisions']]
    return decode(encode(dict(request=request,retrieval=retrieval,plan=plan,decisions=decisions)))
