"""Owned TLS Keycloak reference fixture; never contacts an existing deployment."""
from datetime import datetime,timedelta,timezone
import ipaddress
import json
import os
from pathlib import Path
import secrets
import ssl
import time
import uuid
import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

def bundle(identities):
    key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'owned-lab-issuer')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
        .not_valid_after(now+timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName('issuer'),x509.DNSName('localhost'),
            x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).sign(key,hashes.SHA256()))
    pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    client_secret = secrets.token_hex(24)
    users,bindings,passwords = [],{},{}
    for principal in identities:
        subject,password = str(uuid.uuid4()),secrets.token_hex(24)
        users.append({'id':subject,'username':principal['actor_id'],'enabled':True,'emailVerified':True,
            'firstName':'Fixture','lastName':'User','email':principal['actor_id']+'@fixture.invalid',
            'credentials':[{'type':'password','value':password,'temporary':False}]})
        bindings[subject] = principal
        passwords[principal['actor_id']] = password
    realm = {'realm':'prosaic-lab','enabled':True,'sslRequired':'all','accessTokenLifespan':120,
        'users':users,'clients':[{'clientId':'integration-lab','secret':client_secret,'publicClient':False,
            'enabled':True,'directAccessGrantsEnabled':True,'standardFlowEnabled':False,
            'protocol':'openid-connect','protocolMappers':[
                {'name':'api-audience','protocol':'openid-connect','protocolMapper':'oidc-audience-mapper',
                    'config':{'included.client.audience':'integration-lab','access.token.claim':'true','id.token.claim':'false'}},
                {'name':'spoof-billing','protocol':'openid-connect','protocolMapper':'oidc-hardcoded-claim-mapper',
                    'config':{'claim.name':'billing_account_id','claim.value':'SPOOF','jsonType.label':'String',
                        'access.token.claim':'true','id.token.claim':'false'}}]}]}
    files = {'realm.json':json.dumps(realm),'server.pem':pem,'ca.pem':pem,
        'server.key':key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()).decode()}
    return files,bindings,passwords,client_secret

def deliver():
    files = json.loads(Path('/run/source/keycloak-bundle.json').read_text())
    if set(files) != {'realm.json','server.pem','server.key','ca.pem'}:
        raise ValueError('invalid issuer fixture bundle')
    directory = Path('/run/keycloak')
    for name,content in files.items():
        descriptor = os.open(directory/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
        with os.fdopen(descriptor,'w') as output:
            output.write(content)
            output.flush()
            os.fchmod(output.fileno(),0o400)
            os.fchown(output.fileno(),1000,1000)
    os.chmod(directory,0o700)
    os.chown(directory,1000,1000)

def start(stack,container_config,host_config):
    from .stack import command,EngineError
    files,bindings,passwords,client_secret = bundle(stack.identities)
    admin_password = secrets.token_hex(24)
    stack._secret('keycloak-bundle.json',json.dumps(files))
    ca = stack._secret('issuer-ca.pem',files['ca.pem'])
    name = f'prosaic-lab-{stack.owner}-issuer'
    image = json.loads((Path(__file__).resolve().parents[1]/'dependencies/images.json').read_text())['keycloak']
    command(stack.engine,'pull',image)
    volume = stack._create('volume',name+'-config','volume','create','--label',
        f'io.prosaic.lab.owner={stack.owner}',name+'-config')
    job = stack._create('container',name+'-delivery','create','--name',name+'-delivery','--label',
        f'io.prosaic.lab.owner={stack.owner}','--network','none','--user','0','--read-only',
        '--cap-drop','ALL','--cap-add','CHOWN','--cap-add','DAC_OVERRIDE','--security-opt','no-new-privileges',
        '--memory','128m','--pids-limit','32','-v',f'{stack.secrets / "keycloak-bundle.json"}:/run/source/keycloak-bundle.json:ro',
        '-v',f'{volume}:/run/keycloak',stack.manifest['images']['consumer'],'python','-m','lab_runner.keycloak')
    command(stack.engine,'start','-a',job)
    identifier = stack._create('container',name,'run','-d','--name',name,'--label',
        f'io.prosaic.lab.owner={stack.owner}','--network',stack.manifest['network_id'],'--network-alias','issuer',
        '--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--memory','1g','--cpus','2','--pids-limit','256','-p','127.0.0.1::8443',
        '-e','KC_BOOTSTRAP_ADMIN_USERNAME=lab-admin','-e',f'KC_BOOTSTRAP_ADMIN_PASSWORD={admin_password}',
        '-v',f'{volume}:/run/keycloak:ro','-v',f'{volume}:/opt/keycloak/data/import:ro',image,
        'start-dev','--http-enabled=false','--hostname=https://issuer:8443','--import-realm',
        '--https-certificate-file=/run/keycloak/server.pem','--https-certificate-key-file=/run/keycloak/server.key')
    port = json.loads(command(stack.engine,'inspect',identifier))[0]['NetworkSettings']['Ports']['8443/tcp'][0]['HostPort']
    host_url = f'https://127.0.0.1:{port}/realms/prosaic-lab'
    context = ssl.create_default_context(cafile=str(ca))
    with httpx.Client(verify=context,trust_env=False,timeout=3) as client:
        deadline = time.monotonic()+90
        while True:
            try:
                if client.get(host_url+'/.well-known/openid-configuration').status_code == 200: break
            except httpx.HTTPError: pass
            if time.monotonic() >= deadline: raise EngineError('owned issuer readiness timeout')
            time.sleep(.2)
        tokens,refresh = {},{}
        for subject,principal in bindings.items():
            response = client.post(host_url+'/protocol/openid-connect/token',data={
                'grant_type':'password','client_id':'integration-lab','client_secret':client_secret,
                'username':principal['actor_id'],'password':passwords[principal['actor_id']]})
            if response.status_code != 200: raise EngineError('owned issuer token fixture failed')
            data = response.json()
            tokens[data['access_token']] = principal
            refresh[principal['actor_id']] = data['refresh_token']
    issuer = 'https://issuer:8443/realms/prosaic-lab'
    container_config.update(deployment_mode='production',principals={},authentication={
        'provider':'oidc','issuer':issuer,'audience':'integration-lab','subjects':bindings,
        'jwks_uri':issuer+'/protocol/openid-connect/certs','ca_file':'/run/secrets/issuer-ca.pem',
        'introspection':{'url':issuer+'/protocol/openid-connect/token/introspect',
            'client_id':'integration-lab','client_secret':client_secret}})
    host_config.update(principals=tokens,oidc_fixture={'url':host_url,'issuer':issuer,'ca_file':str(ca),
        'client_id':'integration-lab','client_secret':client_secret,'refresh_tokens':refresh,
        'passwords':passwords,'admin_password':admin_password})
    stack.manifest['issuer_id'] = identifier
    stack.manifest['endpoints']['issuer'] = host_url
    stack.manifest['images']['keycloak'] = image
    stack._save()

if __name__ == '__main__': deliver()
