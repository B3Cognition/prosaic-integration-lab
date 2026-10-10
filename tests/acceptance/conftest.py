import json
import os
from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def lab():
    path = os.environ.get('LAB_ACCEPTANCE_CONFIG')
    if not path:
        pytest.fail('Required owned acceptance stack is missing')
    return json.loads(Path(path).read_text())


@pytest.fixture
def owned_database(lab):
    """Allocate only within the validated, freshly owned fixture container."""
    def create(prefix='native'):
        import uuid
        from psycopg.conninfo import conninfo_to_dict,make_conninfo
        from lab_runner.stack import command
        from lab_runner.manifest import validate_resource
        manifest = json.loads(Path(lab['fixture_manifest']).read_text())
        identifier = manifest['database_id']
        validate_resource(json.loads(command(manifest['engine'],'inspect',identifier))[0],identifier,manifest['owner'])
        name = prefix+'_'+uuid.uuid4().hex
        command(manifest['engine'],'exec',identifier,'createdb','-U','postgres','--owner=lab_migration',name)
        result = dict(lab)
        for key in ('migration_dsn','app_dsn'):
            parameters = conninfo_to_dict(lab[key]); parameters['dbname'] = name
            result[key] = make_conninfo(**parameters)
        return result
    return create
