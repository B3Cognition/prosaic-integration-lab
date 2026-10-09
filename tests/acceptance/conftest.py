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
