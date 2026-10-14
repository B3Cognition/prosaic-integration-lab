"""Local exact synthetic byte units; not a production tokenizer integration."""
import json


MODELS = frozenset({'test-model-balanced','test-model-strong'})


def counter_identity(model):
    if type(model) is not str or model not in MODELS:
        raise ValueError('synthetic context counter requires the approved fixture model')
    return 'lab-synthetic-byte-'+model.removeprefix('test-model-')+'-v1'


class SyntheticByteCounter:
    def count_tokens(self, request):
        return len(json.dumps(request,allow_nan=False).encode('utf-8'))


def synthetic_registry(model):
    identity=counter_identity(model)
    from prosaic_runtime import ProsaicRuntime
    if 'context_assembly_v1' not in ProsaicRuntime.capabilities:
        raise ValueError('context assembly capability unavailable')
    from prosaic_runtime import TokenCounterDescriptor,TokenCounterRegistration,TokenCounterRegistry
    descriptor=TokenCounterDescriptor(identity,'openai-compatible',model,'openai-chat-v1',
        1_048_576,'1','0'*64,'1'*64,'exact',
        'Exact JSON UTF-8 byte units for the synthetic fixture grammar; not model tokenizer qualification.')
    return TokenCounterRegistry({identity:TokenCounterRegistration(descriptor,SyntheticByteCounter())})


def context_configuration(definition):
    ordinary=definition.get('context_policy')
    interpreting=definition.get('interpretation_context_policy')
    if ordinary is None and interpreting is None:return {}
    from prosaic_runtime import ContextPolicy,TokenCounterRegistry
    policies,registrations={},{}
    for name,value,model in (
            ('context_policy',ordinary,definition.get('model','test-model')),
            ('interpretation_context_policy',interpreting,
             definition.get('interpretation_model',definition.get('model','test-model')))):
        policy=ContextPolicy.from_dict(value) if value is not None else None
        policies[name]=policy
        if policy is None:continue
        identity=counter_identity(model)
        if policy.counter_identity!=identity:raise ValueError('unregistered context counter')
        registrations[identity]=synthetic_registry(model).resolve(identity)
    return {**policies,'token_counters':TokenCounterRegistry(registrations)}
