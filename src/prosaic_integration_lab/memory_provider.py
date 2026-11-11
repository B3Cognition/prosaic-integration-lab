"""Optional host-bound memory. No adapter/model import or worker when disabled."""

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import threading


class MemoryUnavailable(RuntimeError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def _identity(principal):
    return (principal.tenant_id, principal.actor_id, principal.billing_account_id)


def _reference(value):
    return type(value) is str and re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value
    )


def _binding(value):
    required = {
        "tenant_id",
        "actor_id",
        "billing_account_id",
        "namespace",
        "palace_path",
        "config_path",
        "worker_command",
        "allowed_wings",
    }
    if (
        type(value) is not dict
        or not required <= set(value)
        or set(value)
        - required
        - {"profile", "recency_boost", "startup_timeout", "operation_timeout"}
    ):
        raise ValueError("invalid memory configuration")
    result = deepcopy(value)
    for name in ("tenant_id", "actor_id", "billing_account_id", "namespace"):
        if not _reference(result[name]):
            raise ValueError("invalid memory configuration")
    for name in ("palace_path", "config_path"):
        if (
            type(result[name]) is not str
            or "\x00" in result[name]
            or not Path(result[name]).is_absolute()
        ):
            raise ValueError("absolute memory path required")
    command, wings = result["worker_command"], result["allowed_wings"]
    if (
        type(command) is not list
        or not command
        or len(command) > 16
        or any(type(arg) is not str or not arg or "\x00" in arg for arg in command)
        or not Path(command[0]).is_absolute()
        or type(wings) is not list
        or not 1 <= len(wings) <= 128
        or any(not _reference(wing) for wing in wings)
        or len(set(wings)) != len(wings)
    ):
        raise ValueError("invalid memory command or scope")
    result["profile"] = result.get("profile", "memory-fts-v1")
    result["recency_boost"] = result.get("recency_boost", False)
    if (
        result["profile"] not in {"memory-fts-v1", "memory-v1"}
        or type(result["recency_boost"]) is not bool
        or result["recency_boost"]
        and result["profile"] != "memory-fts-v1"
    ):
        raise ValueError("invalid memory profile")
    for name, default in (("startup_timeout", 30), ("operation_timeout", 10)):
        result[name] = result.get(name, default)
        if (
            type(result[name]) not in {int, float}
            or not math.isfinite(result[name])
            or not 0 < result[name] <= 120
        ):
            raise ValueError("bounded memory timeout required")
    result["allowed_wings"] = tuple(wings)
    result["worker_command"] = tuple(command)
    return result


