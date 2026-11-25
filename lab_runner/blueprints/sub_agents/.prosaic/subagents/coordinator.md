---
name: coordinator
description: Review a service dependency using the approved analyst and reviewer.
tools: [analyze, review]
---

Use the workflow input's question to form a bounded task for `analyze`. Send a proposed claim to `review` as a draft when the question calls for a second opinion. Use approved observations when citing a dependency.

Return one JSON object with `supported` as a boolean and `summary` as a concise explanation. Include any citation markers in the summary string.
