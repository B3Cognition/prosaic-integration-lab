# Prosaic Castle: enable only what you need

Use this guide for the **independent, unpublished Prosaic Castle candidate**.
It replaces package setup in steps 1–2 of the historical
[Castle quickstart](castle-quickstart.md). That quickstart retains its r7
`cognitive-castle` bundle and platform evidence; those are a different profile.
Do not mix their same-version wheels with this bundle.

**Memory and SUE review are independently disabled by default.** Installing any
package below enables neither feature. There is no automatic chat capture,
background indexing, model call or permission to read a new source.

| Your task | Enable | What you get |
| --- | --- | --- |
| Find why a project chose a database or attempted a particular fix | Memory, after importing the notes or exported development sessions you authorize | Scoped full-text search and an exact frozen evidence snapshot |
| Inspect a particular specification or proposed interpretation | SUE review with explicitly selected sources | An advisory structured review with quotations and open questions |
| Ask a model to rank snippets, refine entity labels or classify corpus origin | A separate [Castle model job](castle-model-jobs.md) | Bounded advice after host selection and approval; no automatic corpus changes |

Memory supplies evidence. SUE does not independently establish truth or
correctness, and a judge result is not authorization. These fixtures make no
claim that a real model becomes better at retrieval, review or coding.

## 1. Obtain the matching candidate bundle

Run from the root of this Lab checkout using Python 3.12. Obtain the three
candidate wheels and the matching Lab wheel from the maintainer. They are not
published package-index releases. The source profile is
[`prosaic-castle-source-2026-10-24.json`](../dependencies/prosaic-castle-source-2026-10-24.json):

| Piece | Distribution / file | Install into |
| --- | --- | --- |
| Read-only worker | `prosaic-castle==3.4.2` / `prosaic_castle-3.4.2-py3-none-any.whl` | Worker environment |
| Host adapter | `b3-prosaic-memory-castle==0.1.0` / `b3_prosaic_memory_castle-0.1.0-py3-none-any.whl` | Host environment, for memory |
| Separate pure SUE engine | `cognitive-castle-sue==0.1.0` / `cognitive_castle_sue-0.1.0-py3-none-any.whl` | Host environment, for review |

The independent fork source is
`e810a016abab7b96b4c905b04314562065d5fed3`, based on Cognitive Castle
`53637196cc215e9bd5b85b9253b3430b2781b884`. It retains the legacy engine version
3.4.2; its distribution name identifies the fork. SUE still imports as
`castle_sue`, and the host adapter still imports as `prosaic_memory_castle`.
Runtime payloads are unchanged from fork commit `971dd4fe`; the final source
archive also makes legacy CI dependencies explicit and archives the inherited
upstream publishing workflow. The new repository requires its own release setup.

Create fresh environments. **Never coinstall `prosaic-castle` and
`cognitive-castle`: both own `cognitive_castle` and legacy `castle*` commands.**
The new provider command rejects detected coinstallation, but cannot repair
files that a package installer has already overwritten.

```sh
export CASTLE_WHEELS=/absolute/path/to/prosaic-castle-candidate-wheels
export LAB_WHEEL=/absolute/path/to/prosaic_integration_lab-0.6.0-py3-none-any.whl
python3.12 -m venv .venv-castle-host
python3.12 -m venv .venv-castle-worker
```

Verify all three candidate hashes before installing. This profile is a mapping,
not the seven-artifact list consumed by the historical `memory_artifacts()` helper:

```sh
.venv-castle-host/bin/python - <<'PY'
import hashlib, json, os
from pathlib import Path
profile = json.loads(Path('dependencies/prosaic-castle-source-2026-10-24.json').read_text())
root = Path(os.environ['CASTLE_WHEELS'])
names = {
    'worker': 'prosaic_castle-3.4.2-py3-none-any.whl',
    'adapter': 'b3_prosaic_memory_castle-0.1.0-py3-none-any.whl',
    'sue': 'cognitive_castle_sue-0.1.0-py3-none-any.whl',
}
for kind, filename in names.items():
    wheel = root / filename
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == profile[kind]['wheel_sha256'], filename
    print('Verified:', filename)
PY
```

An absent file or hash mismatch is a setup failure. Get the correct bundle;
do not substitute an arbitrary same-name/version download. The profile also
pins the worker source archive and preserved historical profile hashes.

## 2. Install the host and the lean worker separately

