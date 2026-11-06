"""Catalogue-desk blueprint: tagged prose, host-registered guards and the host wiring that runs them.

Importing the package checks the installed SDKs first, so a Core without
``parse_rules`` or a Runtime without rule admission is a clear refusal rather
than an import error deep inside a module.
"""

import prosaic as _core

if not all(callable(getattr(_core, name, None)) for name in ('parse_rules', 'strip_tags')):
    raise ImportError(
        'catalogue-desk blueprint needs Prosaic Core with parse_rules and strip_tags (9d5a02f or later) '
        'and Prosaic Runtime with rule_admission_v1'
    )

import prosaic_runtime as _runtime  # noqa: E402  (imported after the Core check on purpose)

if 'rule_admission_v1' not in getattr(getattr(_runtime, 'ProsaicRuntime', None), 'capabilities', ()):
    raise ImportError(
        'catalogue-desk blueprint needs Prosaic Runtime with rule_admission_v1 '
        'and Prosaic Core with parse_rules and strip_tags (9d5a02f or later)'
    )
