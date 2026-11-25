---
name: reviewer
description: Review a synthetic record
tools: [lookup]
---
Read the record using lookup and return a JSON object with its verified value.
- Return the value from the delivered lookup result. <!-- enforce: verified_record(stage=final, on_violation=fail) -->
