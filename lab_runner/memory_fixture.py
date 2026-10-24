"""Owned synthetic PostgreSQL/model/Castle qualification; no shared resources."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
import uuid

from .manifest import validate_resource
from .stack import command


PREPARE = r"""
import json,sys
from pathlib import Path
from cognitive_castle.config import CognitiveCastleConfig
from cognitive_castle.backends.lancedb_backend import LanceDBBackend
from cognitive_castle.context import PalacePaths
from cognitive_castle.provider_setup import prepare_provider
root=Path(sys.argv[1]); root.mkdir(parents=True,exist_ok=True)
cfgdir=root/'config'; cfgdir.mkdir(exist_ok=True)
(cfgdir/'config.json').write_text(json.dumps({'embedder_dim':4,'embedder_model':'synthetic','embedding_device':'cpu'}))
cfg=CognitiveCastleConfig(config_dir=cfgdir)
backend=LanceDBBackend(cfg=cfg)
col=backend.get_collection(str(root/'palace'),collection_name='castle_drawers',create=True)
text='Atlas chose SQLite for offline persistence. 🙂\r\nExact original evidence.\r\n'
if len(sys.argv)>2: text='Changed source: Atlas now chose PostgreSQL.'
col.upsert(ids=['own','foreign','partial'],documents=[text,'SQLite foreign secret','SQLite unpublished draft'],
 metadatas=[{'wing':'approved','source_file':'fixture://atlas','representation':'project','source_revision':'v2' if len(sys.argv)>2 else 'v1'},
 {'wing':'denied'},{'wing':'approved','ingest_complete':False}],embeddings=[[0.0]*4]*3)
backend.close()
prepare_provider(PalacePaths.resolve(root/'palace'),namespace='owner-memory',config=cfg)
"""

READ_GUARD = r"""
import importlib.abc, runpy, socket, sys
from pathlib import Path
marker=Path(sys.argv.pop(1))
sys.argv[0]='castle-provider'
def forbidden(value):
    marker.write_text(value)
    raise RuntimeError('qualification forbids '+value)
class ReadGuard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch','sentence_transformers','spacy','sml'} or fullname.startswith((
            'cognitive_castle.sue','cognitive_castle.soar','cognitive_castle.brain',
            'cognitive_castle.understanding','cognitive_castle.quality',
            'cognitive_castle.llm','cognitive_castle.judge',
            'cognitive_castle.embedding','cognitive_castle.reranker')):
            forbidden('import:'+fullname)
