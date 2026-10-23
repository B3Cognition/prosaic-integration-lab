"""Explicit optional-memory qualification. Disabled invocation starts nothing."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile


def memory_artifacts(manifest, directory):
    """Require complete wheel identities at both allocation and build boundaries."""
    from prosaic_integration_lab.dependencies import read_manifest, verify_dependencies
    from packaging.utils import parse_wheel_filename
    from packaging.version import Version

    selected = read_manifest(manifest)
    names = {row["distribution"] for row in selected["artifacts"]}
    if names != {
        "b3-prosaic",
        "b3-prosaic-runtime",
        "b3-prosaic-runtime-postgres",
        "b3-prosaic-harness",
        "b3-prosaic-harness-postgres",
        "b3-prosaic-memory-castle",
        "cognitive-castle",
    }:
        raise ValueError("complete selected memory candidate family required")
    for row in selected["artifacts"]:
        try:
            name, version, _, _ = parse_wheel_filename(row["filename"])
            if name != row["distribution"] or version != Version(row["version"]):
                raise ValueError("wheel identity mismatch")
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid memory wheel identity") from error
    verify_dependencies(manifest, directory)
    return selected


def verify_installed(manifest, directory, worker_python):
    selected = memory_artifacts(manifest, directory)
    for row in selected["artifacts"]:
        if row["distribution"] == "cognitive-castle":
            script = """import importlib.metadata as m,sys,zipfile
d=m.distribution('cognitive-castle')
assert d.version==sys.argv[2]
with zipfile.ZipFile(sys.argv[1]) as z:
 for n in z.namelist():
  if n.endswith('.py'): assert d.locate_file(n).read_bytes()==z.read(n),n
"""
            result = subprocess.run(
                [
                    worker_python,
                    "-I",
                    "-c",
                    script,
                    str(Path(directory) / row["filename"]),
                    row["version"],
                ],
                capture_output=True,
                timeout=10,
            )
            if result.returncode:
                raise ValueError("installed worker differs from selected wheel")
        else:
            owner = importlib.metadata.distribution(row["distribution"])
            if owner.version != row["version"]:
                raise ValueError("installed SDK version mismatch")
            with ZipFile(Path(directory) / row["filename"]) as archive:
                for name in archive.namelist():
                    if name.endswith(".py") and owner.locate_file(
                        name
                    ).read_bytes() != archive.read(name):
                        raise ValueError("installed SDK differs from selected wheel")
    from prosaic_runtime import ProsaicRuntime

    if "custom_tool_errors_v1" not in ProsaicRuntime.capabilities:
        raise ValueError("qualified Runtime capability missing")
    return [
        {key: row[key] for key in ("distribution", "version", "sha256")}
        for row in selected["artifacts"]
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--worker-python")
    parser.add_argument("--postgres-version", type=int, choices=(16, 18), default=16)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.enable:
        print(json.dumps({"enabled": False, "qualified": False, "reason": "disabled"}))
        return 0
    if not all((args.manifest, args.artifacts, args.worker_python, args.output)):
        parser.error(
            "enable requires explicit manifest, artifacts, worker-python and output"
        )
    artifacts = verify_installed(args.manifest, args.artifacts, args.worker_python)
    from .memory_fixture import OwnedPostgres

    result = {
        "enabled": True,
        "qualified": False,
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "artifacts": artifacts,
        "synthetic_only": True,
        "private_state_exported": False,
    }
    fixture = OwnedPostgres(args.postgres_version)
    try:
        with (
            fixture,
            tempfile.TemporaryDirectory(
                prefix="lab-memory-qualification-"
            ) as directory,
        ):
            settings = Path(directory) / "fixture.json"
            settings.write_text(
                json.dumps({"dsn": fixture.dsn, "worker_python": args.worker_python})
            )
            settings.chmod(0o600)
            junit = Path(directory) / "result.xml"
            run = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-m",
                    "pytest",
                    "tests/acceptance/test_memory_workflow.py",
                    "-o",
                    "pythonpath=",
                    "-q",
                    "--junitxml",
                    str(junit),
                ],
                env={**os.environ, "LAB_MEMORY_FIXTURE": str(settings)},
                capture_output=True,
                text=True,
                timeout=180,
            )
            # Test diagnostics stay local. Export counts and closed status only.
            if junit.exists():
                from xml.etree import ElementTree

                suites = ElementTree.parse(junit).getroot()
                result["tests"] = sum(
                    int(s.get("tests", "0")) for s in suites.iter("testsuite")
                )
                result["failures"] = sum(
                    int(s.get("failures", "0")) + int(s.get("errors", "0"))
                    for s in suites.iter("testsuite")
                )
                result["skipped"] = sum(
                    int(s.get("skipped", "0")) for s in suites.iter("testsuite")
                )
            if run.returncode:
                result["failed_tests"] = (
                    [
                        case.get("name")
                        for case in suites.iter("testcase")
                        if case.find("failure") is not None
                        or case.find("error") is not None
                    ]
                    if junit.exists()
                    else []
                )
                sys.stderr.write(
                    "memory acceptance failed; only sanitized case identities are exported\n"
                )
            result["qualified"] = (
                run.returncode == 0
                and result.get("tests", 0) >= 6
                and result.get("skipped") == 0
            )
    finally:
        result["postgres"] = fixture.manifest
        result["qualified"] = (
            result["qualified"] and fixture.manifest["cleanup_verified"]
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
