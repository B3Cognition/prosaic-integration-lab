# Constrained operational recovery

The approved fix queue's issue 9 covers an owner-authenticated terminal recovery
interface and interrupted credential-delivery recovery. Implement these before
the finite HTTP budget qualification, preserving all historic crash evidence.

The CLI inspects filtered HTTP run/usage views using a token supplied via a
secret-managed environment variable. Mutations require the exact reviewed
revision and explicit action; there are no tenant/billing override arguments,
automatic revision refreshes or mutation retries. Missing checkpoint/start
uncertainty permits inspection/reconciliation only. Missing receipt cannot prove
absence of an external effect. Interrupted-call retry additionally requires
explicit effect-risk acknowledgement; the SDK's durable budget remains authority.
Unknown accounting never becomes zero or an invoice through recovery.

Credential delivery switches one atomic pointer to a complete private generation
containing runtime config and its matching CA. A failed/killed staging job never
publishes a mixed generation, and random staging names do not block later
delivery. Preserve prior/orphan generations for reviewed retirement rather than
deleting unexplained files automatically. Runtime config/DSN formats and the
existing LAB_CONFIG path remain compatible. Test actual private-volume permissions
and restart after a real root delivery job abort before publication.

Required tests: unit action/revision/uncertainty policy; functional terminal CLI
failure sanitization and owner access; owned A/B receipt crash recovery without
dispatch, lease-busy/no blind retry, unknown/uncertain inspection and root delivery
abort/retry. The Keycloak TLS lane additionally interrupts delivery after writing
a different CA and proves the old generation still authenticates on replica
restart. Engine creation uncertainty remains a failed original receipt; later
inventories are separate evidence and never rewrite it as a successful run.
