"""Rule admission through public, installed Prosaic SDKs: a copyable blueprint and its lane."""

from importlib.metadata import version
from pathlib import Path

BLUEPRINT = Path(__file__).parent / 'blueprint'
MANIFEST = 'dependencies/releases.json'


def require_sdk():
    """Refuse anything but installed SDK wheels that can admit and enforce tagged prose."""
    from packaging.version import Version

    import prosaic

    if not callable(getattr(prosaic, 'parse_rules', None)) or not callable(getattr(prosaic, 'strip_tags', None)):
        raise ValueError('rule admission lane requires Core 0.5.0 or later with parse_rules and strip_tags')
    import prosaic_runtime as sdk

    if not Version('0.9.14') <= Version(version('b3-prosaic-runtime')) < Version('0.10'):
        raise ValueError('rule admission lane requires installed Runtime 0.9.14..<0.10')
    if 'rule_admission_v1' not in sdk.ProsaicRuntime.capabilities:
        raise ValueError('rule admission lane requires the rule_admission_v1 Runtime capability')
    if 'site-packages' not in Path(sdk.__file__).resolve().parts:
        raise ValueError('rule admission lane requires installed SDK wheels')
    return sdk
