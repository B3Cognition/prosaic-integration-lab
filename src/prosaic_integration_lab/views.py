def public_native_interaction(source, *, include_response_schema=False):
    allowed = ('version','runId','revision','stepId','question','choices','deadline','responseSchemaDigest')
    result = {name:source[name] for name in allowed if name in source}
    if include_response_schema and 'responseSchema' in source:
        result['responseSchema'] = source['responseSchema']
    reviewed = source.get('reviewOutputs',{}).get('review')
    if type(reviewed) is dict:
        result['reviewOutputs'] = {'review':{name:reviewed[name] for name in ('entity_id','approved') if name in reviewed}}
    return result

def public_run(run_id, state, revision, *, workflow=None):
    result = {'run_id': run_id, 'status': state['status'], 'current_step': state['current'],
              'revision': revision, 'recovery_status': {
                  'interrupted_call':'retry_consent_required','usage_unknown':'usage_reconciliation_required',
                  'token_limit':'budget_exhausted'}.get(state.get('reason'))}
    if state['status'] == 'waiting':
        result['choices'] = [c for c in state.get('choices', []) if c in {'approve', 'reject'}]
        if state['current'] == 'approval' and workflow in {'approval','synthetic'}:
            reviewed = None
            valid = workflow == 'approval'
            if workflow == 'synthetic':
                output = state.get('outputs',{}).get('author')
                valid = (isinstance(output,dict) and set(output) == {'result'} and
                    type(output['result']) is str and len(output['result']) <= 256)
                if valid:
                    reviewed = {'result':output['result']}
            result['review'] = {'revision':revision,'question':
                'Approve this fixture output?' if workflow == 'synthetic' else 'Approve this fixture request?',
                'result':reviewed} if valid else None
            if not valid:
                result['choices'] = []
    return result

def uncertain_run(run_id):
    return {'run_id': run_id, 'status': 'start_uncertain', 'current_step': None,
            'revision': None, 'recovery_status': 'operator_reconciliation_required'}

def public_usage(report):
    allowed = ('version', 'total_calls', 'complete_calls', 'unresolved_calls', 'quarantined_calls',
               'unsupported_calls', 'partial_calls', 'unavailable_assessment_calls', 'estimated_amounts',
               'fully_costed', 'billing_eligible', 'coverage', 'excluded_resources', 'as_of')
    return {name: report[name] for name in allowed}


def public_conversation_history(session_id,messages,*,max_bytes=4194304+512):
    """Only the public role-aware message contract may leave the host."""
    import json
    documents=[]
    for message in messages:
        item=message.to_dict()
        if (type(item) is not dict or item.get('role') not in {'user','assistant','tool'} or
                set(item)-{'role','content','turnStatus','failureCode'}):
            raise ValueError('invalid conversation history')
        documents.append(item)
    result={'version':1,'sessionId':session_id,'messages':documents}
    if len(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8'))>max_bytes:
        raise ValueError('conversation history limit')
    return result
