"""Explicit local walkthrough: real Castle, synthetic notes and fixture response."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import uuid


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--worker-python", type=Path)
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args(argv)
    if not args.enable:
        print(json.dumps({"enabled": False, "executed": False}))
        return 0
    if (
        args.worker_python is None
        or not args.worker_python.is_absolute()
        or args.directory is None
        or not args.directory.is_absolute()
    ):
        parser.error("enable requires absolute --worker-python and a new --directory")
    # Never overwrite an existing palace or run directory.
    args.directory.mkdir(mode=0o700)
    from prosaic_harness import FileRunStore
    from prosaic_runtime import EndpointConfig, RuntimeConfig
    from prosaic_integration_lab.identity import Principal
    from prosaic_integration_lab.memory_provider import MemoryProviders
    from prosaic_integration_lab.memory_workflow import MemoryWorkflowSession
    from lab_runner.memory_fixture import memory_settings, model_fixture, prepare_castle

    palace = args.directory / "castle"
    worker = str(args.worker_python)
    prepare_castle(worker, palace)
    principal = Principal("tenant-a", "alice", "payer-a")
    run_id = uuid.uuid4().hex
    with (
        closing(MemoryProviders(memory_settings(worker, palace))) as providers,
        FileRunStore(args.directory / "runs", namespace="castle-demo") as store,
        model_fixture("available") as (url, requests),
    ):
        config = RuntimeConfig(
            {
                "fixture": EndpointConfig(
                    url, "memory-fixture", features={"streaming": False}
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
            namespace="castle-demo",
        )
        waiting = session.start(
            run_id,
            task="What did Atlas choose for offline persistence?",
            query="SQLite offline",
            required=True,
        )
        if waiting["status"] != "waiting" or requests:
            raise RuntimeError("walkthrough did not pause before inference")
        frozen = store.load_run(run_id).state["inputs"]["memory"]
        providers.close()
        prepare_castle(worker, palace, mutate=True)
        # A fresh host session has memory disabled. It must use saved evidence.
        with closing(MemoryProviders()) as disabled:
            resumed = MemoryWorkflowSession(
                providers=disabled,
                store=store,
                config=config,
                principal=principal,
                namespace="castle-demo",
            ).resume(run_id, expected_revision=waiting["revision"], choice="continue")
        if (
            resumed["status"] != "completed"
            or len(requests) != 1
            or store.load_run(run_id).state["inputs"]["memory"] != frozen
        ):
            raise RuntimeError("walkthrough did not preserve frozen evidence")
        print(
            json.dumps(
                {
                    "enabled": True,
                    "executed": True,
                    "data": "synthetic notes only",
                    "model": "local fixture response, not an LLM",
                    "status_before_review": waiting["status"],
                    "status_after_resume": resumed["status"],
                    "memory_status": resumed["memory_status"],
                    "remembered_text": frozen["bundle"]["texts"],
                    "source_changed_after_pause": True,
                    "resumed_with_memory_disabled": True,
                    "frozen_snapshot_preserved": True,
                    "model_calls": len(requests),
                    "run_id": run_id,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
