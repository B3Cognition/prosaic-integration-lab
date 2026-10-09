def public_run(run_id, state, revision, *, workflow=None):
    result = {'run_id': run_id, 'status': state['status'], 'current_step': state['current'],
              'revision': revision, 'recovery_status': 'retry_consent_required' if state.get('reason') == 'interrupted_call' else None}
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
