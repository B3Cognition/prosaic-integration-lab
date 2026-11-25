from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
import uuid

from prosaic_harness import FileRunStore
from prosaic_runtime import EndpointConfig, RuntimeConfig
from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.memory_provider import MemoryProviders
from prosaic_integration_lab.memory_workflow import MemoryWorkflowSession


@contextmanager
def model_fixture(status):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            requests.append(
                json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            )
            body = json.dumps(
                {
                    "id": "memory-fixture",
                    "model": "memory-fixture",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(
                                    {
                                        "answer": "fixture answer",
                                        "memory_status": status,
                                    }
                                ),
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
        assert not thread.is_alive()


def test_new_process_resume_uses_persisted_snapshot_without_recapture(tmp_path):
    frozen = {
        "status": "available",
        "bundle": {
            "texts": ["Original evidence 🙂\r\n"],
            "sources": [{"record_id": "one"}],
        },
    }

    class Capture:
        calls = 0

        def capture(self, *args, **kwargs):
            self.calls += 1
            return frozen

    capture = Capture()
    run_id = uuid.uuid4().hex
    owner = Principal("tenant", "alice", "payer")
    with model_fixture("available") as (url, requests):
        config = RuntimeConfig(
            {
                "fixture": EndpointConfig(
                    url, "memory-fixture", features={"streaming": False}
                )
            },
            {},
            "fixture",
        )
        with FileRunStore(tmp_path / "runs", namespace="memory-functional") as store:
            session = MemoryWorkflowSession(
                providers=capture,
                store=store,
                config=config,
                principal=owner,
                namespace="memory-functional",
            )
            waiting = session.start(run_id, task="What was recorded?", query="evidence")
            assert (
                waiting["status"] == "waiting" and not requests and capture.calls == 1
            )
        frozen["bundle"]["texts"][0] = "Changed source after capture"
        host = {
            "namespace": "memory-functional",
            "principal": vars(owner),
            "memory": {"enabled": False},
            "runtime": {"base_url": url, "model": "memory-fixture"},
            "store": {"kind": "file", "path": str(tmp_path / "runs")},
        }
        path = tmp_path / "host.json"
        path.write_text(json.dumps(host))
        path.chmod(0o600)
        command = [
            sys.executable,
            "-I",
            "-c",
            "import runpy,sys; from pathlib import Path; "
            "root=Path(sys.argv.pop(1)); sys.path[:0]=[str(root/'src'),str(root)]; "
            "runpy.run_module('lab_runner.memory_workflow',run_name='__main__')",
            str(Path(__file__).resolve().parents[2]),
            "resume",
            "--config",
            str(path),
            "--run-id",
            run_id,
            "--expected-revision",
            waiting["revision"],
            "--choice",
            "continue",
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr + result.stdout
        assert json.loads(result.stdout)["status"] == "completed"
        assert len(requests) == 1 and capture.calls == 1
        messages = requests[0]["messages"]
        assert any(
            "Original evidence" in m.get("content", "")
            for m in messages
            if m["role"] == "user"
        )
        assert all(
            "Original evidence" not in m.get("content", "")
            for m in messages
            if m["role"] == "system"
        )
        assert "Changed source" not in json.dumps(messages)
        replay = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert replay.returncode in (0, 5) and len(requests) == 1


def test_model_cannot_claim_available_memory_when_frozen_status_is_disabled(tmp_path):
    with (
        model_fixture("available") as (url, requests),
        FileRunStore(tmp_path / "runs", namespace="memory-functional") as store,
    ):
        session = MemoryWorkflowSession(
            providers=MemoryProviders(),
            store=store,
            config=RuntimeConfig(
                {
                    "fixture": EndpointConfig(
                        url, "memory-fixture", features={"streaming": False}
                    )
                },
                {},
                "fixture",
            ),
            principal=Principal("tenant", "alice", "payer"),
            namespace="memory-functional",
        )
        run_id = uuid.uuid4().hex
        waiting = session.start(run_id, task="Explain missing context", query="history")
        result = session.resume(
            run_id, expected_revision=waiting["revision"], choice="continue"
        )
        assert result["status"] == "blocked" and result["memory_status"] == "disabled"
        assert result["answer"] is None and len(requests) == 1
