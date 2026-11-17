import subprocess


def test_release_export_uses_only_recorded_commit_and_excludes_build_debris(tmp_path):
    from scripts.build_castle_release_bundle import export_commit

    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    (source / "tracked.py").write_text("committed = True\n")
    (source / ".gitignore").write_text("ignored.py\n")
    subprocess.run(["git", "add", "."], cwd=source, check=True)
    subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "-qm", "fixture"], cwd=source, check=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    (source / "untracked.py").write_text("unexpected = True\n")
    (source / "ignored.py").write_text("stale = True\n")
    (source / "tracked.py").write_text("committed = False\n")

    exported = tmp_path / "export"
    export_commit(source, commit, exported)

    assert (exported / "tracked.py").read_text() == "committed = True\n"
    assert sorted(path.name for path in exported.iterdir()) == [".gitignore", "tracked.py"]
    assert (source / "untracked.py").read_text() == "unexpected = True\n"
