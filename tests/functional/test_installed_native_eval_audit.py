"""The evaluation runner must audit SDKs without a repository scripts package."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import packaging

from tests.functional.test_dependency_install import ROOT, wheel_family


def test_packaged_evaluation_audits_and_rejects_tampering_without_source_helpers(tmp_path):
    manifest, cache, site = wheel_family(tmp_path, renamed=True, install=True)
    installed = tmp_path / 'site-packages'
    site.rename(installed)
    runtime = cache / 'b3_prosaic_runtime-1.0-py3-none-any.whl'
    with zipfile.ZipFile(runtime) as original:
        files = {name: original.read(name) for name in original.namelist()}
    files['prosaic_runtime/__init__.py'] += b'NativeRuntime = object\nNativePolicy = object\n'
    with zipfile.ZipFile(runtime, 'w') as updated:
        for name, body in files.items():
            updated.writestr(name, body)
    (installed / 'prosaic_runtime/__init__.py').write_bytes(files['prosaic_runtime/__init__.py'])
    data = json.loads(manifest.read_text())
    for item in data['artifacts']:
        item['source_commit'] = 'a' * 40
        if item['distribution'] == 'b3-prosaic-runtime':
            item['sha256'] = hashlib.sha256(runtime.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(data))
    for source, name in ((ROOT / 'src/prosaic_integration_lab', 'prosaic_integration_lab'),
                         (ROOT / 'lab_runner', 'lab_runner'),
                         (Path(packaging.__file__).parent, 'packaging')):
        shutil.copytree(source, installed / name, ignore=shutil.ignore_patterns('__pycache__'))
    # No source root, host site packages, PYTHONPATH or scripts directory can
    # mask the missing installed dependency. The real auditor inspects real files.
    code = r'''import importlib.util,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
assert importlib.util.find_spec('scripts') is None
from lab_runner.native_eval.provenance import audit_candidate
report=audit_candidate(sys.argv[2],sys.argv[3])
assert report['installedRuntimeVersion']=='1.0' and len(report['artifacts'])==5
(Path(sys.argv[1])/'prosaic/__init__.py').write_text('VALUE="tampered"\n')
try: audit_candidate(sys.argv[2],sys.argv[3])
except ValueError as error:
 assert 'payload' in str(error)
else: raise AssertionError('modified SDK code was certified')
print(json.dumps({'audited':True,'tamperRejected':True}))
'''
    result = subprocess.run([sys.executable, '-I', '-S', '-c', code,
        str(installed), str(manifest), str(cache)], cwd=tmp_path,
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'audited': True, 'tamperRejected': True}
