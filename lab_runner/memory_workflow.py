"""Trusted operator CLI for the optional frozen-memory workflow; no HTTP grants."""

import argparse
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse
import uuid


def load_host(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 65536 or path.stat().st_mode & 0o077:
        raise ValueError("private bounded host configuration required")
    value = json.loads(path.read_text())
    required = {"namespace", "principal", "store", "runtime"}
    if (
        type(value) is not dict
        or not required <= set(value)
        or set(value) - required - {"memory", "memory_required", "accounting"}
    ):
        raise ValueError("invalid memory workflow configuration")
    if type(value.get("memory_required", False)) is not bool:
        raise ValueError("invalid memory policy")
    if type(value["namespace"]) is not str or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value["namespace"]
    ):
        raise ValueError("invalid namespace")
    runtime = value["runtime"]
    if type(runtime) is not dict or set(runtime) != {"base_url", "model"}:
        raise ValueError("invalid runtime binding")
    url = urlparse(runtime["base_url"])
    if (
        url.scheme != "http"
        or url.hostname not in {"127.0.0.1", "localhost", "::1"}
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ValueError("this synthetic CLI requires a loopback model fixture")
    return value


def store_for(value):
    from prosaic_harness import FileRunStore

    spec = value["store"]
    if type(spec) is not dict:
        raise ValueError("invalid store")
    if spec.get("kind") == "file" and set(spec) == {"kind", "path"}:
        if not Path(spec["path"]).is_absolute():
            raise ValueError("absolute store path required")
        return FileRunStore(spec["path"], namespace=value["namespace"])
    if spec.get("kind") == "postgres" and set(spec) == {"kind", "dsn_env"}:
        from prosaic_harness_postgres import PostgresRunStore

        return PostgresRunStore(
            os.environ[spec["dsn_env"]], namespace=value["namespace"]
        )
    raise ValueError("invalid store")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "status", "resume"))
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--expected-revision")
    parser.add_argument("--choice", choices=("continue", "reject"))
    args = parser.parse_args(argv)
    if args.action != "start" and not args.run_id:
        parser.error("status and resume require --run-id")
    from prosaic_integration_lab.identity import Principal
    from prosaic_integration_lab.memory_provider import (
        MemoryProviders,
        MemoryUnavailable,
    )
    from prosaic_integration_lab.memory_workflow import MemoryWorkflowSession
    from prosaic_runtime import EndpointConfig, RuntimeConfig
    from prosaic_harness import StoreError

    providers, store = None, None
    try:
        host = load_host(args.config)
        principal = Principal(**host["principal"])
        providers = MemoryProviders(host.get("memory"))
        store = store_for(host)
        recorder = None
        if "accounting" in host:
            from prosaic_runtime import RateCard
            from prosaic_runtime_postgres import PostgresRecorder

            recorder = PostgresRecorder(
                os.environ[host["accounting"]["dsn_env"]],
                namespace=host["namespace"],
                environment="sandbox",
                rate_card=RateCard(
                    "memory-fixture-v1", host["runtime"]["model"], "2", "8", "0.5"
                ),
            )
        config = RuntimeConfig(
            {
                "fixture": EndpointConfig(
                    host["runtime"]["base_url"],
                    host["runtime"]["model"],
                    features={"streaming": False},
                )
            },
            {},
            "fixture",
            allowed_tools=frozenset(),
        )
        session = MemoryWorkflowSession(
            providers=providers,
            store=store,
            config=config,
            principal=principal,
            namespace=host["namespace"],
            accounting=recorder,
        )
        run_id = args.run_id or uuid.uuid4().hex
        if args.action == "start":
            if args.request is None or args.request.stat().st_size > 8192:
                raise ValueError("bounded request required")
            request = json.loads(args.request.read_text())
            if type(request) is not dict or set(request) != {"task", "query"}:
                raise ValueError("invalid request")
            result = session.start(
                run_id, **request, required=host.get("memory_required", False)
            )
        elif args.action == "status":
            result = session.status(run_id)
        else:
            if not args.expected_revision or not args.choice:
                raise ValueError("explicit review revision required")
            result = session.resume(
                run_id, expected_revision=args.expected_revision, choice=args.choice
            )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except MemoryUnavailable as error:
        print(json.dumps({"error": "memory_unavailable", "reason": error.reason}))
        return 3
    except PermissionError:
        print(json.dumps({"error": "not_found"}))
        return 4
    except StoreError as error:
        print(json.dumps({"error": error.code}))
        return 5
    except (ValueError, TypeError, KeyError, OSError):
        print(json.dumps({"error": "invalid_configuration_or_request"}))
        return 2
    finally:
        if providers is not None:
            providers.close()
        if store is not None:
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())
