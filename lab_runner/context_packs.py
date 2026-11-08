"""Synthetic public-SDK qualification helpers; no paid model or copied engine."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from threading import Thread


def require_candidate_install(manifest):
    """Audit host SDK bytes as well as the consumer image before any resources."""
    from pathlib import Path
    import runpy
    from prosaic_integration_lab.dependencies import sdk_manifest,cache_directory
    root=Path(__file__).resolve().parents[1]
    sdk_manifest(manifest)
    audit=runpy.run_path(str(root/'scripts/audit_install.py'))['audit']
    audit(manifest,cache_directory(manifest,root/'.cache/wheels'))


def answer(text):
    return {'model':'synthetic-context-packs','choices':[{'message':{'role':'assistant','content':text},'finish_reason':'stop'}],
        'usage':{'prompt_tokens':3,'completion_tokens':2,'total_tokens':5}}


def read_answer(citation):
    return {'model':'synthetic-context-packs','choices':[{'message':{'role':'assistant','content':None,
        'tool_calls':[{'id':'read-1','type':'function','function':{'name':'read_context_item','arguments':json.dumps({'citationId':citation})}}]},
        'finish_reason':'tool_calls'}],'usage':{'prompt_tokens':3,'completion_tokens':2,'total_tokens':5}}


@contextmanager
def endpoint():
    requests,replies=[],[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            if not replies:
                self.send_error(500,'unexpected synthetic provider call');return
            encoded=json.dumps(replies.pop(0)).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(encoded)));self.end_headers();self.wfile.write(encoded)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try: yield f'http://127.0.0.1:{server.server_port}/v1',requests,replies
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        assert not thread.is_alive()
