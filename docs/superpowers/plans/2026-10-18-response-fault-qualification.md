# Provider-neutral response fault qualification

User authorization: implement failure diagnostics and qualify response/usage
faults offline under the current limits, before another live comparison. Native
execution continues. No live inference, increase, push or release in this task.

- [x] Consume the new Runtime diagnostic metadata through installed public APIs;
  Harness owns receipts and recovery. Do not import private SDK code or patch
  SDK engines. Prior unknown reservations and all live evidence remain charged.
- [x] Create credential-free native HTTP fixtures for both wire formats. Include
  healthy JSON/SSE, missing/incomplete/invalid usage, provider error, contradictory
  error+tool envelope, unexpected shape, malformed/duplicate JSON, invalid UTF-8,
  non-2xx/redirect, and unknown usage after a successful tool lookup.
- [x] Verify original evidence is untouched and copied receipt bytes/returned
  receipt digests preserve diagnostics under network-denied recovery. Unknown
  usage cannot cause a further provider dispatch. Known permanent provider errors
  stop without tools. Full synthetic sample caps remain4requests/2tools/8192tokens/
  600seconds/output512. No live allowance is spent by these fixtures.
- [x] Bind a separate explicit checksum manifest to Runtime0.9.8+diagnostics.1
  and the four unchanged public SDK wheels. Update only this private Lab
  candidate's packaged provenance; preserve active releases and prior candidates.
- [ ] Full Lab suite, exact-source wheel/sdist and installed payload audit;
  repeat36installed fault/replay cases with that exact Lab candidate,14continuation
  and10legacy memory/replay scenarios. Record earlier setup/operator failures.
- [ ] Preserve private qualification evidence and35historical ledger hashes.
  Report capability, limitations and readiness. Memory stays experimental.

Ruling: the first generic candidate environment used Runtime's Python3.11 floor,
which Lab correctly rejected before inference because Lab requires3.12. A new
Python3.12 environment uses the existing hash-locked requirements. No version
floor is relaxed. Lab's earlier45failures are provenance enforcement against an
unbound SDK candidate; the new explicit manifest addresses that mismatch without
relaxing validation. The Runtime candidate's executable payload is source21cca3f;
later Runtime qualification-gate changes only align private version expectations.

Ruling: correct synthetic SSE framing to emit delta without a duplicate message
container, and assert one request/150known tokens for a permanent contradictory
provider error. Preserve failed operator outputs; they are not product failures
or completed qualification. The last36-scenario smoke passed, and final exact
Lab candidate qualification remains pending.
