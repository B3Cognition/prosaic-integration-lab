"""Private deployment inputs cannot fall back to fixture success or network."""
import httpx
import pytest
import time
import datetime
import jwt

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
    return result

@pytest.mark.parametrize('mutation',['origin','permissions','issuer','missing_case'])
def test_private_inputs_are_checked_before_network(monkeypatch,private_config,mutation):
    from pathlib import Path
    from lab_runner.staging_qualification import run
    if mutation=='origin':private_config['origin']='https://unapproved.example'
    elif mutation=='issuer':private_config['issuer']='https://wrong-issuer.example'
    elif mutation=='permissions':Path(private_config['token_file']).chmod(0o644)
    else:private_config['cases'].pop('drain')
    monkeypatch.setattr(httpx,'Client',lambda *a,**k:(_ for _ in ()).throw(AssertionError('network')))
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
    real_client=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:real_client(transport=httpx.MockTransport(response),**kwargs))
    result=run(private_config,enabled=True)
    assert result['reason']==reason and result['qualified'] is qualified
    assert seen==['https://deployment.example/readyz']
    assert 'deployment.example' not in str(result) and 'issuer.example' not in str(result)

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
