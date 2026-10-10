"""TLS ingress on exact-owned resources; no retries or sticky user routing."""
import ipaddress
import json
import os
import re
from pathlib import Path
import ssl
import subprocess
import time
import httpx

IMAGE = 'nginx:1.28-alpine@sha256:a8b39bd9cf0f83869a2162827a0caf6137ddf759d50a171451b335cecc87d236'

def configuration(upstreams):
    addresses = [str(ipaddress.ip_address(address)) for address in upstreams]
    if len(addresses) != 2 or any(':' in address for address in addresses):
        raise ValueError('two IPv4 replica addresses required')
    servers = '\n'.join(f'        server {address}:8080;' for address in addresses)
    result = '''worker_processes 1;
pid /tmp/nginx.pid;
error_log /dev/null crit;
worker_shutdown_timeout 15s;
events { worker_connections 128; }
http {
    access_log off;
    server_tokens off;
    client_header_timeout 2s;
    client_body_timeout 2s;
    client_max_body_size 8k;
    large_client_header_buffers 2 8k;
    keepalive_timeout 5s;
    send_timeout 12s;
    client_body_temp_path /tmp/body;
    proxy_temp_path /tmp/proxy;
    fastcgi_temp_path /tmp/fastcgi;
    uwsgi_temp_path /tmp/uwsgi;
    scgi_temp_path /tmp/scgi;
    limit_conn_zone $server_name zone=connections:1m;
    upstream replicas {
'''+servers+'''
    }
    server {
        listen 8443 ssl;
        ssl_certificate /run/ingress/server.pem;
        ssl_certificate_key /run/ingress/server.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        limit_conn connections 64;
        limit_conn_status 503;
        location / {
            proxy_pass http://replicas;
            proxy_http_version 1.1;
            proxy_set_header Connection "close";
            proxy_set_header Host $host;
            proxy_set_header X-Tenant-ID "";
            proxy_set_header X-Actor-ID "";
            proxy_set_header X-Billing-Account-ID "";
            proxy_set_header Forwarded "";
            proxy_set_header X-Forwarded-For "";
            proxy_set_header X-Forwarded-Proto "https";
            proxy_request_buffering off;
            proxy_buffering off;
            proxy_next_upstream off;
            proxy_connect_timeout 2s;
            proxy_send_timeout 3s;
            proxy_read_timeout 12s;
            add_header X-Lab-Upstream $upstream_addr always;
        }
    }
}
'''
    # Exact route only. Preserve every ownership/header/timeout/no-retry setting.
    location = result.split('        location / {',1)[1].split('        }',1)[0]
    proposal = '        location = /workflow-proposals {\n            client_max_body_size 64k;' + location + '        }\n'
    return result.replace('        location / {',proposal+'        location / {',1)

def deliver():
    files = json.loads(Path('/run/source/ingress.json').read_text())
    if set(files) != {'server.pem','server.key','nginx.conf'}:
        raise ValueError('invalid ingress bundle')
    directory = Path('/run/ingress')
    for name,content in files.items():
        descriptor = os.open(directory/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
        with os.fdopen(descriptor,'w') as output:
            output.write(content)
            output.flush()
            os.fchmod(output.fileno(),0o400)
            os.fchown(output.fileno(),101,101)
            os.fsync(output.fileno())
    os.chmod(directory,0o700)
    os.chown(directory,101,101)

def start(stack):
    from .stack import command,EngineError
    from .keycloak import bundle
    command(stack.engine,'pull',IMAGE)
    addresses = []
    for replica in ('a','b'):
        state = json.loads(command(stack.engine,'inspect',stack.manifest['replica_ids'][replica]))[0]
        addresses.append(next(iter(state['NetworkSettings']['Networks'].values()))['IPAddress'])
    files,_,_,_ = bundle([])
    source = stack._secret('ingress.json',json.dumps({'server.pem':files['server.pem'],
        'server.key':files['server.key'],'nginx.conf':configuration(addresses)}))
    ca = stack._secret('ingress-ca.pem',files['ca.pem'])
    name = f'prosaic-lab-{stack.owner}-ingress'
    volume = stack._create('volume',name,'volume','create','--label',f'io.prosaic.lab.owner={stack.owner}',name)
    delivery = stack._create('container',name+'-delivery','create','--name',name+'-delivery',
        '--label',f'io.prosaic.lab.owner={stack.owner}','--network','none','--user','0',
        '--read-only','--cap-drop','ALL','--cap-add','CHOWN','--cap-add','DAC_OVERRIDE',
        '--security-opt','no-new-privileges','--memory','128m','--pids-limit','32',
        '-v',f'{source}:/run/source/ingress.json:ro','-v',f'{volume}:/run/ingress',
        stack.manifest['images']['consumer'],'python','-m','lab_runner.ingress')
    command(stack.engine,'start','-a',delivery)
    identifier = stack._create('container',name,'run','-d','--name',name,
        '--label',f'io.prosaic.lab.owner={stack.owner}','--network',stack.manifest['network_id'],
        '--user','101:101','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--memory','128m','--cpus','1','--pids-limit','32',
        '--tmpfs','/tmp:rw,noexec,nosuid,size=32m,mode=1777',
        '-v',f'{volume}:/run/ingress:ro','-p','127.0.0.1::8443',
        '--entrypoint','nginx',IMAGE,'-c','/run/ingress/nginx.conf','-g','daemon off;')
    state = json.loads(command(stack.engine,'inspect',identifier))[0]
    bindings = state['NetworkSettings']['Ports'].get('8443/tcp')
    if not bindings:
        result = subprocess.run([stack.engine,'logs',identifier],capture_output=True,text=True,timeout=5)
        logs = result.stdout+result.stderr
        # Fixed categories only: never export raw configuration/log contents.
        markers = ('Permission denied','Read-only file system','unknown directive',
            'cannot load certificate','bind()','invalid number','emerg')
        stack.manifest['ingress_start_failure'] = next((marker for marker in markers if marker in logs),'startup_failed')
        # Only predefined fixture file locations can accompany a category.
        stack.manifest['ingress_failure_paths'] = [path for path in (
            '/run/ingress/nginx.conf','/run/ingress/server.pem','/run/ingress/server.key',
            '/tmp','/var/cache/nginx','/var/log/nginx','/var/run') if path in logs]
        stack.manifest['ingress_failure_directives'] = [name for name in (
            'ssl_handshake_timeout','ssl_protocols','limit_conn','limit_conn_zone',
            'limit_conn_status','client_header_timeout','proxy_next_upstream',
            'worker_shutdown_timeout') if re.search('"'+name+'"',logs)]
        stack._save()
        raise EngineError('ingress failed before binding')
    port = bindings[0]['HostPort']
    config = {'url':f'https://127.0.0.1:{port}','ca_file':str(ca),'id':identifier}
    stack.manifest['images']['ingress'] = IMAGE
    stack.manifest['ingress_id'] = identifier
    stack._save()
    deadline = time.monotonic()+20
    with httpx.Client(verify=ssl.create_default_context(cafile=str(ca)),trust_env=False,timeout=2) as client:
        while time.monotonic() < deadline:
            try:
                if client.get(config['url']+'/readyz').status_code == 200: return config
            except httpx.HTTPError: pass
            time.sleep(.2)
    raise EngineError('ingress readiness timeout')

if __name__ == '__main__': deliver()
