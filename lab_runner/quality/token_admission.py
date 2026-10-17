"""Trusted host token admission; no model-specific estimator or fallback."""
from contextlib import nullcontext


def admit_live_counters(counters,config,profiles):
    """Validate host registrations before any live reservation or execution."""
    if type(counters) is not dict or set(counters)!=set(profiles):
        raise ValueError('live benchmarks require a trusted token counter for every profile')
    from prosaic_runtime import ProsaicRuntime,TokenCounterRegistration
    if 'token_admission_v1' not in ProsaicRuntime.capabilities:
        raise ValueError('qualified Runtime token admission support required')
    owned={}
    for alias in profiles:
        counter=counters[alias];endpoint=config.profiles[alias]
        if (type(counter) is not TokenCounterRegistration or
                (counter.descriptor.provider,counter.descriptor.model)!=(endpoint.provider,endpoint.model) or
                type(endpoint.max_tokens) is not int or endpoint.max_tokens<=0):
            raise ValueError('trusted token counter binding or output bound mismatch')
        owned[alias]=TokenCounterRegistration(counter.descriptor,counter.counter)
    return owned


def execution_scope(limits,token_counter=None):
    if token_counter is None:return nullcontext()
    from prosaic_runtime import ExecutionBudget
    return ExecutionBudget(timeout_s=limits['timeoutSeconds'],max_provider_requests=limits['providerRequests'],
        max_tool_calls=limits['toolCalls'],max_reported_tokens=limits['reportedTokens'],token_counter=token_counter)


def activate_scope(scope):
    return scope.activate() if callable(getattr(scope,'activate',None)) else scope


def counter_identity(counters,*,output,config,profiles,recover_only=False):
    """Persist only descriptor provenance; recovery never needs executable counters."""
    from .contracts import decode
    from .allowance import private_write
    from prosaic_runtime import TokenCounterDescriptor
    path=output/'token-admission.json'
    if recover_only:
        if path.is_symlink() or path.stat().st_size>65536:raise ValueError('invalid counter provenance')
        value=decode(path.read_bytes(),65536)
        if type(value) is not dict or set(value)!=set(profiles):raise ValueError('counter provenance mismatch')
        for alias,descriptor in value.items():
            parsed=TokenCounterDescriptor.from_dict(descriptor);endpoint=config.profiles[alias]
            if (parsed.provider,parsed.model)!=(endpoint.provider,endpoint.model):raise ValueError('counter provenance mismatch')
    else:
        value={k:v.descriptor.to_dict() for k,v in counters.items()}
        if path.exists():
            if path.is_symlink() or path.stat().st_size>65536 or decode(path.read_bytes(),65536)!=value:
                raise ValueError('counter provenance mismatch')
        else:private_write(path,value)
    return value
