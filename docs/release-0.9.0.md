# Integration Lab 0.9.0

Lab 0.9.0 makes actual model output generation visible in the Observatory's Live
and Inspect views and enables streaming by default in Lab conversations, native
workflow bindings, chat and local example profiles.

## See generation

Follow the [setup](quickstart.md#setup-once), then run from a checkout or complete
source archive with Docker available:

```sh
.venv/bin/python scripts/build_consumer.py --tag prosaic-integration-lab:dev
.venv/bin/python -m lab_runner.observatory --max-calls 12 --fixture-latency 1
```

Open the private one-use launcher link and click **Start lab test** with the
default `Show generation` message. The owned synthetic HTTP provider produces
52 paced output chunks. Both views show provisional text, actual arrival marks,
a cumulative character curve, first-output wait and gaps. Live returns particles
when chunks arrive; Inspect follows live output and supports call selection,
pause, scrubbing and replay. Replay makes no new provider request. Reduced-motion
mode suppresses moving provider packets.

The synthetic default uses no model credential. Real local inference remains an
explicit, bounded opt-in. [The Observatory guide](../prototypes/observatory/README.md)
covers connection links, live-local configuration, source assets and cleanup.
The Observatory host fixture requires a checkout or complete source archive;
the wheel alone does not supply that tree. Explorer remains independently
available from its installed wheel.

## Defaults, connections and compatibility

- Trusted bundles can explicitly select `streaming: false`. Existing omitted-flag
  buffered conversation and native workflow identities remain available for
  retained sessions/proposals; new runs select streaming.
- Manual credentials are validated before the Observatory shows Connected. A
  rejected credential reveals reconnect controls and cannot silently dispatch.
- A process-bound HttpOnly, SameSite=Strict launcher session restores the same
  authorized browser after reload, for at most eight hours. The one-use launch
  handshake and session restoration require the exact origin. API bearer tokens
  are not written to localStorage/sessionStorage, and cookies do not authenticate
  ordinary API requests. Another browser needs a fresh link or valid API token.
- Per-turn provider reservations remain independent of cumulative session
  budgets. The launcher explicitly supports a one-request allowance without
  weakening the ordinary reservation rule. No request is automatically retried.
- Streaming selects provider transport. Existing message HTTP responses and
  committed chat history retain their JSON contracts and validation semantics.

## Evidence and limits

Chunk marks represent client-observed text arrivals, not exact token boundaries.
Provider token totals remain separate, run-wide recorder evidence; unknown,
partial and unsupported reports retain their qualification. The UI makes no
claim about server prefill, queueing, reasoning or per-token timing.

The optional owner-authorized generation projection retains at most 32 calls,
512 timing samples and 4,096 preview characters per call. It excludes prompts,
tool arguments, interpreter output and credentials. Interrupted text stays
provisional; truncated timing is visibly unknown. Metadata events stay separate.
Observations are best effort and in memory, rather than durable billing records.

The SDK train is unchanged: Core 0.4.1, Runtime 0.9.8, Runtime recorder 0.3.0,
Harness 0.9.4 and store 0.4.0. Earlier release artifacts and tags are preserved.

## Release qualification

Publication requires the exact versioned source to pass all four Linux
AMD64/ARM64 × PostgreSQL 16/18 CI cells, including required owned-stack gates,
public SDK adoption, installed wheel/rebuilt-source consumers and documented
demos. Publication uses the original successful CI wheel and source archive,
with checksums and a verification record binding them to their exact source,
SDK manifest and safe receipts. Qualification uses synthetic providers and makes
no new live-provider or model-quality claim.

Conversation acceptance allows up to 15 minutes for its provider-timeout,
worker-loss and lease-recovery cases, with a separate bounded stack-lifecycle
allowance. A deadline still fails qualification and safe receipts identify it
as `execution_timeout`; required counts, assertions and cleanup remain enforced.
