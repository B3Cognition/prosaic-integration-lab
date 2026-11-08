"""Shared consumers retain explicit support for the preserved published train."""
from pathlib import Path
import runpy
import importlib.metadata
import pytest


@pytest.mark.parametrize('runtime_version', ['0.9.17', '0.9.18'])
def test_accounting_ownership_assertion_accepts_both_qualified_trains(monkeypatch, runtime_version):
    consumer = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                                 'blueprint_acceptance/test_accounting_metadata.py'))
    original = importlib.metadata.version
    monkeypatch.setattr(importlib.metadata, 'version',
                        lambda name: runtime_version if name == 'b3-prosaic-runtime' else original(name))
    consumer['test_public_sdk_ownership_and_capability']()


def test_accounting_ownership_assertion_refuses_unqualified_runtime(monkeypatch):
    consumer = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                                 'blueprint_acceptance/test_accounting_metadata.py'))
    original = importlib.metadata.version
    monkeypatch.setattr(importlib.metadata, 'version',
                        lambda name: '0.9.19' if name == 'b3-prosaic-runtime' else original(name))
    with pytest.raises(AssertionError):
        consumer['test_public_sdk_ownership_and_capability']()
