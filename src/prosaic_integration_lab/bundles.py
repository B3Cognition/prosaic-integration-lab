"""Retained public SDK bundles registered solely by trusted host code."""


class BundleRegistry:
    def __init__(self):
        self._bundles = {}

    def register(self, bundle):
        from prosaic_harness import WorkflowBundle
        if type(bundle) is not WorkflowBundle:
            raise ValueError('bundle_conflict')
        key = (bundle.version, bundle.identity)
        self._bundles.setdefault(key, bundle)
        return self._bundles[key]

    def resolve(self, version, identity):
        try:
            bundle = self._bundles[(version, identity)]
        except (KeyError, TypeError):
            raise ValueError('bundle_unavailable') from None
        if bundle.version != version or bundle.identity != identity:
            raise ValueError('bundle_conflict')
        return bundle
