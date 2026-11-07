"""Copyable application hosts, backed by public installed SDK APIs."""
from pathlib import Path
import shutil

ROOT = Path(__file__).parent
BLUEPRINTS = {
    'request-headers': ROOT / 'request_headers',
    'revision-review': ROOT / 'revision_review',
    'conversation-caps': ROOT / 'conversation_caps',
    'rule-admission': ROOT.parent / 'rule_admission' / 'blueprint',
}


def copy_blueprint(name, destination):
    """Copy a complete example without replacing an existing consumer directory."""
    if type(name) is not str or name not in BLUEPRINTS:
        raise ValueError('unknown feature blueprint')
    return Path(shutil.copytree(BLUEPRINTS[name], destination,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc')))
