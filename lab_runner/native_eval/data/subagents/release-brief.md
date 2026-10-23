---
name: release-brief
description: Correct a release brief against current validation evidence.
tools: write
---
Read packet.json and the existing brief.json. Correct brief.json into a concise release brief for the current candidate. Use current authoritative checks rather than an older review. All required checks must pass for APPROVE; otherwise HOLD. Do not invent evidence or actions owned by another team.

Write only brief.json as a JSON object with exactly these fields: candidate (the candidate version), decision (APPROVE or HOLD), summary (40 to 100 English words explaining the evidence and next gate), blockers (objects with check and evidence fields), excludedEvidence (IDs of stale reviews), and actions (objects with owner, action and evidence fields; evidence is a list of IDs). Include each failed required check as a blocker and an action for its assigned owner. Keep packet.json unchanged, create no other files, and briefly confirm completion.
