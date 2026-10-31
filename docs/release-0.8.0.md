# Integration Lab 0.8.0

Lab 0.8.0 adds the **execution Observatory**, with a cinematic 3D Live view and
an Inspect timeline for actual Runtime, provider, tool and Harness observations.
It preserves Explorer and the existing application/SDK boundaries.

## Use the Observatory

Follow the [setup](quickstart.md#setup-once), then run from a checkout or complete
source archive with Docker available:

```sh
.venv/bin/python scripts/build_consumer.py --tag prosaic-integration-lab:dev
.venv/bin/python -m lab_runner.observatory --max-calls 12 --fixture-latency 1.5
```

The default owns a disposable PostgreSQL stack and a bounded scripted HTTP
provider. `Find players` shows provider/tool activity followed by workflow
waiting. `Hello` produces a shorter completed turn. Both views expose bounded
text-only owner history and recorder-backed counts; the launcher labels the
model mode. Ctrl+C verifies cleanup of its owned resources.

The [Observatory guide](../prototypes/observatory/README.md) covers the separate
sample-only server, explicit local-model opt-in, one-use connection link,
inspection, reduced motion and Blender source regeneration.

## Behavior and boundaries

- The optional observation API retains trusted ownership and frozen accounting
  attribution. Trace events omit prompts, replies, tool arguments and credentials.
- Unresolved workflow-start intent remains `needsResolution`; reading a trace
  does not grant a retry or start another workflow. Missing static files return 404.
- Source archives include the complete UI, local browser dependencies, font
  licenses, Blender source and exported PBR asset. Release checks verify the
  extracted shell, dependency digests, model digest and JavaScript regressions.
- Observations are best-effort and bounded in memory. The animation represents
  request activity; token counts arrive with completed usage reports, not as
  individually timed token events. Unsupported counts are explicitly unqualified.
- The host fixture/authoring tree requires a checkout or complete source archive.
  Installing the wheel alone does not provide those host fixtures. Explorer
  remains independently runnable with its bundled wheel assets.

The SDK train is unchanged: Core 0.4.1, Runtime 0.9.8, Runtime recorder 0.3.0,
Harness 0.9.4 and store 0.4.0. Existing authorization, execution, accounting,
recovery, benchmarks and experimental boundaries remain unchanged.

## Release qualification

The versioned artifacts are qualified by the full Linux AMD64/ARM64 ×
PostgreSQL 16/18 matrix. Publication uses the original successful CI wheel and
source archive with matching checksums and a verification record binding them
to their exact source and SDK manifest. Earlier release assets are preserved.
Release qualification uses synthetic providers and makes no new model-quality
or live-provider claim.
