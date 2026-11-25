"""Use the public copy command from an isolated installed consumer."""

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def copy_command(tmp_path):
    def copy(*args):
        return subprocess.run(
            [sys.executable, "-I", "-m", "lab_runner.blueprints", *args],
            cwd=tmp_path, capture_output=True, text=True, timeout=15,
        )

    return copy


@pytest.fixture
def copied_blueprint(tmp_path, copy_command):
    from lab_runner import blueprints

    assert Path(blueprints.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    project = tmp_path / "copied-example"
    result = copy_command("copy", "catalogue-ontology", str(project))
    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()) == project
    return project
