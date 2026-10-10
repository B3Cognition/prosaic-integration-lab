"""Private deployment inputs cannot fall back to fixture success or network."""
import httpx
import pytest
import time
import datetime
import jwt
import ipaddress

@pytest.fixture
def private_config(tmp_path):
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization,hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'qualification test CA')])
    now=datetime.datetime.now(datetime.UTC)
    ca=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(1).not_valid_before(now-datetime.timedelta(minutes=1))
        .not_valid_after(now+datetime.timedelta(hours=1)).add_extension(x509.BasicConstraints(ca=True,path_length=None),True)
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),False)
        .sign(key,hashes.SHA256())).public_bytes(serialization.Encoding.PEM)
    token=jwt.encode({'iss':'https://issuer.example','aud':'qualification','iat':int(time.time()),
        'exp':int(time.time())+30},key,algorithm='RS256').encode()
    values={'token_file':token,'ca_file':ca,'signing_key_file':key.public_key().public_bytes(
        serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)}
    result={'version':1,'suite':'deployment-staging-v1','origin':'https://deployment.example',
        'approved_origins':['https://deployment.example'],'issuer':'https://issuer.example','audience':'qualification',
        'maximum_token_lifetime_s':60,'maximum_calls':1,'duration_s':5,'maximum_report_bytes':4096,
        'cases':{name:{'passed':True,'evidence_sha256':'a'*64,'observed_at':time.time()}
            for name in ('rotation','outage','backend_isolation','drain')}}
    for name,value in values.items():
        path=tmp_path/name;path.write_bytes(value);path.chmod(0o600);result[name]=str(path)
    server_key=tmp_path/'fixture-server-key.pem'
    server_key.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()));server_key.chmod(0o600)
    return result

@pytest.mark.parametrize('scenario',['body','headers'])
def test_staging_wall_deadline_and_zero_body_consumption_with_real_owned_https(private_config,tmp_path,scenario):
    """Frequent bytes must not turn the inactivity timeout into unlimited time."""
    import socket
    import ssl
    import threading
    from lab_runner.staging_qualification import run
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(5)
    port=listener.getsockname()[1];stop=threading.Event();closed=threading.Event();errors=[]
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(private_config['ca_file'],str(tmp_path/'fixture-server-key.pem'))
    def server():
        try:
            connection,_=listener.accept()
            with context.wrap_socket(connection,server_side=True) as secure:
                secure.settimeout(3);secure.recv(8192)
                if scenario=='body':
                    secure.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 1310720\r\n\r\n')
                    for _ in range(20):
                        if stop.wait(.1):break
                        secure.sendall(b'x'*65536)
                else:
                    # Keep the header read active for 2s with 50ms arrivals.
                    secure.sendall(b'HTTP/1.1 200 OK\r\nX-Fixture: ')
                    for _ in range(40):
                        if stop.wait(.05):break
                        secure.sendall(b'x')
                    secure.sendall(b'\r\nContent-Length: 0\r\n\r\n')
        except (BrokenPipeError,ConnectionResetError,ssl.SSLError):pass
        except Exception as error:errors.append(type(error).__name__)
        finally:closed.set()
    worker=threading.Thread(target=server,daemon=True);worker.start()
    private_config.update(origin=f'https://127.0.0.1:{port}',approved_origins=[f'https://127.0.0.1:{port}'],duration_s=1)
    began=time.monotonic()
    try:
        result=run(private_config,enabled=True);elapsed=time.monotonic()-began
        assert elapsed<1.5
        assert result['response_bytes']==0
        if scenario=='body':assert result['qualification']=='qualified'
        else:
            assert result['qualification']=='not_qualified'
            assert result['reason']=='deployment_deadline_exceeded'
    finally:
        stop.set();listener.close();worker.join(3)
    assert closed.is_set() and not errors

@pytest.mark.parametrize('mutation',['origin','permissions','issuer','missing_case'])
def test_private_inputs_are_checked_before_network(monkeypatch,private_config,mutation):
    from pathlib import Path
    from lab_runner.staging_qualification import run
    if mutation=='origin':private_config['origin']='https://unapproved.example'
    elif mutation=='issuer':private_config['issuer']='https://wrong-issuer.example'
    elif mutation=='permissions':Path(private_config['token_file']).chmod(0o644)
    else:private_config['cases'].pop('drain')
    monkeypatch.setattr(httpx,'Client',lambda *a,**k:(_ for _ in ()).throw(AssertionError('network')))
    monkeypatch.setattr(httpx,'AsyncClient',lambda *a,**k:(_ for _ in ()).throw(AssertionError('network')))
    result=run(private_config,enabled=True)
    assert result['qualification']=='not_qualified' and result['reason']=='missing_deployment_inputs'

@pytest.mark.parametrize('status,reason,qualified',[(200,'operator_observations_verified',True),
    (302,'redirect_rejected',False),(503,'deployment_cases_failed',False)])
def test_staging_reads_only_approved_origin_and_rejects_redirects(monkeypatch,private_config,status,reason,qualified):
    from lab_runner.staging_qualification import run
    seen=[]
    def response(request):
        seen.append(str(request.url))
        return httpx.Response(status,headers={'Location':'https://unapproved.example/secret'},json={})
    real_client=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:real_client(transport=httpx.MockTransport(response),**kwargs))
    result=run(private_config,enabled=True)
    assert result['reason']==reason and result['qualified'] is qualified
    assert seen==['https://deployment.example/readyz']
    assert 'deployment.example' not in str(result) and 'issuer.example' not in str(result)

def test_staging_closes_stream_without_reading_or_buffering_body(monkeypatch,private_config):
    import asyncio
    from lab_runner.staging_qualification import run
    class Trickle(httpx.AsyncByteStream):
        reads=0
        closed=False
        async def __aiter__(self):
            for _ in range(20):
                self.reads+=1
                await asyncio.sleep(.5)
                yield b'x'*65536
        async def aclose(self):self.closed=True
    stream=Trickle();clients=[]
    real_client=httpx.AsyncClient
    def client(**kwargs):
        created=real_client(transport=httpx.MockTransport(lambda _:httpx.Response(200,stream=stream)),**kwargs)
        clients.append(created);return created
    monkeypatch.setattr(httpx,'AsyncClient',client)
    result=run(private_config,enabled=True)
    assert result['qualified'] is True and result['response_bytes']==0
    assert stream.reads==0 and stream.closed is True
    assert len(clients)==1 and clients[0].is_closed is True

def test_missing_staging_configuration_is_not_fixture_success(monkeypatch):
    from lab_runner.staging_qualification import run
    monkeypatch.setattr(httpx.Client,'request',lambda *a,**k:(_ for _ in ()).throw(AssertionError('network')))
    result=run(None,enabled=True)
    assert result['qualification']=='not_qualified'
    assert result['reason']=='missing_deployment_inputs'

def test_disabled_staging_does_not_read_private_inputs_or_open_client(monkeypatch):
    from lab_runner.staging_qualification import run
    monkeypatch.setattr(httpx,'Client',lambda *a,**k:(_ for _ in ()).throw(AssertionError('network')))
    assert run({'origin':'https://private.example'},enabled=False)['reason']=='staging_disabled'

def test_incomplete_staging_inputs_are_redacted_before_network(monkeypatch):
    from lab_runner.staging_qualification import run
    monkeypatch.setattr(httpx,'Client',lambda *a,**k:(_ for _ in ()).throw(AssertionError('network')))
    result=run({'origin':'https://private.example','token':'secret'},enabled=True)
    assert result['qualification']=='not_qualified'
    assert 'private' not in str(result) and 'secret' not in str(result)
