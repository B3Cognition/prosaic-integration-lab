# Guided onboarding verification — 2026-10-25

This is a local post-0.6.2 onboarding follow-up, not a release or new model
benchmark. It changes the README/guides, an example configuration and a standalone
public-SDK admission example. SDK pins, engines, benchmark Markdown/inputs,
historical evidence and immutable release assets are unchanged.

## Executed paths

macOS ARM64, Python 3.12.15, Docker Desktop Linux/aarch64, Docker 29.9.2,
released Runtime 0.9.8 with the unchanged active manifest:
`36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.

| Path | Observed result |
| --- | --- |
| First-workflow subprocess regression | Watched fail before example existed, then pass with actual public Core parsing, workflow admission and input preparation |
| Exact newcomer setup in an empty environment | Locked dependencies, checksummed SDK preparation/install, Lab source install, audit, pip check, SDK version command and neutral-cwd example passed; temporary environment removed |
| Fresh candidate wheel / rebuilt-source consumers | Each passed 51 standalone fixtures and the new first-workflow example; cleanup verified; no source SDK imports |
| `unified-cli-test` | 13/13 checks, zero live invocations, verified cleanup |
| `unified-fallback-test` | 18/18 checks, including learned cooldowns and no partial replay; zero live invocations, verified cleanup |
| Native service demo, PostgreSQL 16 | Completed discovery/admission/start/review/resume; two complete synthetic model calls; owner result passed and cleanup verified |
| Conversation service demo, PostgreSQL 16 | Completed correction/lookup/selection/confirmation; nine synthetic model calls and one fixture operation; owner result passed and cleanup verified |
| Copied private example configs | Loaded through public `UnifiedRuntimeConfig.load`, no inference |
| Links and shell syntax | 161 local links/anchors verified; quickstart shell blocks passed `bash -n` |
| Candidate wheel and source build | Both built successfully; new example included in source archive |
| Full source suite | 1,923 passed in 500.29s; one existing Starlette dependency deprecation warning |

The demo consumer was built as a distinct owned image and invoked by immutable
ID `sha256:c33f3a647d5d07bbd0b601442d43a293d381ada1655325d5da8c24d30c346798`.
Owned service resources were cleaned; no global Docker pruning was performed.
The displayed native/conversation reports identify completed journeys; cleanup
is verified in each owner's `.lab/<owner>/result.json`, as documented.

## Review and scope

Independent read-only review found the initial setup omitted installing the Lab
consumer before its version command. The guide now includes
`pip install --no-deps .`; the corrected exact sequence passed in an empty
environment. Re-review found no remaining actionable issues. Manual command
verification also corrected demo receipt locations and the browser bootstrap
connection-file instructions.

The browser launcher/help and existing regression coverage were inspected;
this change does not claim a new manual interactive browser qualification.
Real provider execution and live benchmark commands were not dispatched for
onboarding verification. Their flags/configuration follow existing installed
contracts; model/login availability remains operator-specific. Browser unified
pool execution is explicitly outside this implementation. Linux/database CI of
this new branch remains separate from the recorded 0.6.2 release qualification.

Private local logs/receipts retain the full source-suite, setup, installed
consumers, links, builds and owned service-demo results. No raw provider output,
secrets or private run state is committed.
