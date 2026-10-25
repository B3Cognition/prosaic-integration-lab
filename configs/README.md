# Optional local inference

For released Runtime 0.9.8 unified pools, start with the
[guided model setup](../docs/quickstart.md#4-connect-real-models-explicit-opt-in).
Copy `unified-runtime.example.yml`,
`native-runtime.example.yml` and `runtime-comparison-local.example.yml` together
into private operator storage. Adjust the native model/login paths and local
model/authentication reference. Relative config references resolve from the
unified file; never commit credentials or a private capacity file. Merely loading
these files authorizes no calls. The
[unified CLI guide](../docs/unified-runtime-pools.md) supplies separate native/API
permissions and explicit deadlines, attempts and request/tool limits.

The new [conversation guide](../docs/conversations.md) includes
`conversation-conformance.example.json`, a private Runtime YAML/allowance recipe.
Its pure preflight makes zero provider requests and opens no credential files.
The live command reserves twelve shared requests, uses separate fixed balanced/
strong sessions and requires explicit `--live-local` or `--live-hosted` opt-in.
Run `python scripts/conversation_conformance.py --config PRIVATE.json --max-calls
12 --export SAFE.json` for pure preflight; add the live flag to contact the
approved endpoint. No actual live calls have qualified this branch. The command
uses nondurable diagnostic accounting and private temporary session/run files;
the shared allowance persists uncertain consumption across crashes. The existing
routing smoke below is independent.

`runtime-local.example.yml` uses the released Runtime configuration contract for
the host-side endpoint `http://127.0.0.1:8000/v1`. Authenticated discovery
identified `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit`; this smaller model
is selected for the default and balanced routes. The strong route selects
`ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`. Runtime reads authentication directly
from `~/.omlx_token` using `api_key_file`. Never put the key in YAML or Git.

Run `.venv/bin/python scripts/local_smoke.py` for the existing single-model
smoke; its `fast` route and default model remain the smaller Qwen Coder model.
For the public factory/Harness routing smoke, use an interpreter containing the
five exact published SDK pins and explicitly authorize all three shared calls:

```sh
.venv/bin/python scripts/local_routing_smoke.py --live-local --max-calls 3
```

The routing command clears every case-insensitive `*_proxy` environment variable
and sets `no_proxy`/`NO_PROXY` to `*` before preflight, credential reads or dispatch.
This bypass also disables system proxy discovery. It restores the exact original
proxy environment on success or exceptions. It then validates every profile and
both routes without reading the credential file. It accepts literal loopback IP endpoints, secret-managed
`api_key_file`, non-streaming responses and at most 512 output tokens. It admits
three separate workflows: omitted tier with empty explicit tier grants, balanced,
then strong. Each invocation permits one provider request, no tools, no retries
and a 60-second deadline. The command reserves failed/uncertain attempts from the
shared three-call allowance and stops at the first failure. Before removing
private temporary state, it loads the checkpoint and invocation receipt through
public `FileRunStore` APIs. Success requires one call, one complete invocation and
its matching receipt, the observed expected profile/request model, one recorded
provider request and zero tool calls. The receipt exports these validated fields
and measured token counts; missing/contradictory evidence fails the case and unknown
counts/usage stay null. A rejected redirect retains its first recorded provider
request and does not proceed to another case.
The tiers prove model selection; they do not establish model quality or prices.
Local inference is never selected by default CI.

Ordinary public-index adoption is a separate credential-free command:

```sh
.venv/bin/python scripts/verify_public_adoption.py \
  --manifest dependencies/releases.json --export /tmp/public-adoption.json
```

It creates a neutral temporary virtual environment, disables inherited installer
configuration, removes proxy variables regardless of casing and bypasses system
proxies. It disables netrc/keyring authentication and interactive prompts, then
runs an isolated cache-free PyPI installation of all
five exact pins with dependencies enabled. It checks pip's archive hashes against
the release manifest, freshly downloads the selected wheel bytes, uses the
existing installed-payload audit, verifies import ownership, CLI help/version,
`pip check` and public factory construction, then rechecks the manifest digest.
Raw logs and pip reports remain in the owned temporary environment and are
deleted with it. The exported receipt contains only verified release identities,
hashes and fixed result fields. Candidate manifests cannot claim public adoption.
Synthetic inference remains the default for repeatable accounting assertions.
Do not apply synthetic rate cards to real local-model usage as if they were
provider prices; report missing measurements explicitly.

For container replicas, loopback addresses refer to the container itself. The
host-side routing script rejects bridged/container host names.
Docker Desktop can use `http://host.docker.internal:8000/v1` if the host server
is reachable that way; verify connectivity before selecting this address.
Linux Docker/Podman host routing requires explicit engine-specific setup, and
a server bound only to host loopback may not accept bridged connections.
Do not silently broaden the model server's network binding. Resolve this when
configuring the owned stack, keeping the model endpoint trusted host config.