class MemoryProviders:
    """Host-only registry; identities never come from model or request arguments."""

    def __init__(self, settings=None):
        settings = {"enabled": False} if settings is None else settings
        if type(settings) is not dict or type(settings.get("enabled")) is not bool:
            raise ValueError("invalid memory configuration")
        self.enabled = settings["enabled"]
        self._bindings, self._providers = {}, {}
        self._lock, self._closed = threading.Lock(), False
        if not self.enabled:
            if set(settings) != {"enabled"}:
                raise ValueError("disabled memory cannot configure bindings")
            return
        if (
            set(settings) != {"enabled", "bindings"}
            or type(settings["bindings"]) is not list
            or not 1 <= len(settings["bindings"]) <= 128
        ):
            raise ValueError("explicit memory bindings required")
        for value in settings["bindings"]:
            binding = _binding(value)
            key = tuple(
                binding[name]
                for name in ("tenant_id", "actor_id", "billing_account_id")
            )
            if key in self._bindings:
                raise ValueError("duplicate memory owner")
            self._bindings[key] = binding

    def _provider(self, principal):
        key = _identity(principal)
        if key not in self._bindings:
            raise PermissionError("memory_forbidden")
        with self._lock:
            if self._closed:
                raise MemoryUnavailable("unavailable")
            if key not in self._providers:
                from prosaic_memory_castle import CastleMemoryProvider, WorkerCommand

                settings = self._bindings[key]
                self._providers[key] = CastleMemoryProvider(
                    WorkerCommand(settings["worker_command"]),
                    **{
                        name: settings[name]
                        for name in (
                            "palace_path",
                            "namespace",
                            "config_path",
                            "allowed_wings",
                            "profile",
                            "recency_boost",
                            "startup_timeout",
                            "operation_timeout",
                        )
                    },
                )
            return self._providers[key]

    def capture(self, principal, query, *, required=False):
        if (
            type(required) is not bool
            or type(query) is not str
            or not query.strip()
            or len(query.encode()) > 4096
        ):
            raise ValueError("invalid memory request")
        if not self.enabled:
            if required:
                raise MemoryUnavailable("disabled")
            return {"status": "disabled", "bundle": None}
        try:
            provider = self._provider(principal)
        except (ImportError, MemoryUnavailable):
            if required:
                raise MemoryUnavailable("unavailable") from None
            return {"status": "unavailable", "bundle": None, "reason": "unavailable"}
        from prosaic_memory_castle import MemoryProviderError

        try:
            hits = provider.search(query, limit=3)["hits"]
            if not hits:
                return {"status": "empty", "bundle": None}
            ids = [hit["record_id"] for hit in hits]
            expected = {
                hit["record_id"]: {
                    "text_sha256": hit["text_sha256"],
                    "revision": hit["revision"],
                }
                for hit in hits
            }
            bundle = provider.snapshot(ids, expected=expected, maximum_bytes=65536)
            # Persist an owned JSON value. Never alias a mutable provider response.
            return json.loads(
                json.dumps({"status": "available", "bundle": bundle}, allow_nan=False)
            )
        except MemoryProviderError as error:
            if required:
                raise MemoryUnavailable(error.code) from None
            return {"status": "unavailable", "bundle": None, "reason": error.code}

    def capture_selected(self, principal, selections, *, maximum_bytes=65536):
        """Freeze an exact host selection; selected review never falls back to recall."""
        if (
            type(selections) is not list
            or not 1 <= len(selections) <= 16
            or type(maximum_bytes) is not int
            or not 1 <= maximum_bytes <= 65536
        ):
            raise ValueError("invalid selected memory request")
        expected = {}
        for selection in selections:
            if type(selection) is not dict or set(selection) != {
                "record_id", "text_sha256", "revision"
            }:
                raise ValueError("invalid selected memory request")
            record_id, text_hash, revision = (
                selection[name] for name in ("record_id", "text_sha256", "revision")
            )
            if (
                type(record_id) is not str
                or not record_id.strip()
                or "\x00" in record_id
                or len(record_id.encode("utf-8")) > 512
                or record_id in expected
                or type(text_hash) is not str
                or not re.fullmatch("[0-9a-f]{64}", text_hash)
                or revision is not None and (
                    type(revision) is not str
                    or not revision.strip()
                    or "\x00" in revision
                    or len(revision.encode("utf-8")) > 512
                )
            ):
                raise ValueError("invalid selected memory request")
            expected[record_id] = {"text_sha256": text_hash, "revision": revision}
        if not self.enabled:
            raise MemoryUnavailable("disabled")
        try:
            provider = self._provider(principal)
            from prosaic_memory_castle import MemoryProviderError
        except (ImportError, MemoryUnavailable):
            raise MemoryUnavailable("unavailable") from None
        try:
            bundle = provider.snapshot(
                list(expected), expected=expected, maximum_bytes=maximum_bytes
            )
        except MemoryProviderError as error:
            raise MemoryUnavailable(error.code) from None
        try:
            # Detach provider-owned data before inspecting and retaining it.
            bundle = json.loads(json.dumps(bundle, allow_nan=False, ensure_ascii=False))
            sources = bundle["sources"]
            ids = [source["record_id"] for source in sources]
            if (
                type(sources) is not list
                or len(ids) != len(expected)
                or any(type(record_id) is not str for record_id in ids)
                or set(ids) != set(expected)
                or type(bundle["texts"]) is not list
                or len(bundle["texts"]) != len(expected)
            ):
                raise ValueError("incomplete selected snapshot")
            total = 0
            for source, text in zip(sources, bundle['texts'], strict=True):
                bound = expected[source['record_id']]
                if (type(text) is not str
                        or source['text_sha256'] != bound['text_sha256']
                        or source['revision'] != bound['revision']
                        or source['wing'] not in self._bindings[_identity(principal)]['allowed_wings']
                        or hashlib.sha256(text.encode('utf-8')).hexdigest() != bound['text_sha256']):
                    raise ValueError('changed selected snapshot')
                total += len(text.encode('utf-8'))
            if total > maximum_bytes:
                raise ValueError('oversized selected snapshot')
        except (KeyError, TypeError, ValueError, RecursionError):
            raise MemoryUnavailable("invalid_snapshot") from None
        binding = self._bindings[_identity(principal)]
        binding_hash = hashlib.sha256(json.dumps(
            binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")).hexdigest()
        scope = {name: binding[name] for name in (
            "tenant_id", "actor_id", "billing_account_id", "namespace"
        )}
        scope.update(binding_sha256=binding_hash, allowed_wings=list(binding["allowed_wings"]))
        return {"bundle": bundle, "scope": scope}

    def close(self):
        with self._lock:
            self._closed = True
            providers, self._providers = list(self._providers.values()), {}
        for provider in providers:
            provider.close()
