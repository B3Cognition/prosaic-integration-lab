import builtins
import hashlib
import sys
from types import ModuleType

import pytest

from prosaic_integration_lab.identity import Principal


OWNER = Principal("tenant-a", "alice", "payer-a")


@pytest.fixture
def adapter(monkeypatch):
    """Optional external SDK boundary; real wheels are exercised in acceptance."""
    module = ModuleType("prosaic_memory_castle")

    class Error(RuntimeError):
        def __init__(self, code):
            self.code = code

    module.MemoryProviderError = Error
    module.WorkerCommand = tuple
    module.CastleMemoryProvider = None
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return module


def settings(tmp_path):
    return {
        "enabled": True,
        "bindings": [
            {
                "tenant_id": "tenant-a",
                "actor_id": "alice",
                "billing_account_id": "payer-a",
                "namespace": "alice-memory",
                "palace_path": str(tmp_path / "palace"),
                "config_path": str(tmp_path / "config.json"),
                "worker_command": [
                    "/absolute/python",
                    "-m",
                    "cognitive_castle.provider_worker",
                ],
                "allowed_wings": ["approved"],
            }
        ],
    }


def test_disabled_memory_neither_imports_adapter_nor_opens_a_worker(monkeypatch):
    from prosaic_integration_lab.memory_provider import (
        MemoryProviders,
        MemoryUnavailable,
    )

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split(".")[0] not in {
            "prosaic_memory_castle",
            "cognitive_castle",
            "torch",
        }
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    registry = MemoryProviders()
    assert registry.capture(OWNER, "question") == {"status": "disabled", "bundle": None}
    with pytest.raises(MemoryUnavailable, match="disabled"):
        registry.capture(OWNER, "question", required=True)
    registry.close()


def test_capture_uses_trusted_exact_owner_and_freezes_selected_digests(
    tmp_path, monkeypatch, adapter
):
    from prosaic_integration_lab.memory_provider import MemoryProviders
    import prosaic_memory_castle

    calls = []
    text = "SQLite chosen. 🙂\r\n"
    digest = hashlib.sha256(text.encode()).hexdigest()

    class Provider:
        def __init__(self, command, **kwargs):
            calls.append(kwargs)

        def search(self, query, limit):
            return {
                "hits": [{"record_id": "one", "text_sha256": digest, "revision": "v1"}]
            }

        def snapshot(self, ids, *, expected, maximum_bytes):
            assert ids == ["one"] and expected == {
                "one": {"text_sha256": digest, "revision": "v1"}
            }
            return {
                "sources": [{"record_id": "one"}],
                "texts": [text],
                "digest": "fixture",
            }

        def close(self):
            calls.append("closed")

    monkeypatch.setattr(prosaic_memory_castle, "CastleMemoryProvider", Provider)
    config = settings(tmp_path)
    registry = MemoryProviders(config)
    config["bindings"][0]["allowed_wings"].append("denied")
    assert calls == []
    frozen = registry.capture(OWNER, "why")
    assert frozen["status"] == "available" and frozen["bundle"]["texts"] == [text]
    assert calls[0]["allowed_wings"] == ("approved",)
    assert calls[0]["profile"] == "memory-fts-v1" and calls[0]["recency_boost"] is False
    for other in (
        Principal("tenant-b", "alice", "payer-a"),
        Principal("tenant-a", "bob", "payer-a"),
        Principal("tenant-a", "alice", "payer-b"),
    ):
        with pytest.raises(PermissionError):
            registry.capture(other, "why")
    registry.close()
    assert calls[-1] == "closed"


def test_optional_unavailable_is_distinct_from_empty_and_required_blocks(
    tmp_path, monkeypatch, adapter
):
    from prosaic_integration_lab.memory_provider import (
        MemoryProviders,
        MemoryUnavailable,
    )
    import prosaic_memory_castle

    class Provider:
        def __init__(self, *args, **kwargs):
            pass

        def search(self, *args, **kwargs):
            raise prosaic_memory_castle.MemoryProviderError("unavailable")

        def close(self):
            pass

    monkeypatch.setattr(prosaic_memory_castle, "CastleMemoryProvider", Provider)
    registry = MemoryProviders(settings(tmp_path))
    assert registry.capture(OWNER, "why") == {
        "status": "unavailable",
        "bundle": None,
        "reason": "unavailable",
    }
    with pytest.raises(MemoryUnavailable, match="unavailable"):
        registry.capture(OWNER, "why", required=True)
    registry.close()
    assert registry.capture(OWNER, "why")["status"] == "unavailable"


def test_healthy_empty_memory_is_explicit_not_an_unavailable_error(
    tmp_path, monkeypatch, adapter
):
    from prosaic_integration_lab.memory_provider import MemoryProviders
    import prosaic_memory_castle

    class Provider:
        def __init__(self, *args, **kwargs):
            pass

        def search(self, *args, **kwargs):
            return {"hits": []}

        def close(self):
            pass

    monkeypatch.setattr(prosaic_memory_castle, "CastleMemoryProvider", Provider)
    registry = MemoryProviders(settings(tmp_path))
    assert registry.capture(OWNER, "why", required=True) == {
        "status": "empty",
        "bundle": None,
    }


@pytest.mark.parametrize(
    "change",
    [
        {"enabled": 1},
        {"enabled": False, "bindings": []},
        {"enabled": True, "bindings": []},
        {"enabled": True, "binding": {}},
    ],
)
def test_invalid_host_configuration_is_rejected(change):
    from prosaic_integration_lab.memory_provider import MemoryProviders

    with pytest.raises(ValueError):
        MemoryProviders(change)
