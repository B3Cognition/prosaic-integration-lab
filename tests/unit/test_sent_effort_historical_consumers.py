"""Shared consumers retain explicit support for the preserved published train."""
from pathlib import Path
import runpy
import importlib.metadata
import pytest


@pytest.mark.parametrize('runtime_version,harness_version', [('0.9.17','0.9.12'),('0.9.18','0.9.12'),('0.9.19','0.9.13'),('0.9.20','0.9.14')])
def test_accounting_ownership_assertion_accepts_qualified_trains(monkeypatch, runtime_version,harness_version):
    consumer = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                                 'blueprint_acceptance/test_accounting_metadata.py'))
    original = importlib.metadata.version
    monkeypatch.setattr(importlib.metadata, 'version',
                        lambda name: {'b3-prosaic-runtime':runtime_version,'b3-prosaic-harness':harness_version}.get(name) or original(name))
    consumer['test_public_sdk_ownership_and_capability']()


@pytest.mark.parametrize('runtime_version,harness_version',[('0.9.20','0.9.12'),('0.9.19','0.9.12'),('0.9.18','0.9.13')])
def test_accounting_ownership_assertion_refuses_unqualified_runtime(monkeypatch,runtime_version,harness_version):
    consumer = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                                 'blueprint_acceptance/test_accounting_metadata.py'))
    original = importlib.metadata.version
    monkeypatch.setattr(importlib.metadata, 'version',
                        lambda name: {'b3-prosaic-runtime':runtime_version,'b3-prosaic-harness':harness_version}.get(name) or original(name))
    with pytest.raises(AssertionError):
        consumer['test_public_sdk_ownership_and_capability']()
