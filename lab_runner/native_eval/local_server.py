"""Prepare a private oMLX agent profile without modifying shared settings."""
import copy
import hashlib
import json
import os
from pathlib import Path


def prepare_agent_server_profile(source_base, destination, model):
    source=Path(source_base).expanduser().resolve()
    destination=Path(destination).expanduser().absolute()
    documents={};bodies={}
    for name in ('settings.json','model_settings.json','model_profiles.json','global_templates.json'):
        path=source/name
        if name in {'model_profiles.json','global_templates.json'} and not path.exists():continue
        if path.is_symlink() or not path.is_file():raise ValueError('regular oMLX settings files required')
        body=path.read_bytes()
        document=json.loads(body)
        if type(document) is not dict:raise ValueError('oMLX settings objects required')
        documents[name]=document;bodies[name]=body
    models=documents['model_settings.json'].get('models')
    if type(models) is not dict or type(models.get(model)) is not dict:
        raise ValueError('selected model must exist in source settings')
    settings=copy.deepcopy(documents['model_settings.json'])
    settings['models'][model]['enable_thinking']=False
    updated=json.dumps(settings,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'
    original=bodies['model_settings.json'];bodies['model_settings.json']=updated
    destination.mkdir(mode=0o700)
    for name,body in bodies.items():
        with os.fdopen(os.open(destination/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as target:
            target.write(body)
    return {'model':model,'enableThinking':False,'copiedSettings':sorted(bodies),
            'sourceModelSettingsSha256':hashlib.sha256(original).hexdigest(),
            'modelSettingsSha256':hashlib.sha256(updated).hexdigest()}
