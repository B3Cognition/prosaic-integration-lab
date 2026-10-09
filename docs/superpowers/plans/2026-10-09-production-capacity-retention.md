# Bounded pilot capacity and retention qualification

Issue 14 acceptance is the approved brief. Keep the two-replica synchronous
blueprint explicitly a bounded pilot rather than certify untested general scale.

- Configure write/read ceilings within the tested pool limits and per-tenant
  admission quotas; retain per-actor single-operation admission. No queued work
  acquires a reservation without a permit. Quotas are per replica, not invoice caps.
- Bound persistent application reservations atomically with a database advisory
  transaction lock and global/tenant record ceilings. Reusing an existing key
  remains permitted at the ceiling; never expire idempotency or uncertain evidence.
- Add private streaming evidence archival/classification using public installed
  SDK read APIs. Archive copies are not destructive retention or point-in-time
  database backups; preserve the source and all unresolved records. Full restore
  remains the existing required backup lane.
- Add finite open-loop arrival-rate/duration profiles with a bounded client
  executor, explicit client shedding, latency/error/rejection/throughput targets,
  independently counted model dispatch and truthful synthetic billing coverage.
- Cover tenant fairness, cross-replica atomic record ceilings, advisory lock and
  connection pressure, unknown/uncertain archival and finite soak/overload profiles
  in owned PostgreSQL 16/18 tests. Run documented pilot baseline and overload
  qualification, preserve both SLO pass/fail evidence and exact provenance.
- Leave native remote matrix activation, extended hardware-specific soak,
  distributed monetary quotas, HA/failover and destructive evidence retirement
  as explicit publication/deployment/feature boundaries. Do not claim them tested.
