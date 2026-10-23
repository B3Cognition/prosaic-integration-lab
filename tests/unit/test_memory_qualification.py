import json
from pathlib import Path

import pytest


@pytest.mark.parametrize("damage", ["missing", "identity"])
def test_memory_artifacts_reject_incomplete_or_misidentified_family(tmp_path, damage):
    from lab_runner.memory import memory_artifacts

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "dependencies/memory-candidates.json").read_text())
    if damage == "missing":
        manifest["artifacts"].pop()
    else:
        manifest["artifacts"][0]["version"] = "999.0.0"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="family|identity"):
        memory_artifacts(path, tmp_path)


def test_default_memory_lane_allocates_nothing(monkeypatch, capsys):
    from lab_runner import memory

    monkeypatch.setattr(memory, "verify_installed", lambda *a: pytest.fail("allocated"))
    assert memory.main([]) == 0
    assert json.loads(capsys.readouterr().out)["reason"] == "disabled"


def test_lost_create_outcome_recovers_only_exact_owned_container(monkeypatch):
    from lab_runner import memory_fixture as fixture

    resource = fixture.OwnedPostgres()
    removed = []

    def command(*args):
        if args[1] == "ps":
            assert f"label=io.prosaic.lab.owner={resource.owner}" in args
            assert "label=io.prosaic.lab.resource=optional-memory-postgres" in args
            return "a" * 64
        if args[1] == "inspect":
            return json.dumps(
                [
                    {
                        "Id": "a" * 64,
                        "Config": {
                            "Labels": {
                                "io.prosaic.lab.owner": resource.owner,
                                "io.prosaic.lab.resource": "optional-memory-postgres",
                            }
                        },
                    }
                ]
            )
        removed.append(args[-1])
        return ""

    monkeypatch.setattr(fixture, "command", command)
    from types import SimpleNamespace

    monkeypatch.setattr(
        fixture.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1)
    )
    resource.close()
    assert removed == ["a" * 64] and resource.manifest["cleanup_verified"]


def test_cleanup_refuses_resource_label_mismatch(monkeypatch):
    from lab_runner import memory_fixture as fixture

    resource = fixture.OwnedPostgres()
    resource.container = "a" * 64
    monkeypatch.setattr(
        fixture,
        "command",
        lambda *args: json.dumps(
            [
                {
                    "Id": resource.container,
                    "Config": {
                        "Labels": {
                            "io.prosaic.lab.owner": resource.owner,
                            "io.prosaic.lab.resource": "different-resource",
                        }
                    },
                }
            ]
        ),
    )
    with pytest.raises(ValueError, match="resource label"):
        resource.close()
    assert not resource.manifest["cleanup_verified"]
