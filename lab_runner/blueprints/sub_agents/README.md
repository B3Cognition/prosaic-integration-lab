# Dependency analyst and reviewer

Use `build_host` with a trusted conversation scope, captured Markdown, a reviewed local graph lookup, current grants, and a fenced tool journal. Provision the owned store using `initialize(sub_agents=True)`. Pass the returned bindings to Harness `Conversation` together with the host-owned execution context and accounting recorder for the selected provider.

The analyst receives the analyst pack and its graph lookup. The optional reviewer receives its own brief and an explicitly schema-checked draft. The coordinator writes the answer and can cite observations delivered by Runtime.
