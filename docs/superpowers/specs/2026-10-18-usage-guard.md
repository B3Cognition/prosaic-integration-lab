# Provider-neutral usage guard

The experimental bounded-correction consumer must check normalized numeric token
counts independently of pricing support. A `reported` or `unsupported` usage
observation has complete counts only when input, output and total are nonnegative
integers (not booleans), within the signed 64-bit token range, and input plus
output equals total. Other states and malformed counts are unavailable.

Complete counts enforce each counted input bound and the 512-token output bound
before another request or final acceptance. Unavailable counts latch a stop and
remain unknown in summaries. Raw usage labels and receipts are preserved. The
scorer independently reconstructs the same guard decisions and role costs.
Revision v2 prevents matching against historical v1 policy; historical evidence
and its immutable installed environment remain unchanged.

Qualification is offline with both supported wire formats and public installed
SDKs, including first lookup, worker final, critic and corrector observations,
valid unsupported counts, missing/partial/invalid counts, and read-only recovery.
Per arm limits remain 4 requests / 2 tools / 8,192 tokens / 600 seconds; output
512. Cumulative ceilings remain 1,558 / 637 / 1,976,623. No live requests,
SDK changes, default dependency changes or release. Memory and correction remain
experimental. Push the reviewed Lab branch and open a PR after qualification.
