# Safe events and captured citations

This candidate requires Runtime 0.9.20.dev2 and Harness 0.9.14.dev2.
Copy with `python -m lab_runner.blueprints copy tool-evidence DESTINATION`.
`host.py` accepts the application's authenticated lookup and explicit current
permissions. The tool returns actual bounded records, selects public component
and count event fields, and declares an exact captured evidence selection.
No network call is made when importing this example.

Create an owned capable store with `initialize(tool_contracts=True)` during
provisioning. Construct `Conversation` with these bindings and your authenticated
`ConversationScope`, then call `create()` and `send(...)`. Forward approved SDK
events using `forward_event`; your application owns SSE delivery. Use the returned
answer and citations together after acceptance. Citation checks withhold answer
text; tool progress remains live. Private locators and credentials never belong in
public events. Keep `lookup` bounded and enforce the application's authorization
before returning records. Change producer/source revision identities when the
underlying contract changes.

Use `citation_view` to open a captured selection with current permission. For
reuse, create `retain_citation(...)` from an adopted owned receipt and pass it via
`retained_evidence=(reference,)`. Raw IDs in history grant nothing. No URL fetches
are needed to resolve a receipt. Citations establish provenance, not entailment.
MCP, parallel calls and sub-agent orchestration are separate follow-ups.
