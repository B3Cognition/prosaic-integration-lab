"""Launcher flags and private bootstrap files do not grant implicit execution."""
import json
from pathlib import Path
import stat

import pytest


def test_launch_file_is_private_exclusive_and_rejects_symlinks(tmp_path):
    from lab_runner.explore.__main__ import write_launch
    target = tmp_path / 'connect.json'
    write_launch(target, 'http://127.0.0.1:1234/#connect=synthetic')
    assert json.loads(target.read_text())['url'].endswith('#connect=synthetic')
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        write_launch(target, 'replacement')
    link = tmp_path / 'link'
    link.symlink_to(target)
    with pytest.raises(OSError):
        write_launch(link, 'replacement')


@pytest.mark.parametrize('args', [
    ['--live'], ['--max-units', '300'], ['--port', '-1'],
    ['--config', 'private.yml'], ['--inspect'], ['--acknowledge'],
    ['--inspect', '--acknowledge', '--evidence-root', '/tmp', '--run-id', 'a' * 32],
])
def test_invalid_launcher_authority_fails_before_resources(args):
    from lab_runner.explore.__main__ import main
    with pytest.raises(SystemExit) as failure:
        main(args)
    assert failure.value.code == 2
