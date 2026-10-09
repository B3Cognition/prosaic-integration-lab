# Owned production ingress proof

Issue 11 acceptance is the approved implementation brief. Use a pinned NGINX
fixture, generated private TLS credentials and the existing exact-owned engine
resource registry. No existing ingress or production identity provider is used.

- Require certificate verification and round-robin routing to both replicas.
- Bound initial headers, body buffering, connection capacity and upstream waits.
- Disable automatic upstream retries; uncertain POST outcomes require inspection.
- Strip identity forwarding headers and preserve bearer authentication authority.
- Test cross-replica owner review, idempotency, lost replies, partial headers,
  body bounds, worker restart and graceful gateway drain with real containers.
- Keep nginx access/error logs disabled to avoid URI or raw private diagnostics;
  sanitized observability is tracked separately in issue 13.
- Record unit policy, functional rendering and real PostgreSQL 16/18 receipts.

The reference terminates TLS on the owned private container network. Production
operators must restrict backend reachability and supply managed certificates;
public service replicas must never be exposed around this ingress.
