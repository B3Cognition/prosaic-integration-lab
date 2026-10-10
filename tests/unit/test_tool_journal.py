import pytest


@pytest.mark.parametrize('outcome', [None, {}, {'status':'error','result':{}},
    {'status':'ok','result':float('nan')}, {'status':'ok','result':{'private':'x'*262144}},
    {'status':'ok','result':'\ud800'}, {'status':'ok','result':object()},
    {'status':'ok','result':[[[[[[object()]]]]]]}])
def test_post_effect_invalid_outcome_is_rejected_before_storage(outcome):
    from prosaic_integration_lab.tool_journal import PgToolJournal
    with pytest.raises(ValueError, match='^invalid_outcome$'):
        PgToolJournal('never-connect', identity='owned-ledger').commit('tenant-a', 'key', 'token', outcome)


@pytest.mark.parametrize('namespace,key,signature', [('','key','a'*64), ('tenant','x'*129,'a'*64),
    ('tenant','key','not-a-signature'), ('tenant','key','b'*65)])
def test_invalid_operation_address_cannot_open_database(namespace,key,signature):
    from prosaic_integration_lab.tool_journal import PgToolJournal
    with pytest.raises(ValueError):
        PgToolJournal('never-connect', identity='owned-ledger').claim(namespace,key,signature)


@pytest.fixture
def journal(tmp_path,monkeypatch):
    from prosaic_integration_lab.tool_journal import PgToolJournal
    from persistence_sql import database
    result = PgToolJournal('unused',identity='unit-ledger')
    monkeypatch.setattr(result,'connection',database(tmp_path/'journal.sqlite'))
    return result


def test_sql_claim_is_uncertain_until_fenced_commit_and_never_reclaims(journal):
    from prosaic_runtime import ToolClaim
    claim = journal.claim('owner','key','a'*64)
    assert type(claim) is ToolClaim and claim.state == 'new' and claim.claim_token
    uncertain = journal.claim('owner','key','a'*64)
    assert uncertain.state == 'uncertain' and uncertain.claim_token is None
    with pytest.raises(ValueError,match='tool_claim_conflict'):
        journal.commit('owner','key','stale-token',{'status':'ok','result':{'applied':False}})
    assert journal.claim('owner','key','a'*64).state == 'uncertain'
    journal.commit('owner','key',claim.claim_token,{'status':'ok','result':{'applied':True}})
    replay = journal.claim('owner','key','a'*64)
    assert replay.state == 'replay' and replay.claim_token is None
    assert replay.outcome == {'status':'ok','result':{'applied':True}}
    with pytest.raises(ValueError,match='tool_claim_conflict'):
        journal.commit('owner','key',claim.claim_token,{'status':'ok','result':{'applied':False}})
    assert journal.claim('owner','key','a'*64).outcome == replay.outcome


def test_sql_signature_conflict_and_namespaces_are_independent(journal):
    journal.claim('first','key','a'*64)
    with pytest.raises(ValueError,match='tool_identity_conflict'):
        journal.claim('first','key','b'*64)
    assert journal.claim('second','key','b'*64).state == 'new'
    assert journal.claim('first','key','a'*64).state == 'uncertain'


def test_sql_post_effect_invalid_outcome_keeps_uncertain(journal):
    claim = journal.claim('owner','key','a'*64)
    with pytest.raises(ValueError,match='invalid_outcome'):
        journal.commit('owner','key',claim.claim_token,{'status':'ok','result':'x'*262144})
    assert journal.claim('owner','key','a'*64).state == 'uncertain'


def test_sql_lost_acknowledgement_is_evidence_without_permission_to_retry(journal,monkeypatch):
    from contextlib import contextmanager
    original = journal.connection
    @contextmanager
    def lost_ack():
        with original() as connection:
            yield connection
        raise OSError('synthetic lost acknowledgement')
    with monkeypatch.context() as patch:
        patch.setattr(journal,'connection',lost_ack)
        with pytest.raises(OSError):
            journal.claim('owner','claim-lost','a'*64)
    assert journal.claim('owner','claim-lost','a'*64).state == 'uncertain'
    claim = journal.claim('owner','commit-lost','a'*64)
    with monkeypatch.context() as patch:
        patch.setattr(journal,'connection',lost_ack)
        with pytest.raises(OSError):
            journal.commit('owner','commit-lost',claim.claim_token,{'status':'ok','result':True})
    assert journal.claim('owner','commit-lost','a'*64).outcome == {'status':'ok','result':True}
