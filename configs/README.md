# Optional local inference

`runtime-local.example.yml` uses the Runtime 0.6.0 configuration contract for
the host-side endpoint `http://127.0.0.1:8000/v1`. Authenticated discovery
identified `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit`; this smaller model
is selected for optional smoke tests. Runtime reads authentication directly
from `~/.omlx_token` using `api_key_file`. Never put the key in YAML or Git.

This file is an optional configuration example, not a runnable lab command.
Run `.venv/bin/python scripts/local_smoke.py` for the explicit host-side smoke.
The implementation plan is approved; service and acceptance runner work is
tracked in `docs/verification/progress.md`.
Synthetic inference remains the default for repeatable accounting assertions.
Do not apply synthetic rate cards to real local-model usage as if they were
provider prices; report missing measurements explicitly.

For container replicas, loopback addresses refer to the container itself.
Docker Desktop can use `http://host.docker.internal:8000/v1` if the host server
is reachable that way; verify connectivity before selecting this address.
Linux Docker/Podman host routing requires explicit engine-specific setup, and
a server bound only to host loopback may not accept bridged connections.
Do not silently broaden the model server's network binding. Resolve this when
implementing the owned stack, keeping the model endpoint trusted host config.
