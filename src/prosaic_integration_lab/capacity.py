"""Tested per-replica pool and persistent pilot-record ceilings."""
DEFAULTS={'writes':2,'reads':4,'per_tenant':2,'max_runs':10000,'max_tenant_runs':10000}

def policy(value):
    if not isinstance(value,dict) or set(value)-set(DEFAULTS): raise ValueError('invalid capacity policy')
    result={**DEFAULTS,**value}
    if 'per_tenant' not in value: result['per_tenant']=result['writes']
    if 'max_tenant_runs' not in value: result['max_tenant_runs']=result['max_runs']
    for name,maximum in (('writes',2),('reads',4),('per_tenant',2),('max_runs',10000),('max_tenant_runs',10000)):
        if type(result[name]) is not int or not 1 <= result[name] <= maximum: raise ValueError('untested capacity policy')
    if result['per_tenant']>result['writes'] or result['max_tenant_runs']>result['max_runs']:
        raise ValueError('incoherent capacity policy')
    return result
