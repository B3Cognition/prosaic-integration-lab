---
name: incident-handoff
description: Correct an operational handoff without overstating causality.
tools: write
---
Read packet.json and the existing handoff.json. Correct the handoff for the next shift. Distinguish mitigation from a confirmed root cause. Compute the affected window in whole minutes from the first elevated errors to the return to baseline. Use the supplied aggregate request counts, not the peak error percentage, for impact.

Write only handoff.json as a JSON object with exactly these fields: status (ACTIVE, MITIGATED or RESOLVED), rootCause (CONFIRMED or UNCONFIRMED), impact (failedRequests, totalRequests and windowMinutes), summary (40 to 100 English words covering mitigation, impact and uncertainty), evidence (the IDs of timeline and metrics evidence), and actions (objects with owner and action, one for every assigned follow-up owner). Root-cause confirmation is required for RESOLVED. Keep packet.json unchanged, create no other files, and briefly confirm completion.
