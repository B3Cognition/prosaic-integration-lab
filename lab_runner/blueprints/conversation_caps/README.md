# Effective conversation input caps

Copy with `python -m lab_runner.blueprints copy conversation-caps /private/project`.
Lab 0.9.8 qualifies this example with Core 0.5.0, Runtime 0.9.16 and Harness
0.9.11; the read-only cap properties were introduced in Harness 0.9.10.

Run `python host.py` to construct admitted bindings and print both effective
limits without contacting an endpoint. The default ordinary and interpreter
caps are both 8192 bytes. `build_bindings(max_input_bytes=..., run_max_input_bytes=...,
interpretation_max_input_bytes=...)` allows explicit tighter, separate caps.
The effective value is the smaller of the conversation and that purpose's
run cap. The host's `limits(bindings)` reports the public SDK properties.

These are complete encoded-request limits, including history and framing;
the user-message limit is a separate boundary. The installed tests grow real
conversation history and prove that the visible cap is the one that refuses
the next dispatch. Both policy declarations retain their own values.

ALWAYS derive `ConversationScope`, authorization and private storage from the
trusted application host. NEVER derive identity or authority from these prose
files or model output. Use the ordinary public Conversation/session-store APIs
with these bindings; provider execution still requires explicit host consent.

This constructs new bindings for new sessions. Existing saved sessions keep
their sealed policy and identity; changing configuration is not a session
migration. Keep the original bindings for replay/recovery of old sessions.
