"""Registry-to-review composition; external worker replies are synthetic here."""

import uuid

from prosaic_harness import FileRunStore
from prosaic_runtime import EndpointConfig,RuntimeConfig

from prosaic_integration_lab.memory_provider import MemoryProviders
from prosaic_integration_lab.sue_review.session import SueReviewSession
from prosaic_integration_lab.sue_review.sources import freeze_castle_snapshot
from tests.unit.test_memory_selected_capture import OWNER,TEXT,SELECTIONS,boundary,settings
from tests.sue_review.test_execution import CLAIM,fixture,script


def test_selected_registry_capture_is_frozen_before_provider_disappears(tmp_path,boundary):
    providers = MemoryProviders(settings(tmp_path))
    capture = providers.capture_selected(OWNER,SELECTIONS)
    frozen = freeze_castle_snapshot(capture,expected_scope=capture['scope'])
    values,_ = script(max_turns=1)
    values[0]['evidence'][0]['quote'] = TEXT.splitlines()[0]
    values[0]['premises'][0]['statement'] = TEXT.splitlines()[0]
    with fixture(values) as (url,calls),FileRunStore(tmp_path/'runs',namespace='owned-memory') as store:
        flow = SueReviewSession({'enabled':True},store,
            RuntimeConfig({'fixture':EndpointConfig(url,'sue-fixture',features={'streaming':False})},{},'fixture'),
            OWNER,'owned-memory')
        run_id = uuid.uuid4().hex
        waiting = flow.start(run_id,seed=CLAIM,sources=frozen,max_turns=1)
        assert waiting['status'] == 'waiting' and calls == []
        providers.close()
        capture['bundle']['texts'][0] = 'Changed after admission'
        boundary.instances[0].bundle['texts'][0] = 'Provider disappeared'
        done = flow.resume(run_id,expected_revision=waiting['revision'],choice='continue')
        assert done['status'] == 'completed' and done['terminal'] == 'BOUNDED_STOP'
        assert len(calls) == 1 and len(boundary.instances[0].calls) == 1
        saved = store.load_run(run_id).state['inputs']['evidence']
        assert saved == frozen and saved['sources'][0]['text'] == TEXT
        assert saved['sources'][0]['provenance']['record_id'] == 'one'
        assert done['proposal']['sourcesSha256'] == frozen['sourcesSha256']
        assert flow.report(run_id)['citations'][0]['quote'] == TEXT.splitlines()[0]
