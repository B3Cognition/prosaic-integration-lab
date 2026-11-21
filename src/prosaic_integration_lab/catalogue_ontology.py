"""Exact SDK families supporting catalogue ontology and the inherited Lab gates."""

TRAIN = {
    'b3-prosaic': '0.5.1',
    'b3-prosaic-harness': '0.9.18',
    'b3-prosaic-runtime': '0.9.23',
    'b3-prosaic-runtime-postgres': '0.3.0',
    'b3-prosaic-harness-postgres': '0.4.5',
}

SANDBOX_RELEASE_TRAIN = {
    **TRAIN,
    'b3-prosaic-runtime': '0.9.27',
    'b3-prosaic-harness': '0.9.20',
}
ONTOLOGY_TRAINS = (TRAIN, SANDBOX_RELEASE_TRAIN)
