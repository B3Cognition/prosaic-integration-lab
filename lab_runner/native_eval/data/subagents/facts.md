---
name: facts
description: Read a synthetic inventory and make a deterministic decision.
tools: read
---
Read inventory.json. Return only a JSON object with total equal to the sum of counts and decision BLOCK if blockingIssue is true, otherwise APPROVE. Do not change any files.
