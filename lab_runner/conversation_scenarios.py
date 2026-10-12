"""Trusted owned-stack conversation configuration and public HTTP helpers."""
import re
import hashlib

import httpx


def conversation_configuration(namespace):
    if type(namespace) is not str or not re.fullmatch('[A-Za-z0-9._-]{1,128}',namespace):
        raise ValueError('invalid owned conversation namespace')
    return {'bundles':[{'version':tier+'-v1','model_url':'http://model:8000/v1',
        'model':'test-model-'+tier,'model_tier':tier,'fixture_effects':True,
        'operation_namespace':'conversation-'+hashlib.sha256(namespace.encode()).hexdigest()[:32]+'-'+tier,
        'journal_identity':'conversation-journal-v1'} for tier in ('balanced','strong')],
        'tenants':{'tenant-a':{'enabled':True,'binding_version':'balanced-v1'},
                   'tenant-b':{'enabled':True,'binding_version':'strong-v1'}},
        'max_sessions':128,'max_owner_sessions':16}


def request(lab,principal,method,path,*,replica='a',**kwargs):
    token=next(token for token,value in lab['principals'].items()
        if value['tenant_id']==principal['tenant_id'] and value['actor_id']==principal['actor_id'])
    return httpx.request(method,lab[replica]+path,headers={'Authorization':'Bearer '+token,
        **kwargs.pop('headers',{})},timeout=90,**kwargs)


def create(lab,principal,key,*,replica='a'):
    result=request(lab,principal,'POST','/conversations',replica=replica,
        headers={'Idempotency-Key':key},json={})
    result.raise_for_status();return result.json()


def send(lab,principal,session,message_id,message,*,replica='a',interaction_ref=None):
    body={'messageId':message_id,'message':message,'expectedRevision':session['revision']}
    if interaction_ref is not None:body['interactionRef']=interaction_ref
    result=request(lab,principal,'POST','/conversations/'+session['sessionId']+'/messages',
        replica=replica,json=body)
    result.raise_for_status();return result.json()
