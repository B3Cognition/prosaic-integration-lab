import pytest


def test_registry_requires_public_immutable_bundle_and_exact_retained_identity():
    from prosaic_integration_lab.bundles import BundleRegistry
    registry = BundleRegistry()
    with pytest.raises(ValueError, match='bundle_conflict'):
        registry.register(object())
    with pytest.raises(ValueError, match='bundle_unavailable'):
        registry.resolve('unavailable', 'a'*64)


def test_registry_retains_both_versions_and_does_not_substitute_latest(bundle_factory):
    from prosaic_integration_lab.bundles import BundleRegistry
    registry = BundleRegistry()
    first, second = bundle_factory(), bundle_factory('v2', max_calls=11)
    registry.register(first)
    registry.register(second)
    assert registry.resolve('v1', first.identity) is first
    assert registry.resolve('v2', second.identity) is second
    with pytest.raises(ValueError, match='bundle_unavailable'):
        registry.resolve('v1', second.identity)


def test_registry_detects_changed_declared_material(bundle_factory):
    from prosaic_integration_lab.bundles import BundleRegistry
    registry = BundleRegistry()
    bundle = bundle_factory()
    identity = bundle.identity
    registry.register(bundle)
    object.__setattr__(bundle, 'identity', 'a'*64)
    with pytest.raises(ValueError, match='bundle_conflict'):
        registry.resolve('v1', identity)

