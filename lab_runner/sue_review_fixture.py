"""Explicit installed SUE qualification; disabled invocation allocates nothing."""

import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import threading
from xml.etree import ElementTree
from zipfile import ZipFile


ENGINE_SHA256 = "fdfb1690505a85b4cbb49e2b4845c91e318efe945068a379ac230c3b4ebf9b75"
SOURCE_LINE = "Only administrators may export data. 🙂"
CLAIM = "Administrators export with current consent."
# Independently scripted euthyphro success, rather than deriving expected
# responses by running the implementation under test.
SUCCESS = (
    ("definition", "ESTABLISHED"),
    ("distinction", "ESTABLISHED"),
    ("criterion", "ESTABLISHED"),
    ("case-split", "ESTABLISHED"),
    ("example", "NOT_FOUND"),
    ("consequence", "CONSISTENT"),
    ("consequence", "EXCLUDED"),
)


@contextmanager
def model_fixture(*, usage=True, first_response_gate=None):
    """Own a bounded loopback responder; it possesses no inference credentials."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1048576 or len(requests) >= len(SUCCESS):
                self.send_error(413)
                return
            requests.append(json.loads(self.rfile.read(length)))
            if len(requests) == 1 and first_response_gate is not None:
                if not first_response_gate.wait(30):
                    self.send_error(504)
                    return
            answer_type, result = SUCCESS[len(requests) - 1]
            answer = {
                "answer": "An attributed interpretation requiring review.",
                "verdict": "SUPPORTED", "answer_type": answer_type,
                "evidence_lines": [1], "claim": CLAIM if len(requests) == 1 else None,
                "test_result": result, "evidence": [{"line": 1, "quote": SOURCE_LINE}],
                "premises": [{"statement": SOURCE_LINE, "kind": "stated", "evidence_lines": [1]}],
                "witness": None, "open_questions": [], "addresses": [], "revision_reason": None,
            }
            body = {"id": "sue-fixture", "model": "sue-fixture", "choices": [{"index": 0,
                "message": {"role": "assistant", "content": json.dumps(answer)}, "finish_reason": "stop"}]}
            if usage:
                body["usage"] = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            data = json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
        if thread.is_alive():
            raise RuntimeError("SUE model fixture cleanup failed")


def verify_installed_wheel(path, distribution, prefixes, *, expected_sha=None):
    """Bind executed installed payloads to the exact supplied wheel bytes."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha is not None and digest != expected_sha:
        raise ValueError("qualification wheel checksum mismatch")
    installed = importlib.metadata.distribution(distribution)
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.startswith(prefixes) and not name.endswith("/")]
        if not names:
            raise ValueError("qualification wheel payload missing")
        for name in names:
            if installed.locate_file(name).read_bytes() != archive.read(name):
                raise ValueError("installed payload differs from qualification wheel")
    return {"distribution": distribution, "version": installed.version, "sha256": digest}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--postgres-version", type=int, choices=(16, 18), default=16)
    parser.add_argument("--tests", type=Path)
    parser.add_argument("--lab-wheel", type=Path)
    parser.add_argument("--engine-wheel", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.enable:
        print(json.dumps({"enabled": False, "qualified": False, "reason": "disabled"}))
        return 0
    if not all((args.tests, args.lab_wheel, args.engine_wheel, args.output)):
        parser.error("enable requires tests, lab-wheel, engine-wheel and output")
    tests = args.tests.resolve(strict=True)
    result = {"enabled": True, "qualified": False, "synthetic_only": True, "private_state_exported": False}
    fixture = None
    try:
        result["artifacts"] = [
            verify_installed_wheel(args.lab_wheel, "prosaic-integration-lab", ("prosaic_integration_lab/", "lab_runner/")),
            verify_installed_wheel(args.engine_wheel, "cognitive-castle-sue", ("castle_sue/",), expected_sha=ENGINE_SHA256),
        ]
        from .memory_fixture import OwnedPostgres

        fixture = OwnedPostgres(args.postgres_version)
        fixture.manifest["qualification"] = "optional-sue-review"
        with fixture, tempfile.TemporaryDirectory(prefix="lab-sue-qualification-") as directory:
            architecture = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64", "AMD64": "amd64"}.get(platform.machine())
            if (architecture is None or fixture.manifest["architecture"] != architecture
                    or fixture.manifest["server_version"].split(".")[0] != str(args.postgres_version)):
                raise ValueError("owned PostgreSQL platform/version mismatch")
            fixture.manifest["host_architecture"] = architecture
            root = Path(directory)
            settings = root / "fixture.json"
            settings.write_text(json.dumps({"dsn": fixture.dsn}))
            settings.chmod(0o600)
            junit = root / "result.xml"
            # Neutral cwd, no repository pythonpath/config/conftests: only the
            # installed Lab/SDK code is reachable by qualification subprocesses.
            run = subprocess.run([
                sys.executable, "-I", "-m", "pytest", str(tests), "-c", os.devnull,
                "--rootdir", str(root), "--confcutdir", str(root), "--import-mode=importlib",
                "-o", "pythonpath=", "-q", "--junitxml", str(junit),
            ], cwd=root, env={**os.environ, "LAB_SUE_FIXTURE": str(settings)},
                capture_output=True, text=True, timeout=240)
            if junit.exists():
                suites = ElementTree.parse(junit).getroot()
                result.update({key: sum(int(s.get(attribute, "0")) for s in suites.iter("testsuite"))
                    for key, attribute in (("tests", "tests"), ("skipped", "skipped"), ("failures", "failures"), ("errors", "errors"))})
                result["failed_tests"] = [case.get("name") for case in suites.iter("testcase")
                    if case.find("failure") is not None or case.find("error") is not None]
            result["qualified"] = run.returncode == 0 and result.get("tests", 0) >= 14 and result.get("skipped") == 0
            if run.returncode:
                sys.stderr.write("SUE acceptance failed; only sanitized case identities are exported\n")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, importlib.metadata.PackageNotFoundError):
        result["reason"] = "required_qualification_failed"
    finally:
        if fixture is not None:
            result["postgres"] = fixture.manifest
            result["qualified"] = result["qualified"] and fixture.manifest["cleanup_verified"]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