The host uses the Lab's existing public SDK pins. Install its hash-locked
dependencies, download the five exact public SDK wheels from the manifest's
immutable URLs, and let the installer verify their hashes:

```sh
.venv-castle-host/bin/python -m pip install --require-hashes -r dependencies/requirements.lock
.venv-castle-host/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases.json
.venv-castle-host/bin/python scripts/install_dependencies.py --manifest dependencies/releases.json
.venv-castle-host/bin/python -m pip install --no-deps "$LAB_WHEEL"
```

Install only the optional host pieces you intend to use. These are separate
commands so SUE-only review does not need the memory adapter or worker:

```sh
# For Castle memory:
.venv-castle-host/bin/python -m pip install --no-deps "$CASTLE_WHEELS/b3_prosaic_memory_castle-0.1.0-py3-none-any.whl"
# For SUE review:
.venv-castle-host/bin/python -m pip install --no-deps "$CASTLE_WHEELS/cognitive_castle_sue-0.1.0-py3-none-any.whl"
.venv-castle-host/bin/python -m pip check
```

For the lean worker on **macOS ARM64 with Python 3.12**, use the separate
[worker dependency lock](../dependencies/prosaic-castle-worker-macos-arm64.lock):

```sh
.venv-castle-worker/bin/python -m pip install --require-hashes -r dependencies/prosaic-castle-worker-macos-arm64.lock
.venv-castle-worker/bin/python -m pip install --no-deps "$CASTLE_WHEELS/prosaic_castle-3.4.2-py3-none-any.whl"
.venv-castle-worker/bin/python -m pip check
.venv-castle-worker/bin/prosaic-castle-provider --help
```

This profile uses LanceDB 0.40.0, PyArrow 26.0.0 and PyYAML 6.0.3. Its default
FTS provider requires neither Torch, sentence-transformers, spaCy nor SML.
The macOS lock is not a qualified Linux lock. Native Linux AMD64/ARM64
qualification remains required; historical r7 Linux results do not qualify
this new distribution.

## 3. Enable memory for one trusted owner

