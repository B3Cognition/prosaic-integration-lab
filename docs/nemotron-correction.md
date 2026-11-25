# Nemotron lookup correction

Install Lab 0.9.19 and use the checksum-pinned SDK profile in
`dependencies/releases-nemotron-correction.json`. The release source includes
`scripts/prepare_dependencies.py` and `scripts/install_dependencies.py` to
download and install the verified wheels. Copy the blueprint with:

```sh
python -m lab_runner.blueprints copy nemotron-correction ./nemotron-correction
```

The copied `host.py` binds the nonstreaming Nemotron endpoint, an
empty-argument `lookup`, an authorization callback, and a guard that accepts
only the delivered lookup value. Pass an oMLX OpenAI-compatible base URL and
the trusted callback pair to `build_workflow` and run the admitted workflow
via Harness. To demonstrate the optional-first-tool case, set
`require_lookup=False`. In either case, the final guard requires the lookup
value before accepting any answer.

The first request and final continuation keep the ordinary wire format. The
one correction can spend the second request on the constrained native call.
The configured budget covers three provider requests and one tool call.
On resume, reconstruct the workflow with the same endpoint and options.

The installed acceptance fixtures are synthetic. They cover optional and
required first tools, a provider ignoring the constraint, a mismatched
final answer, and successful receipt reuse with no additional requests.
