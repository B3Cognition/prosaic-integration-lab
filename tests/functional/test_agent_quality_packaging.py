from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile


def test_built_archives_include_every_quality_resource(tmp_path):
    root=Path(__file__).resolve().parents[2]
    result=subprocess.run([sys.executable,'-m','build','--outdir',str(tmp_path)],
                          cwd=root,capture_output=True,text=True)
    assert result.returncode==0,result.stderr[-3000:]
    required={'evidence-review-v1.json','answer.schema.json','review.schema.json',
              'reviewer.md','critic.md','author.md','review-corrector.md','sdk-provenance.json'}
    wheel=next(tmp_path.glob('*.whl'));sdist=next(tmp_path.glob('*.tar.gz'))
    with zipfile.ZipFile(wheel) as archive:
        assert required<={Path(n).name for n in archive.namelist() if '/quality/data/' in n}
        assert 'lab_runner/memory/evidence.py' in archive.namelist()
        assert 'lab_runner/memory/data/evidence-summary.schema.json' in archive.namelist()
    with tarfile.open(sdist) as archive:
        assert required<={Path(n).name for n in archive.getnames() if '/quality/data/' in n}
        assert any(n.endswith('/configs/agent-quality.example.json') for n in archive.getnames())
