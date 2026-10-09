import json
from pathlib import Path
import ssl
import httpx
import jwt
from lab_runner.manifest import validate_resource
from lab_runner.stack import command
from test_approval import headers,start
from test_accounting import count
from test_recovery import wait_for
from test_recovery import mutate_replica
from test_scope import deliver_owned_config
from test_delivery_recovery import published_path
from lab_runner.stack import EngineError
from lab_runner.keycloak import bundle
import pytest

def test_real_keycloak_tls_token_claims_do_not_control_billing(lab):
    fixture = lab['oidc_fixture']
    token = headers(lab)['Authorization'][7:]
    claims = jwt.decode(token,options={'verify_signature':False})
    assert claims['iss'] == fixture['issuer']
    assert claims['billing_account_id'] == 'SPOOF'
    run = start(lab,workflow='synthetic').json()
    usage = httpx.get(lab['b']+'/runs/'+run['run_id']+'/usage',headers=headers(lab),timeout=5)
    assert usage.status_code == 200
    assert usage.json()['complete_calls'] == 1
    import psycopg
    with psycopg.connect(lab['app_dsn']) as connection:
        row = connection.execute('SELECT tenant_id,actor_id,billing_account_id FROM lab_app.runs WHERE run_id=%s',
            (run['run_id'],)).fetchone()
    assert row == ('tenant-a','alice','account-a')


def test_real_keycloak_signing_key_rotation_preserves_owner_and_frozen_accounting(lab):
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['issuer_id']
    validate_resource(json.loads(command(manifest['engine'],'inspect',identifier))[0],identifier,manifest['owner'])
    fixture = lab['oidc_fixture']
    run = start(lab,workflow='synthetic').json()
    path = '/runs/'+run['run_id']
    before = count(lab)
    original_kid = jwt.get_unverified_header(headers(lab)['Authorization'][7:])['kid']
    context = ssl.create_default_context(cafile=fixture['ca_file'])
    with httpx.Client(verify=context,trust_env=False,timeout=5) as client:
        base = fixture['url'].removesuffix('/realms/prosaic-lab')
        authenticated = client.post(base+'/realms/master/protocol/openid-connect/token',data={
            'grant_type':'password','client_id':'admin-cli','username':'lab-admin','password':fixture['admin_password']})
        assert authenticated.status_code == 200
        admin = {'Authorization':'Bearer '+authenticated.json()['access_token']}
        realm = client.get(base+'/admin/realms/prosaic-lab',headers=admin)
        assert realm.status_code == 200
        rotated = client.post(base+'/admin/realms/prosaic-lab/components',headers=admin,json={
            'name':'owned-rotation','providerId':'rsa-generated','providerType':'org.keycloak.keys.KeyProvider',
            'parentId':realm.json()['id'],'config':{'priority':['200'],'enabled':['true'],
                'active':['true'],'algorithm':['RS256'],'keySize':['2048']}})
        assert rotated.status_code == 201
        issued = client.post(fixture['url']+'/protocol/openid-connect/token',data={
            'grant_type':'password','client_id':fixture['client_id'],'client_secret':fixture['client_secret'],
            'username':'alice','password':fixture['passwords']['alice']})
        assert issued.status_code == 200
        replacement = issued.json()['access_token']
        assert jwt.get_unverified_header(replacement)['kid'] != original_kid
    for replica in ('a','b'):
        actor = {'Authorization':'Bearer '+replacement}
        wait_for(lambda:httpx.get(lab[replica]+path,headers=actor,timeout=5).status_code == 200)
        usage = httpx.get(lab[replica]+path+'/usage',headers=actor,timeout=5)
        assert usage.status_code == 200 and usage.json()['complete_calls'] == 1
        assert httpx.get(lab[replica]+path,headers=headers(lab),timeout=5).status_code == 200
    assert count(lab) == before


def test_killed_ca_delivery_never_publishes_a_mixed_config_generation(lab):
    run = start(lab).json()
    secrets = Path(lab['fixture_manifest']).parent/'secrets'
    source,certificate,controls = secrets/'service.json',secrets/'issuer-ca.pem',secrets/'delivery-controls.json'
    original,original_ca = source.read_text(),certificate.read_text()
    previous = published_path(lab)
    config = json.loads(original)
    config['namespace'] += '-unpublished'
    other_files,_,_,_ = bundle([])
    try:
        source.write_text(json.dumps(config))
        certificate.write_text(other_files['ca.pem'])
        controls.write_text(json.dumps({'failpoint':'after_ca'}))
        with pytest.raises(EngineError): deliver_owned_config(lab)
        assert published_path(lab) == previous
        mutate_replica(lab,'kill','b')
        mutate_replica(lab,'start','b')
        wait_for(lambda:httpx.get(lab['b']+'/readyz',timeout=2).status_code == 200)
        # Real TLS introspection still trusts the old matching CA after restart.
        assert httpx.get(lab['b']+'/runs/'+run['run_id'],headers=headers(lab),timeout=5).status_code == 200
    finally:
        source.write_text(original)
        certificate.write_text(original_ca)
        controls.write_text('{}')
        deliver_owned_config(lab)
        mutate_replica(lab,'kill','b')
        mutate_replica(lab,'start','b')
        wait_for(lambda:httpx.get(lab['b']+'/readyz',timeout=2).status_code == 200)

def test_keycloak_revocation_is_enforced_on_both_replicas_before_body(lab):
    before = count(lab)
    fixture = lab['oidc_fixture']
    context = ssl.create_default_context(cafile=fixture['ca_file'])
    with httpx.Client(verify=context,trust_env=False,timeout=5) as client:
        response = client.post(fixture['url']+'/protocol/openid-connect/logout',data={
            'client_id':fixture['client_id'],'client_secret':fixture['client_secret'],
            'refresh_token':fixture['refresh_tokens']['carol']})
        assert response.status_code == 204
    for replica in ('a','b'):
        denied = httpx.post(lab[replica]+'/runs',content='malformed private body',
            headers={**headers(lab,'carol'),'Idempotency-Key':'revoked'},timeout=5)
        assert denied.status_code == 401
        assert denied.json() == {'detail':'unauthenticated'}
    assert count(lab) == before

def test_identity_outage_fails_closed_without_dispatch(lab):
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['issuer_id']
    state = json.loads(command(manifest['engine'],'inspect',identifier))[0]
    validate_resource(state,identifier,manifest['owner'])
    before = count(lab)
    command(manifest['engine'],'stop','--time','1',identifier)
    for replica in ('a','b'):
        denied = httpx.post(lab[replica]+'/runs',json={'task':'neutral fixture'},
            headers={**headers(lab),'Idempotency-Key':'issuer-outage'},timeout=5)
        assert denied.status_code == 503
        assert denied.json() == {'detail':'identity_unavailable'}
        assert httpx.get(lab[replica]+'/healthz',timeout=2).status_code == 200
    assert count(lab) == before
