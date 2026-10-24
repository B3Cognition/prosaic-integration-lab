import builtins
from copy import deepcopy
import hashlib
import json
import sys
from types import ModuleType

import pytest

from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.memory_provider import MemoryProviders, MemoryUnavailable


OWNER = Principal("tenant-a", "alice", "payer-a")
TEXT = "Exact source. 🙂\r\n"
HASH = hashlib.sha256(TEXT.encode()).hexdigest()
SELECTIONS = [{"record_id": "one", "text_sha256": HASH, "revision": "v1"}]


def settings(tmp_path):
    return {"enabled": True, "bindings": [{
        "tenant_id": "tenant-a", "actor_id": "alice", "billing_account_id": "payer-a",
        "namespace": "owned-memory", "palace_path": str(tmp_path / "palace"),
        "config_path": str(tmp_path / "config.json"), "worker_command": ["/private/python"],
        "allowed_wings": ["approved"],
    }]}


@pytest.fixture
def boundary(monkeypatch):
    """Replace only the optional SDK's public external-worker boundary."""
    module = ModuleType("prosaic_memory_castle")

    class Error(RuntimeError):
        def __init__(self, code):
            self.code = code

    class Provider:
        instances = []

        def __init__(self, command, **kwargs):
            self.command, self.settings, self.calls = command, kwargs, []
            self.error = None
            self.bundle = {"schema_version": 1, "digest": "a" * 64,
                "sources": [{"record_id": "one", "text_sha256": HASH, "revision": "v1",
                    "representation": None, "wing": "approved", "captured_at": None,
                    "source_id": "origin"}], "texts": [TEXT]}
            payload = {k:v for k,v in self.bundle.items() if k != 'digest'}
            self.bundle['digest'] = hashlib.sha256(json.dumps(payload,sort_keys=True,
                separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
            self.instances.append(self)

        def snapshot(self, ids, *, expected, maximum_bytes):
            self.calls.append((deepcopy(ids), deepcopy(expected), maximum_bytes))
            if self.error:
                raise Error(self.error)
            return self.bundle

        def close(self):
            pass

    module.MemoryProviderError, module.CastleMemoryProvider = Error, Provider
    module.WorkerCommand = tuple
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return Provider


def test_selected_capture_owns_exact_snapshot_and_trusted_scope(tmp_path, boundary):
    configuration = settings(tmp_path)
    registry = MemoryProviders(configuration)
    selection = deepcopy(SELECTIONS)
    capture = registry.capture_selected(OWNER, selection, maximum_bytes=1234)
    provider = boundary.instances[0]
    assert provider.calls == [(["one"], {"one": {"text_sha256": HASH, "revision": "v1"}}, 1234)]
    expected_binding = dict(configuration["bindings"][0], profile="memory-fts-v1",
        recency_boost=False, startup_timeout=30, operation_timeout=10)
    binding_hash = hashlib.sha256(json.dumps(expected_binding, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert capture["scope"] == {"tenant_id": "tenant-a", "actor_id": "alice",
        "billing_account_id": "payer-a", "namespace": "owned-memory",
        "binding_sha256": binding_hash, "allowed_wings": ["approved"]}
    assert capture["bundle"]["texts"] == [TEXT]
    assert set(capture) == {"bundle", "scope"}
    assert "palace_path" not in capture["scope"] and "worker_command" not in capture["scope"]
    provider.bundle["texts"][0] = "changed"
    provider.bundle["sources"][0]["wing"] = "changed"
    selection[0]["revision"] = "changed"
    configuration["bindings"][0]["allowed_wings"].append("forged")
    assert capture["bundle"]["texts"] == [TEXT]
    assert capture["bundle"]["sources"][0]["wing"] == "approved"
    with pytest.raises(MemoryUnavailable, match='invalid_snapshot'):
        registry.capture_selected(OWNER, SELECTIONS)
    provider.bundle['texts'][0] = TEXT
    provider.bundle['sources'][0]['wing'] = 'approved'
    capture["scope"]["allowed_wings"].append("forged")
    assert registry.capture_selected(OWNER, SELECTIONS)["scope"]["allowed_wings"] == ["approved"]


def test_disabled_selected_capture_imports_no_optional_engine(monkeypatch):
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert name.split(".")[0] not in {"prosaic_memory_castle", "cognitive_castle", "torch"}
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(MemoryUnavailable, match="disabled"):
        MemoryProviders().capture_selected(OWNER, SELECTIONS)


@pytest.mark.parametrize("principal", [Principal("foreign", "alice", "payer-a"),
    Principal("tenant-a", "foreign", "payer-a"), Principal("tenant-a", "alice", "foreign")])
def test_foreign_principal_never_constructs_selected_provider(tmp_path, boundary, principal):
    with pytest.raises(PermissionError, match="memory_forbidden"):
        MemoryProviders(settings(tmp_path)).capture_selected(principal, SELECTIONS)
    assert not boundary.instances


@pytest.mark.parametrize("selection", [None, (), [], SELECTIONS * 17, SELECTIONS * 2,
    [True], [{"record_id": True, "text_sha256": HASH, "revision": "v1"}],
    [{"record_id": "", "text_sha256": HASH, "revision": "v1"}],
    [{"record_id": "a" * 513, "text_sha256": HASH, "revision": "v1"}],
    [{"record_id": "one", "text_sha256": "A" * 64, "revision": "v1"}],
    [{"record_id": "one", "text_sha256": HASH, "revision": True}],
    [{"record_id": "one", "text_sha256": HASH, "revision": ""}],
    [{"record_id": "one", "text_sha256": HASH}],
    [dict(SELECTIONS[0], scope="forged")]])
def test_malformed_selections_rejected_before_provider(tmp_path, boundary, selection):
    with pytest.raises(ValueError):
        MemoryProviders(settings(tmp_path)).capture_selected(OWNER, selection)
    assert not boundary.instances


@pytest.mark.parametrize("cap", [True, False, 0, -1, 65537, 1.5, None])
def test_selected_byte_cap_rejected_before_provider(tmp_path, boundary, cap):
    with pytest.raises(ValueError):
        MemoryProviders(settings(tmp_path)).capture_selected(OWNER, SELECTIONS, maximum_bytes=cap)
    assert not boundary.instances


@pytest.mark.parametrize("reason", ["unavailable", "revision_conflict", "scope_forbidden"])
def test_provider_rejection_never_returns_partial_capture(tmp_path, boundary, reason):
    registry = MemoryProviders(settings(tmp_path))
    registry.capture_selected(OWNER, SELECTIONS)
    boundary.instances[0].error = reason
    with pytest.raises(MemoryUnavailable) as error:
        registry.capture_selected(OWNER, SELECTIONS)
    assert error.value.reason == reason


@pytest.mark.parametrize("sources", [[], [{"record_id": "other"}],
    [{"record_id": "one"}, {"record_id": "one"}],
    [{"record_id": "one"}, {"record_id": "extra"}], [True]])
def test_snapshot_requires_exact_selected_id_coverage(tmp_path, boundary, sources):
    registry = MemoryProviders(settings(tmp_path))
    registry.capture_selected(OWNER, SELECTIONS)
    boundary.instances[0].bundle["sources"] = sources
    with pytest.raises(MemoryUnavailable):
        registry.capture_selected(OWNER, SELECTIONS)


def test_closed_registry_selected_capture_is_unavailable(tmp_path, boundary):
    registry = MemoryProviders(settings(tmp_path))
    registry.close()
    with pytest.raises(MemoryUnavailable, match="unavailable"):
        registry.capture_selected(OWNER, SELECTIONS)
    assert not boundary.instances


def test_binding_only_change_changes_capture_scope_identity(tmp_path, boundary):
    first = settings(tmp_path)
    second = deepcopy(first)
    second["bindings"][0]["config_path"] = str(tmp_path / "other-config")
    a = MemoryProviders(first).capture_selected(OWNER, SELECTIONS)
    b = MemoryProviders(second).capture_selected(OWNER, SELECTIONS)
    assert a["scope"]["binding_sha256"] != b["scope"]["binding_sha256"]


@pytest.mark.parametrize('field,value', [('text_sha256','b'*64),('revision','v2'),('wing','foreign')])
def test_selected_snapshot_rechecks_bound_revision_hash_and_scope(tmp_path,boundary,field,value):
    registry = MemoryProviders(settings(tmp_path))
    registry.capture_selected(OWNER,SELECTIONS)
    boundary.instances[0].bundle['sources'][0][field] = value
    with pytest.raises(MemoryUnavailable,match='invalid_snapshot'):
        registry.capture_selected(OWNER,SELECTIONS)


def test_selected_snapshot_rechecks_verbatim_bytes_and_byte_limit(tmp_path,boundary):
    registry = MemoryProviders(settings(tmp_path))
    registry.capture_selected(OWNER,SELECTIONS)
    provider = boundary.instances[0]
    provider.bundle['texts'][0] = 'changed'
    with pytest.raises(MemoryUnavailable,match='invalid_snapshot'):
        registry.capture_selected(OWNER,SELECTIONS)
    provider.bundle['texts'][0] = TEXT
    with pytest.raises(MemoryUnavailable,match='invalid_snapshot'):
        registry.capture_selected(OWNER,SELECTIONS,maximum_bytes=1)
