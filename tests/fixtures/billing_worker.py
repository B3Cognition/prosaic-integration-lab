"""Acceptance-only crash barrier; never installed in the application image."""
import json
import os
from pathlib import Path
import sys
import threading
import httpx
from prosaic_integration_lab.billing_store import BillingStore
from prosaic_integration_lab.billing_delivery import LagoClient

config = json.loads(Path(sys.argv[1]).read_text())
store = BillingStore(config['billing_dsn'])
row = store.claim(1,1)[0]
if sys.argv[2] == 'after-send':
    with httpx.Client() as http:
        LagoClient(config['lago']['url'],config['lago']['key'],http).send(row['payload'])
barrier = Path(sys.argv[3])
with barrier.open('x') as output:
    output.write(row['key'])
    output.flush()
    os.fsync(output.fileno())
threading.Event().wait()
