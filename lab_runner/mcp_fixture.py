"""Loopback-only synthetic MCP fixtures for installed consumer qualification."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
from threading import Thread
from time import monotonic, sleep
from typing_extensions import TypedDict

MODERN = "2026-07-28"
LEGACY = "2025-11-25"
SCHEMA = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}


class Count(TypedDict):
    count: int


@contextmanager
def sdk_endpoint(*, text=False):
    """Exercise real SDK server schemas, routing, and result serialization."""
    from mcp.server.mcpserver import MCPServer
    import uvicorn

    effects = []
    server = MCPServer("lab-graph", version="1")

    if text:
        @server.tool(name="lookup", structured_output=False)
        def lookup_text(name: str) -> str:
            effects.append(name)
            return "14 dependents"
    else:
        @server.tool(name="lookup", structured_output=True)
        def lookup(name: str) -> Count:
            effects.append(name)
            return {"count": 14}

    methods = []
    app = server.streamable_http_app(json_response=True)

    async def tracked(scope, receive, send):
        async def read():
            message = await receive()
            if message["type"] == "http.request" and not message.get("more_body"):
                data = message.get("body", b"")
                if data:
                    methods.append(json.loads(data)["method"])
            return message
        await app(scope, read, send)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        worker = uvicorn.Server(uvicorn.Config(tracked, log_level="error", lifespan="on",
                                              timeout_graceful_shutdown=2))
        thread = Thread(target=worker.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        try:
            deadline = monotonic() + 5
            while not worker.started and thread.is_alive() and monotonic() < deadline:
                sleep(0.01)
            assert worker.started
            yield f"http://127.0.0.1:{port}/mcp", methods, effects
        finally:
            worker.should_exit = True
            thread.join(5)
            assert not thread.is_alive()


@contextmanager
def fault_endpoint(case, grant):
    methods, effects = [], []
    listed = 0

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            nonlocal listed
            if self.path != "/mcp":
                self.send_error(404)
                return
            size = int(self.headers["Content-Length"])
            if not 0 < size <= 32768:
                self.send_error(413)
                return
            request = json.loads(self.rfile.read(size))
            method = request["method"]
            methods.append(method)
            if method == "tools/list":
                listed += 1
                schema = SCHEMA
                if listed == 2 and case == "revocation-during-listing":
                    grant[0] = False
                if listed == 2 and case == "catalogue-drift":
                    schema = {**SCHEMA, "maxProperties": 1}
                value = {"tools": [{"name": "lookup", "inputSchema": schema}],
                         "cacheScope": "private", "resultType": "complete", "ttlMs": 0}
            elif method == "tools/call":
                effects.append(request["params"]["arguments"]["name"])
                if case == "uncertain-dispatch":
                    self.close_connection = True
                    return
                value = {"resultType": "complete", "structuredContent": {"count": 14},
                         "content": [], "isError": False}
            else:
                self.send_error(400)
                return
            body = json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": value}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/mcp", methods, effects
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)
        assert not thread.is_alive()
