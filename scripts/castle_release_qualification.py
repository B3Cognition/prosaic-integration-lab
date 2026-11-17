"""Strict native enabled-provider receipt gate; exports no private run state."""

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import subprocess
from zipfile import ZipFile


def native_architecture(expected, *, system=None, machine=None):
    system = platform.system() if system is None else system
    machine = platform.machine() if machine is None else machine
    actual = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(machine)
    if system != "Linux" or expected not in {"amd64", "arm64"} or actual != expected:
        raise ValueError("native Linux architecture mismatch")
    return actual


def validate_receipt(value, *, architecture, postgres_major, manifest_sha256, expected_artifacts):
    if (value.get("enabled") is not True or value.get("qualified") is not True
            or value.get("synthetic_only") is not True
            or value.get("private_state_exported") is not False
            or value.get("manifest_sha256") != manifest_sha256
            or value.get("artifacts") != expected_artifacts):
        raise ValueError("unqualified or mismatched memory evidence")
    for key, expected in (("tests", 6), ("failures", 0), ("skipped", 0)):
        if type(value.get(key)) is not int or value[key] != expected:
            raise ValueError("exact six-case, zero-failure, zero-skip memory lane required")
    postgres = value.get("postgres", {})
    if (postgres.get("architecture") != architecture
            or postgres.get("cleanup_verified") is not True
            or postgres.get("separate_runtime_role") is not True
            or str(postgres.get("server_version", "")).split(".")[0] != str(postgres_major)):
        raise ValueError("PostgreSQL version, architecture, role or cleanup mismatch")


def installed_lab(wheel):
    owner = metadata.distribution("prosaic-integration-lab")
    with ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.endswith(".py") and owner.locate_file(name).read_bytes() != archive.read(name):
                raise ValueError("installed Lab differs from qualified wheel")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--architecture", choices=("amd64", "arm64"), required=True)
    parser.add_argument("--postgres-version", type=int, choices=(16, 18), required=True)
    parser.add_argument("--worker-python", required=True)
    parser.add_argument("--worker-report", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    native_architecture(args.architecture)
    manifest_path = args.bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    build = json.loads((args.bundle / "build.json").read_text())
    root = Path(__file__).resolve().parents[1]
    spec = json.loads((root / "dependencies/castle-release-source.json").read_text())
    lab_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    public_path = root / "dependencies/releases.json"
    if (build.get("built") is not True or build.get("published") is not False
            or build.get("castle_source_commit") != spec["source_commit"]
            or build.get("lab_source_commit") != lab_commit
            or build.get("manifest_sha256") != hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            or build.get("public_sdk_manifest_sha256") != hashlib.sha256(public_path.read_bytes()).hexdigest()
            or manifest["artifacts"][:5] != json.loads(public_path.read_text())["artifacts"]):
        raise ValueError("bundle source or public SDK lineage mismatch")
    expected = [{key: row[key] for key in ("distribution", "version", "sha256")}
                for row in manifest["artifacts"]]
    value = json.loads(args.receipt.read_text())
    validate_receipt(value, architecture=args.architecture, postgres_major=args.postgres_version,
                     manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                     expected_artifacts=expected)
    lab_wheel = args.bundle / build["lab_wheel"]["filename"]
    if hashlib.sha256(lab_wheel.read_bytes()).hexdigest() != build["lab_wheel"]["sha256"]:
        raise ValueError("Lab wheel changed")
    installed_lab(lab_wheel)
    worker = json.loads(subprocess.check_output([
        args.worker_python, "-I", "-c",
        "import json,platform; print(json.dumps({'system':platform.system(), 'machine':platform.machine(), 'python':platform.python_version()}))",
    ], text=True, timeout=10))
    native_architecture(args.architecture, system=worker["system"], machine=worker["machine"])
    daemon = json.loads(subprocess.check_output(
        ["docker", "info", "--format", "{{json .}}"], text=True, timeout=15))
    native_architecture(args.architecture, system="Linux" if daemon["OSType"] == "linux" else "",
                        machine=daemon["Architecture"])
    image = json.loads(subprocess.check_output(
        ["docker", "image", "inspect", value["postgres"]["image_id"]], text=True, timeout=15))[0]
    if image["Os"] != "linux" or image["Architecture"] != args.architecture:
        raise ValueError("PostgreSQL image architecture mismatch")
    image_pins = json.loads((Path(__file__).resolve().parents[1] / "dependencies/images.json").read_text())
    digest = image_pins["postgres" + str(args.postgres_version)].split("@", 1)[1]
    if not any(reference.endswith("@" + digest) for reference in image.get("RepoDigests", [])):
        raise ValueError("PostgreSQL image does not match qualified image pin")
    dependencies = {}
    for path in args.worker_report:
        for item in json.loads(path.read_text())["install"]:
            info = item["metadata"]
            hashes = item.get("download_info", {}).get("archive_info", {}).get("hashes", {})
            dependencies[info["name"]] = {"distribution": info["name"], "version": info["version"],
                                         "sha256": hashes.get("sha256")}
    result = {"qualified": True, "synthetic_only": True, "native_linux": True,
              "architecture": args.architecture, "postgres_major": args.postgres_version,
              "host_python": platform.python_version(), "worker": worker,
              "castle_source_commit": build["castle_source_commit"],
              "lab_source_commit": build["lab_source_commit"],
              "bundle_build_sha256": hashlib.sha256((args.bundle / "build.json").read_bytes()).hexdigest(),
              "memory_profile": "memory-fts-v1", "recency_boost": False,
              "default_memory_enabled": False, "installed_lab_payloads_verified": True,
              "memory": value, "worker_dependencies": sorted(dependencies.values(), key=lambda x:x["distribution"]),
              "private_state_exported": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"qualified": True, "architecture": args.architecture,
                      "postgres_major": args.postgres_version, "tests": value["tests"]}))


if __name__ == "__main__":
    main()
