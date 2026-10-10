"""Real owned SQL journal concurrency/fencing acceptance."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import uuid
import psycopg
import pytest
from prosaic_integration_lab.tool_journal import PgToolJournal


@pytest.fixture
def journal(lab):
    return PgToolJournal(lab['app_dsn'],identity='owned-fixture-'+lab['namespace'])


def test_uncertain_claim_never_reclaims_and_stale_token_cannot_commit(journal):
    from prosaic_runtime import ToolClaim
    key = uuid.uuid4().hex
    first = journal.claim('tenant-a',key,'a'*64)
    assert isinstance(first,ToolClaim) and first.state == 'new'
    repeated = journal.claim('tenant-a',key,'a'*64)
    assert repeated.state == 'uncertain' and repeated.claim_token is None
    with pytest.raises(ValueError):
        journal.commit('tenant-a',key,'stale-token',{'status':'ok','result':{'applied':True}})
    journal.commit('tenant-a',key,first.claim_token,{'status':'ok','result':{'applied':True}})
    replay = journal.claim('tenant-a',key,'a'*64)
    assert replay.state == 'replay' and replay.claim_token is None
    assert replay.outcome == {'status':'ok','result':{'applied':True}}
    with pytest.raises(ValueError):
        journal.commit('tenant-a',key,first.claim_token,{'status':'ok','result':{'applied':False}})
    assert journal.claim('tenant-a',key,'a'*64).outcome == replay.outcome


def test_same_scope_concurrent_claim_has_only_one_dispatch_winner(journal):
    key = uuid.uuid4().hex
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _:journal.claim('tenant-a',key,'a'*64),range(2)))
    assert sorted(claim.state for claim in claims) == ['new','uncertain']
    assert sum(claim.claim_token is not None for claim in claims) == 1
    assert journal.claim('tenant-b',key,'b'*64).state == 'new'
    with pytest.raises(ValueError,match='tool_identity_conflict'):
        journal.claim('tenant-a',key,'b'*64)
    assert journal.claim('tenant-a',key,'a'*64).state == 'uncertain'


def test_lost_commit_acknowledgement_discovers_committed_replay(journal,monkeypatch):
    key = uuid.uuid4().hex
    first = journal.claim('tenant-a',key,'a'*64)
    original_connection = journal.connection
    @contextmanager
    def lost_ack():
        with original_connection() as connection:
            yield connection
        raise psycopg.OperationalError('synthetic lost commit acknowledgement')
    with monkeypatch.context() as patch:
        patch.setattr(journal,'connection',lost_ack)
        with pytest.raises(psycopg.OperationalError):
            journal.commit('tenant-a',key,first.claim_token,{'status':'ok','result':{'applied':True}})
    replay = journal.claim('tenant-a',key,'a'*64)
    assert replay.state == 'replay' and replay.outcome['result']['applied'] is True


def test_lost_claim_acknowledgement_never_grants_redispatch(journal,monkeypatch):
    key = uuid.uuid4().hex
    original_connection = journal.connection
    @contextmanager
    def lost_ack():
        with original_connection() as connection:
            yield connection
        raise psycopg.OperationalError('synthetic lost claim acknowledgement')
    with monkeypatch.context() as patch:
        patch.setattr(journal,'connection',lost_ack)
        with pytest.raises(psycopg.OperationalError):
            journal.claim('tenant-a',key,'a'*64)
    claim = journal.claim('tenant-a',key,'a'*64)
    assert claim.state == 'uncertain' and claim.claim_token is None


def test_restricted_role_cannot_replace_signature_or_fencing_token(lab,journal):
    key = uuid.uuid4().hex
    journal.claim('tenant-a',key,'a'*64)
    for column in ('signature','claim_token','operation_namespace'):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(lab['app_dsn']) as connection:
                connection.execute(f'UPDATE lab_app.tool_operations SET {column}=%s WHERE operation_key=%s',
                    ('changed',key))
    assert journal.claim('tenant-a',key,'a'*64).state == 'uncertain'


@pytest.mark.parametrize('result', ['x'*262144, float('nan'), {'bad':object()}],ids=['oversize','nonfinite','unserializable'])
def test_post_effect_invalid_result_preserves_uncertain_row(journal,result):
    key = uuid.uuid4().hex
    claim = journal.claim('tenant-a',key,'a'*64)
    with pytest.raises(ValueError,match='invalid_outcome'):
        journal.commit('tenant-a',key,claim.claim_token,{'status':'ok','result':result})
    assert journal.claim('tenant-a',key,'a'*64).state == 'uncertain'
