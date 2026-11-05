from copy import deepcopy

import pytest


def receipt():
    return {
        "enabled": True,
        "qualified": True,
        "synthetic_only": True,
        "private_state_exported": False,
        "manifest_sha256": "a" * 64,
        "artifacts": [{"distribution": "fixture", "version": "1", "sha256": "b" * 64}],
        "tests": 6,
        "failures": 0,
        "skipped": 0,
        "postgres": {"architecture": "amd64", "cleanup_verified": True,
                     "server_version": "16.15", "separate_runtime_role": True},
    }


def validate(value):
    from scripts.castle_release_qualification import validate_receipt

    return validate_receipt(
        value,
        architecture="amd64",
        postgres_major=16,
        manifest_sha256="a" * 64,
        expected_artifacts=receipt()["artifacts"],
    )


def test_enabled_receipt_requires_exact_results_and_selected_bytes():
    value = receipt()
    assert validate(value) is None
    assert value == receipt()


@pytest.mark.parametrize(
    "change",
    [
        {"qualified": False},
        {"enabled": False},
        {"tests": 0},
        {"tests": 5},
        {"tests": 7},
        {"failures": 1},
        {"skipped": 1},
        {"tests": True},
        {"private_state_exported": True},
        {"synthetic_only": False},
        {"manifest_sha256": "c" * 64},
        {"artifacts": []},
        {"postgres": {"architecture": "arm64", "cleanup_verified": True}},
        {"postgres": {"architecture": "amd64", "cleanup_verified": False}},
        {"postgres": {"architecture": "amd64", "cleanup_verified": True,
                      "server_version": "18.1", "separate_runtime_role": True}},
        {"postgres": {"architecture": "amd64", "cleanup_verified": True,
                      "server_version": "16.15", "separate_runtime_role": False}},
    ],
)
def test_enabled_receipt_refuses_partial_wrong_arch_or_unverified_evidence(change):
    value = deepcopy(receipt())
    value.update(change)
    with pytest.raises(ValueError):
        validate(value)


@pytest.mark.parametrize("system,machine", [("Darwin", "arm64"), ("Linux", "aarch64")])
def test_native_architecture_is_measured_instead_of_trusting_matrix_labels(system, machine):
    from scripts.castle_release_qualification import native_architecture

    with pytest.raises(ValueError):
        native_architecture("amd64", system=system, machine=machine)


@pytest.mark.parametrize("expected,machine", [("amd64", "x86_64"), ("arm64", "aarch64")])
def test_native_linux_architectures_are_accepted(expected, machine):
    from scripts.castle_release_qualification import native_architecture

    assert native_architecture(expected, system="Linux", machine=machine) == expected
