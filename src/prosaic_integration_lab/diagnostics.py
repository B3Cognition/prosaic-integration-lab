"""Safe stage diagnostics: exception messages and request contents are excluded."""
from contextlib import contextmanager
import json
import logging
import re
import psycopg
from fastapi import HTTPException
from prosaic_harness import StoreError
from prosaic_runtime import AccountingError

logger = logging.getLogger('prosaic_integration_lab')


@contextmanager
def stage(name):
    try:
        yield
    except Exception as error:
        classes = ((psycopg.Error,'DatabaseError'),(StoreError,'StoreError'),(AccountingError,'AccountingError'),
                   (HTTPException,'HTTPException'),(ValueError,'ValueError'),(TimeoutError,'TimeoutError'))
        category = next((label for kind,label in classes if isinstance(error,kind)),'UnexpectedError')
        record = {'event':'operation_failed','stage':name,'error_class':category}
        sqlstate = getattr(error,'sqlstate',None)
        if isinstance(error,psycopg.Error) and isinstance(sqlstate,str) and re.fullmatch('[A-Z0-9]{5}',sqlstate):
            record['sqlstate'] = sqlstate
        code = getattr(error,'code',None)
        if isinstance(error,StoreError) and code in {
            'run_busy','revision_conflict','run_already_exists','receipt_conflict','store_unavailable',
            'store_uninitialized','store_incompatible','store_busy','store_corrupt','run_not_found',
            'lease_lost','operation_timeout','pool_timeout'}:
            record['store_code'] = code
        logger.warning(json.dumps(record))
        raise
