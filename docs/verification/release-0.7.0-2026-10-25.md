# Lab 0.7.0 release and clean-install verification

[Lab 0.7.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.7.0)
publishes the original CI wheel and source archive from
[run 40234494951](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/40234494951).
Tag `v0.7.0` selects qualified source
`9a7542c8b736939bf4d22ee2cd3164760eb07449`.
[PR #35](https://github.com/B3Cognition/prosaic-integration-lab/pull/35) merged as
`4fa6e4634d1e6f836c35fe666bb0a155979b5415` with an identical file tree.

## Qualification and published bytes

All four Linux AMD64/ARM64 × PostgreSQL 16/18 cells passed 1,980 source tests
and 334 required stack checks each: 36 lanes / 1,336 stack checks total,
zero skipped or failed stack checks, and verified cleanup. Public-index SDK
adoption, actual sandbox confinement, native/unified acceptance, installed
distribution consumers and documented demos passed. AMD64/PostgreSQL 16 also
passed 10 browser checks; ARM64/PostgreSQL 16 additionally qualified the rebuilt
source service stack. All 191 wheel and 722 archive source payload files matched
the exact qualified commit before publication.

| Public asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `prosaic_integration_lab-0.7.0-py3-none-any.whl` | 688779 | `d22997567d1cee5f56b4b53172b5e4ffff29ee43aefd5b64b216e9198ca4831b` |
| `prosaic_integration_lab-0.7.0.tar.gz` | 1562051 | `affc09fa6c905885f20e1a1abfc365d340d92819ab188028b50ae39bae96be8b` |
| `SHA256SUMS-0.7.0.txt` | 306 | `95862bff5fc8df1920717bceab9eee47b53b7ac20f3006371e0748e06f347ed9` |
| `VERIFICATION-0.7.0.json` | 7009 | `29c6070b1ddeb05b396c60548d142dfea8416b1b5c6fe1af5fadf5233d0e006d` |

Uploaded asset hashes/sizes and all four anonymous public downloads matched the
audited files. The wheel and source archive retain their original CI bytes.
`VERIFICATION-0.7.0.json` binds their hashes to the source, SDK manifest and
retained qualification receipts. The release notes also record the completed
post-publication verification. Earlier releases retain their original artifacts.

## Clean installed consumers

Fresh public-wheel and rebuilt-public-source consumers ran on macOS ARM64,
Python 3.12.15. Each installed locked dependencies and the public SDK train:
Core 0.4.1, **Runtime 0.9.8**, Runtime recorder 0.3.0, Harness 0.9.4 and store 0.4.0.
Manifest SHA-256:
`36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.

The downloaded source archive was extracted into owned temporary storage and
rebuilt with Python's build frontend. Both consumers used non-editable installs,
isolated imports and private working directories. Installed Lab/SDK payload
audits, absence of repository `scripts`, public API construction, dependency
compatibility and cleanup passed. Explorer served its installed assets; Node was
used only by external browser-test tooling, not by the installed launcher.

| Installed verification | Public wheel | Rebuilt public source |
| --- | --- | --- |
| `test` native fixtures | 9/9 | 9/9 |
| `unified-test` API fixtures | 11/11 | 11/11 |
| `unified-cli-test` CLI fixtures | 13/13 | 13/13 |
| `unified-fallback-test` rejection/no-replay fixtures | 18/18 | 18/18 |
| CLI default 180s, explicit 240s, fractional 299.999999s | 3/3 | 3/3 |
| Installed Explorer browser checks | 10/10 | 10/10 |
| Total fixture/browser checks | **64/64** | **64/64** |

All 128 fixture/browser checks passed. Deadline fixtures exercise installed CLI
parsing, configuration, readiness, accounting and saved receipts with inference
replaced by explicit refusals. They establish deadline propagation, not a model's
ability to complete within 240 seconds.

The verification driver invoked these public installed entrypoints with `-I -B`:
`python -m prosaic_integration_lab --version`, `python -m lab_runner --help`,
and `python -m lab_runner.native_eval` with each of the four fixture commands
above plus `--manifest` and `--wheel-dir`. It ran the source archive's
`tests/functional/test_benchmark_local_timeout.py` with an empty pytest config,
`--noconftest` and `--import-mode=importlib` against each installed consumer.

For the browser suite it ran `npm run test:browser` from the archive's
`frontend/explorer`, with `EXPLORER_INSTALLED=1` and `EXPLORER_PYTHON` selecting
the clean consumer. The launcher then ran `python -I -B -m lab_runner.explore`
from a private temporary working directory, preventing checkout imports.

## Visual documentation and playback

Both installed consumers passed checks for all five chapters and eight
deterministic playback scenarios; user/developer inspection, keyboard selection,
locally loaded Instrument Sans/Geist Mono, and System/Light/Dark appearance
worked. Chapter frame/navigation checks covered 1920×900, 1440×900, 1280×720,
768×1024 and 390×844. Previous/Next remained in the viewport while longer
chapter content scrolled internally. Installed desktop/light (1440×1000) and
mobile/dark (390×844) screenshots were also inspected.

Documentation, playback and appearance changes dispatched no model work.
The browser suite uses a documentation-only launcher and intercepted synthetic
responses for live UI cases, including explicit confirmation, escaped output,
cancellation, lost-response recovery and retained receipt selection. Separate
execution checks below validate the actual host/Runtime boundary.

## Bounded execution through the installed Runtime CLI

Each consumer additionally launched installed Explorer with `--live`, a private
unified configuration, the real installed SDK payload audit, an owned loopback
API fixture and a 20-unit durable allowance. No SDK imports or execution paths
were patched. The sequence exercised the browser, Explorer host, public Runtime
CLI and actual HTTP/tool execution:

1. The Run button required reviewed authority and explicit confirmation. The
   `invoice-sql` task used the 240s local/API deadline, completed and passed its
   grader with two provider requests, one file write and 14 reported tokens.
2. Repeating its request identity returned the retained receipt without another
   provider request. The allowance retained 2 units, leaving 18.
3. A second task was cancelled with a provider request pending. Its unknown
   reservation remained charged: 12/20 units retained in total, 8 remaining,
   one unknown reservation and recovery required.
4. New submissions were refused before and after restarting the launcher with
   the same evidence root. Each sequence made three synthetic provider requests;
   cancellation/restart did not trigger another request or replay work.

Fixed policy remained native 60s / pool 300s, at most 3 attempts / 2 native
attempts, 8 API requests, 7 tool calls, 8 tool rounds and 65,536 reported tokens,
with native `workspace-write` permission and the task's explicit API tool/file
grants. Mixed allowance units are native attempts plus API provider requests;
they are not tokens, currency or a native subscription spending limit.

All owned processes, sockets and temporary consumers were cleaned up. Private
verification receipts retain the download, payload, command and control proofs;
connection credentials, raw configuration and private run state are not published.

This is synthetic release qualification, with **zero real model calls**. It does
not certify Claude/Codex authentication or live quota behavior, establish a new
benchmark, or change existing Markdown tasks, inputs, graders or SDK pins. The
[historical live study](unified-cli-lab061-local240-2026-10-25.md) remains separate.
Memory and correction remain experimental.