sys.meta_path.insert(0,ReadGuard())
def no_network(*args,**kwargs): forbidden('network')
socket.socket.connect=no_network
socket.create_connection=no_network
runpy.run_module('cognitive_castle.provider_worker',run_name='__main__')
"""


WORKER_PROXY = "READ_GUARD=" + repr(READ_GUARD) + "\n" + r"""
import json,os,signal,subprocess,sys
from pathlib import Path
trace=Path(sys.argv[1])
child=subprocess.Popen([sys.executable,'-I','-c',READ_GUARD,str(trace.with_suffix('.forbidden'))]+sys.argv[2:],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
trace.with_suffix('.pid').write_text(str(child.pid))
def stop(*args):
    if child.poll() is None:
        child.terminate()
        try: child.wait(timeout=1)
        except subprocess.TimeoutExpired: child.kill(); child.wait(timeout=1)
    if args: raise SystemExit(0)
signal.signal(signal.SIGTERM,stop)
try:
    for frame in sys.stdin.buffer:
        op=json.loads(frame)['op']
        with trace.open('a') as output: output.write(op+'\n')
        child.stdin.write(frame); child.stdin.flush()
        answer=child.stdout.readline(1048577)
        if not answer: break
        sys.stdout.buffer.write(answer); sys.stdout.buffer.flush()
finally: stop()
"""


@contextmanager
def model_fixture(status):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            length = int(self.headers["Content-Length"])
            if length > 131072:
                self.send_error(413)
                return
            requests.append(json.loads(self.rfile.read(length)))
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
                                        "answer": "Synthetic evidence answer",
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
        if thread.is_alive():
            raise RuntimeError("model fixture cleanup failed")


def prepare_castle(worker_python, root, *, mutate=False):
    result = subprocess.run(
        [worker_python, "-I", "-c", PREPARE, str(root)]
        + (["mutate"] if mutate else []),
        env={
            **os.environ,
            "HOME": str(root / "home"),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        },
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError("synthetic Castle preparation failed")


def memory_settings(worker_python, root):
    root.mkdir(parents=True, exist_ok=True)
    proxy = root / "worker_proxy.py"
    proxy.write_text(WORKER_PROXY)
    return {
        "enabled": True,
        "bindings": [
            {
                "tenant_id": "tenant-a",
                "actor_id": "alice",
                "billing_account_id": "payer-a",
                "namespace": "owner-memory",
                "palace_path": str(root / "palace"),
                "config_path": str(root / "config/config.json"),
                "worker_command": [
                    worker_python,
                    "-I",
                    str(proxy),
                    str(root / "operations.log"),
                ],
                "allowed_wings": ["approved"],
                "startup_timeout": 10,
                "operation_timeout": 10,
            }
        ],
    }


class OwnedPostgres:
    def __init__(self, major=16):
        if major not in (16, 18):
            raise ValueError("unsupported fixture version")
        self.major, self.owner, self.container = major, uuid.uuid4().hex, None
        self.manifest = {
            "owner": self.owner,
            "kind": "optional-memory",
            "cleanup_verified": False,
        }

    def __enter__(self):
        import psycopg
        from psycopg import sql
        from prosaic_runtime import RateCard
        from prosaic_runtime_postgres import PostgresRecorder

        image = json.loads(
            command("docker", "image", "inspect", f"postgres:{self.major}")
        )[0]
        self.manifest.update(image_id=image["Id"], architecture=image["Architecture"])
        password = secrets.token_hex(16)
        mount = (
            "/var/lib/postgresql/data" if self.major == 16 else "/var/lib/postgresql"
        )
        try:
            self.container = command(
                "docker",
                "run",
                "--detach",
                "--label",
                f"io.prosaic.lab.owner={self.owner}",
                "--label",
                "io.prosaic.lab.resource=optional-memory-postgres",
                "--publish",
                "127.0.0.1::5432",
                "--tmpfs",
                mount,
                "--env",
                "POSTGRES_DB=memory_fixture",
                "--env",
                "POSTGRES_USER=fixture_owner",
                "--env",
                f"POSTGRES_PASSWORD={password}",
                image["Id"],
            )
            state = json.loads(command("docker", "inspect", self.container))[0]
            validate_resource(state, self.container, self.owner)
            binding = state["NetworkSettings"]["Ports"]["5432/tcp"][0]
            if binding["HostIp"] != "127.0.0.1":
                raise RuntimeError("fixture must bind loopback")
            self.manifest["container_id"] = self.container
            owner_dsn = f"host=127.0.0.1 port={binding['HostPort']} dbname=memory_fixture user=fixture_owner password={password}"
            deadline = time.monotonic() + 30
            while True:
                try:
                    with psycopg.connect(owner_dsn, connect_timeout=1) as connection:
                        connection.execute("SELECT 1")
                    break
                except psycopg.Error:
                    if time.monotonic() > deadline:
                        raise RuntimeError("owned database readiness failed") from None
                    time.sleep(0.1)
            migration = subprocess.run(
                [
                    str(Path(sys.executable).parent / "prosaic-harness-postgres"),
                    "init",
                    "--dsn-env",
                    "LAB_MEMORY_OWNER_DSN",
                ],
                env={**os.environ, "LAB_MEMORY_OWNER_DSN": owner_dsn},
                capture_output=True,
                timeout=30,
            )
            if migration.returncode:
                raise RuntimeError("owned Harness migration failed")
            PostgresRecorder(
                owner_dsn,
                namespace="memory-qualification",
                environment="sandbox",
                rate_card=RateCard(
                    "memory-fixture-v1", "memory-fixture", "2", "8", "0.5"
                ),
            ).initialize()
            runtime_password = secrets.token_hex(16)
            with psycopg.connect(owner_dsn) as connection:
                connection.execute(
                    sql.SQL("CREATE ROLE memory_runtime LOGIN PASSWORD {}").format(
                        sql.Literal(runtime_password)
                    )
                )
                connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
                connection.execute(
                    "GRANT USAGE ON SCHEMA public,prosaic_harness TO memory_runtime"
                )
                connection.execute(
                    "GRANT SELECT ON prosaic_harness.schema_version,prosaic_harness.leases,prosaic_harness.runs,prosaic_harness.receipts TO memory_runtime"
                )
                connection.execute(
                    "GRANT INSERT,UPDATE ON prosaic_harness.leases,prosaic_harness.runs TO memory_runtime"
                )
                connection.execute(
                    "GRANT INSERT ON prosaic_harness.receipts TO memory_runtime"
                )
                connection.execute(
                    "GRANT SELECT,INSERT ON prosaic_metering_intents,prosaic_metering_observations TO memory_runtime"
                )
                connection.execute(
                    "GRANT UPDATE ON prosaic_metering_intents TO memory_runtime"
                )
            self.dsn = owner_dsn.replace(
                "user=fixture_owner", "user=memory_runtime"
            ).replace(password, runtime_password)
            with psycopg.connect(self.dsn) as connection:
                self.manifest["server_version"] = connection.execute(
                    "SHOW server_version"
                ).fetchone()[0]
                assert (
                    connection.execute(
                        "SELECT has_schema_privilege(current_user,'public','CREATE')"
                    ).fetchone()[0]
                    is False
                )
            self.manifest["separate_runtime_role"] = True
            return self
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.container is None:
            # Recover a create whose CLI outcome was lost, using both unique labels.
            owned = command(
                "docker",
                "ps",
                "--all",
                "--quiet",
                "--no-trunc",
                "--filter",
                f"label=io.prosaic.lab.owner={self.owner}",
                "--filter",
                "label=io.prosaic.lab.resource=optional-memory-postgres",
            ).splitlines()
            if len(owned) > 1:
                raise RuntimeError("ambiguous owned fixture identity")
            self.container = owned[0] if owned else None
        if self.container is not None:
            state = json.loads(command("docker", "inspect", self.container))[0]
            validate_resource(state, self.container, self.owner)
            if (
                state["Config"]["Labels"].get("io.prosaic.lab.resource")
                != "optional-memory-postgres"
            ):
                raise ValueError("fixture resource label mismatch")
            command("docker", "rm", "--force", "--volumes", self.container)
            check = subprocess.run(
                ["docker", "inspect", self.container], capture_output=True, timeout=10
            )
            if check.returncode == 0:
                raise RuntimeError("owned database cleanup failed")
            self.manifest["cleanup_verified"] = True
            self.container = None

    def __exit__(self, *args):
        self.close()
