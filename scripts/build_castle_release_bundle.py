"""Build exact-source, artifact-only Castle releases and verify sdist round trips."""

import argparse
from copy import deepcopy
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wheel_payload(path):
    with ZipFile(path) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest()
                for name in archive.namelist() if not name.endswith("/RECORD")}


def run(*command, cwd, env):
    subprocess.run(command, cwd=cwd, env=env, check=True, timeout=300)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--castle-source", type=Path, required=True)
    parser.add_argument("--source-spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.castle_source.resolve()
    spec = json.loads(args.source_spec.read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if (commit != spec["source_commit"] or len(commit) != 40
            or subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=source)):
        raise ValueError("clean exact Castle source required")
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("clean committed Lab source required")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    epoch = subprocess.check_output(["git", "show", "-s", "--format=%ct", commit], cwd=source, text=True).strip()
    env = {**os.environ, "SOURCE_DATE_EPOCH": epoch}
    package_rows = []
    roundtrips = []
    projects = [(source, "cognitive-castle", spec["worker_version"]),
                (source / "adapters/prosaic", "b3-prosaic-memory-castle", spec["adapter_version"])]
    for directory, distribution, version in projects:
        project = tomllib.loads((directory / "pyproject.toml").read_text())["project"]
        if project["name"] != distribution or project["version"] != version:
            raise ValueError("release package identity/version mismatch")
        run(sys.executable, "-m", "build", "--no-isolation", "--outdir", str(output), cwd=directory, env=env)
        stem = distribution.replace("-", "_") + "-" + version
        wheel = output / (stem + "-py3-none-any.whl")
        sdist = output / (stem + ".tar.gz")
        with tempfile.TemporaryDirectory(prefix="castle-sdist-roundtrip-") as temporary:
            unpacked = Path(temporary)
            with tarfile.open(sdist) as archive:
                archive.extractall(unpacked, filter="data")
            extracted = unpacked / stem
            run(sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(unpacked / "wheel"),
                cwd=extracted, env=env)
            if wheel_payload(wheel) != wheel_payload(unpacked / "wheel" / wheel.name):
                raise ValueError("sdist rebuilt wheel payload differs")
        roundtrips.append({"distribution": distribution, "version": version,
                           "wheel": wheel.name, "wheel_sha256": digest(wheel),
                           "sdist": sdist.name, "sdist_sha256": digest(sdist),
                           "rebuilt_sdist_payloads_match": True})
        package_rows.append({"distribution": distribution, "version": version,
                             "filename": wheel.name, "sha256": digest(wheel),
                             "source_commit": commit, "candidate": True,
                             **({"environment": "worker-only"} if distribution == "cognitive-castle" else {})})
    run(sys.executable, "-m", "twine", "check", *[str(output / row[key]) for row in roundtrips for key in ("wheel", "sdist")],
        cwd=ROOT, env=env)
    from scripts.prepare_dependencies import prepare
    cache = prepare(ROOT / "dependencies/releases.json", ROOT / ".cache/wheels")
    public = json.loads((ROOT / "dependencies/releases.json").read_text())
    for row in public["artifacts"]:
        shutil.copyfile(cache / row["filename"], output / row["filename"])
    manifest = deepcopy(public)
    manifest["qualification"] = "artifact-only Castle release preparation; memory remains disabled by default"
    # Keep the historic public family order, followed by the adapter and worker.
    manifest["artifacts"].extend(reversed(package_rows))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    run(sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(output), cwd=ROOT, env=env)
    lab_version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    lab_wheel = output / ("prosaic_integration_lab-" + lab_version + "-py3-none-any.whl")
    lab_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    build = {"built": True, "published": False, "castle_source_commit": commit,
             "lab_source_commit": lab_commit, "source_date_epoch": epoch,
             "packages": roundtrips, "lab_wheel": {"filename": lab_wheel.name, "sha256": digest(lab_wheel)},
             "manifest_sha256": digest(output / "manifest.json"),
             "public_sdk_manifest_sha256": digest(ROOT / "dependencies/releases.json"),
             "build_tools": {name: metadata.version(name) for name in ("build", "setuptools", "hatchling", "twine")}}
    (output / "build.json").write_text(json.dumps(build, indent=2) + "\n")
    # The smoke and public SDK checks run in clean Runtime-only environments.
    shutil.copyfile(source / "adapters/prosaic/scripts/wheel_smoke.py", output / "adapter_wheel_smoke.py")
    print(json.dumps({"built": True, "castle_source_commit": commit, "published": False}))


if __name__ == "__main__":
    main()