Continue with [quickstart steps 3–5](castle-quickstart.md#3-connect-your-own-castle-palace)
to prepare a palace, create a trusted host binding, then ask, review and resume.
Use the environments above and replace the binding's worker command with:

```json
"worker_command": ["/absolute/path/to/this/checkout/.venv-castle-worker/bin/python", "-I", "-m", "prosaic_castle.provider_worker"]
```

Keep `profile: "memory-fts-v1"` and `recency_boost: false` for raw FTS ordering.
Enable memory explicitly with `"memory": {"enabled": true, "bindings": [...]}`.
The host chooses the principal, namespace, paths and allowed wings from trusted
policy; a model or client cannot choose them. Explicit preparation may create
an index; provider reads do not silently repair the palace.

An existing populated palace can be read without installing NLP/model extras.
For the quickstart's **legacy import commands only**, install the fork's
`legacy` extra into the worker environment first, then provision the compatible
spaCy model and local embedding weights as instructed there:

```sh
.venv-castle-worker/bin/python -m pip install "prosaic-castle[legacy] @ file://$CASTLE_WHEELS/prosaic_castle-3.4.2-py3-none-any.whl"
```

That optional installation makes the worker environment heavy; use a separate
import environment if you want the read worker to remain lean. Import only
authorized files or exported sessions. This does not continuously capture
future work. The separate standalone fast-memory sidecar is not automatically
part of the provider's LanceDB palace.

Dense retrieval requires both the explicit `dense` extra and the legacy
`memory-v1` profile. It is separate from this default profile and its lean
qualification. Installing extras alone does not enable retrieval or authorize
model execution.

To disable memory, omit its settings or use `"memory": {"enabled": false}`
with no bindings. New captures stop; a previously accepted workflow can resume
from its already frozen evidence under its existing owner/revision policy.

## 4. Enable SUE only for selected sources

SUE is currently for experimental evaluation. The [corrected Qwen rerun](verification/review-contract-fixes-2026-10-24.md)
fixes the critic contract and restores canonical guidance, but SUE responses
still fail validation. Keep review disabled for normal work. Those findings do
not change the separately qualified memory provider.

Use the [SUE walkthrough and host API](sue-review.md#try-the-credential-free-walkthrough),
replacing `.venv-sue` in its commands with `.venv-castle-host`. Skip that guide's
older engine installation section: the candidate hash in this profile differs
because of archive timestamps, while the qualified package payload and engine
identity remain unchanged. The engine identity is
`bbde4669d1eb069dcb8c72e121cd08be4ca953b349f9243b9e650e0d1b596f0b`.

Enable review explicitly with `"review": {"enabled": true, ...}` using the
documented review settings. Start freezes the host-selected documents, or
explicitly selected Castle records, and pauses with zero model calls. Review
executes only after the authorized owner resumes the saved revision. Expiration
includes approval time; it does not reset on resume. Reports are advisory.

Omit review settings or use `"review": {"enabled": false}` to disable it.
Memory can remain enabled or disabled independently. Installing SUE alone does
not grant access to a palace. Castle-derived sources retain strict namespace,
wing, revision, exact-byte and provenance checks. Snapshot verification accepts
the known provider wire encoding and historical sorted encoding only when their
computed digests match; it does not bypass source or scope validation.

## What is retained, and what this profile supports

| Capability | Retained legacy behavior | New profile boundary |
| --- | --- | --- |
| LanceDB storage and existing palace formats | Legacy modules, import APIs and commands remain | Scoped, read-only FTS provider; explicit preparation required |
| Dense retrieval and neural reranking | Retained with optional dependencies | Opt-in `dense` extra plus `memory-v1`; absent from lean default |
| NLP import and session mining | Retained with `legacy` extra and provisioned models | Separate operator action; no automatic capture |
| Recency/rule scoring | Legacy paths retained | Raw FTS default; recency explicit; shipped Python boosts are a separate opt-in API |
| SOAR productions | Original rules, bridge and custom-rule paths retained | Python policy recognizes exact shipped bytes; rejects custom rules; real SML equivalence remains pending |
| Standalone SUE source selection | Legacy path permits up to 2 MiB / 2,000 drawers | Lab SUE accepts 1–16 selected sources, at most 64 KiB total UTF-8 text |
| SUE engine and adapter APIs | Canonical engine/manifest and imports preserved | Separately installed engine; frozen scope/engine identity and owner/revision checks |
| Judge, entity refinement, corpus origin | Original modules and transports retained | Separate approved [host jobs](castle-model-jobs.md), with no automatic writeback |
| Transport coverage | Original CLI/provider modes retained | Host jobs admit only their documented OpenAI-compatible HTTP path; live transport parity is pending |
| Durable resume and usage | Harness and Runtime public APIs own these | Saved evidence and accepted receipts; no automatic retry of uncertain model work |
| Model-facing memory tools | Adapter API retained | Current Runtime must expose the explicit error capability; host snapshots work without granting model tools |
| Platform qualification | Historical receipts preserved | New fork requires its own installed native Linux gates; no review-quality claim |

## Maintainer qualification command

This credential-free gate needs Docker for an owned disposable PostgreSQL
fixture, the installed matching Lab/engine/adapter wheels in the host, a truly
lean installed worker, and this checkout's tests. It exercises synthetic cases;
it does not run a real LLM. Use absolute paths and a new output directory:

```sh
.venv-castle-host/bin/python -I -m lab_runner.prosaic_castle_fixture \
  --enable --postgres-version 16 \
  --lab-wheel "$LAB_WHEEL" \
  --engine-wheel "$CASTLE_WHEELS/cognitive_castle_sue-0.1.0-py3-none-any.whl" \
  --adapter-wheel "$CASTLE_WHEELS/b3_prosaic_memory_castle-0.1.0-py3-none-any.whl" \
  --worker-wheel "$CASTLE_WHEELS/prosaic_castle-3.4.2-py3-none-any.whl" \
  --worker-python "$PWD/.venv-castle-worker/bin/python" \
  --tests-root "$PWD/tests" --output /absolute/new/evidence-pg16
```

Repeat with PostgreSQL 18 and a different output directory. Verify the rebuilt
sdist wheel set too; byte-identical wheels execute the same installed payload.
Changed rebuilt payloads require fresh acceptance. The gate requires exactly
76 distinct named cases, including all eight optional model-job cases, zero
skips/failures/errors, pinned worker/adapter/engine hashes, verified installed
bytes and verified fixture cleanup. Inherited pytest filters are removed.
Inspect `qualification.json`, `pytest.log` and `result.xml`; this
command is a recipe, not a claim that a platform or candidate has passed.
Without `--enable`, it reports disabled and allocates nothing. The separate
requirements comparison checks frozen synthetic cases; it cannot establish
real-model review benefit or custom SOAR/transport equivalence.
