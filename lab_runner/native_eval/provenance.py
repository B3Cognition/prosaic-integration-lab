"""Require installed public APIs and reuse the Lab's complete payload auditor."""
from contextlib import redirect_stdout
import io
from importlib.metadata import version
from pathlib import Path

from prosaic_integration_lab.dependencies import manifest_digest, sdk_manifest


def require_native():
    import prosaic_runtime as sdk
    if not hasattr(sdk, 'NativeRuntime') or not hasattr(sdk, 'NativePolicy'):
        raise ValueError('installed Runtime lacks native extension; install the explicit candidate wheels')
    if 'site-packages' not in Path(sdk.__file__).resolve().parts:
        raise ValueError('native tests require installed SDK wheels, not source/editable imports')
    return sdk


def audit_candidate(manifest, wheel_directory):
    from scripts.audit_install import audit
    data = sdk_manifest(manifest)
    with redirect_stdout(io.StringIO()):
        audit(Path(manifest), Path(wheel_directory))
    require_native()
    return {'manifestSha256': manifest_digest(manifest),
        'origin': data.get('native_candidate', {}).get('origin', 'manifest_selected'),
        'artifacts': [{key: item[key] for key in ('distribution', 'version', 'sha256', 'source_commit')}
                      for item in data['artifacts']],
        'installedRuntimeVersion': version('b3-prosaic-runtime')}
