import importlib
from pathlib import Path
import runpy
import socket
import sys
from types import ModuleType

import pytest


@pytest.mark.parametrize("attempt", ["torch", "spacy", "cognitive_castle.sue", "cognitive_castle.soar_bridge", "network"])
def test_qualification_worker_records_and_blocks_forbidden_paths(tmp_path, monkeypatch, attempt):
    from lab_runner.memory_fixture import READ_GUARD

    marker = tmp_path / "forbidden.txt"
    parent = ModuleType("cognitive_castle")
    parent.__path__ = []
    monkeypatch.setitem(sys.modules, "cognitive_castle", parent)
    monkeypatch.delitem(sys.modules, attempt, raising=False)
    monkeypatch.setattr(sys, "argv", ["worker", str(marker)])
    monkeypatch.setattr(sys, "meta_path", list(sys.meta_path))
    # Register restoration before the isolated bootstrap replaces these hooks.
    monkeypatch.setattr(socket.socket, "connect", socket.socket.connect)
    monkeypatch.setattr(socket, "create_connection", socket.create_connection)

    def provider(*args, **kwargs):
        if attempt == "network":
            socket.create_connection(("127.0.0.1", 9))
        else:
            importlib.import_module(attempt)

    monkeypatch.setattr(runpy, "run_module", provider)
    with pytest.raises(RuntimeError, match="qualification forbids"):
        exec(READ_GUARD, {"__name__": "qualification_guard"})
    assert marker.read_text() == ("network" if attempt == "network" else "import:" + attempt)
