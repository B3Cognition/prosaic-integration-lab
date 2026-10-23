"""Offline candidate image overlay on an explicit cached immutable lab base."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]


def main():
    from lab_runner.memory import memory_artifacts
    from lab_runner.stack import command

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-image", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--lab-wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch("sha256:[0-9a-f]{64}", args.base_image):
        parser.error("immutable cached base ID required")
    base = json.loads(command("docker", "image", "inspect", args.base_image))[0]
    if base["Id"] != args.base_image:
        raise ValueError("base identity changed")
    selected = memory_artifacts(args.manifest, args.artifacts)
    owner = uuid.uuid4().hex
    base_tag = "prosaic-memory-base:" + owner
    tag = "prosaic-integration-lab-memory:" + owner
    command("docker", "image", "tag", args.base_image, base_tag)
    try:
        with tempfile.TemporaryDirectory(prefix="memory-consumer-build-") as directory:
            context = Path(directory)
            wheels = context / "wheels"
            wheels.mkdir()
            for row in selected["artifacts"]:
                if row["distribution"] != "cognitive-castle":
                    shutil.copyfile(
                        args.artifacts / row["filename"], wheels / row["filename"]
                    )
            shutil.copyfile(args.lab_wheel, wheels / args.lab_wheel.name)
            shutil.copyfile(
                ROOT / "containers/Memory.Dockerfile", context / "Dockerfile"
            )
            shutil.copyfile(
                ROOT / "scripts/memory_smoke.py", context / "memory_smoke.py"
            )
            # An owned unique tag names the verified local base; no registry lookup.
            import subprocess

            build = subprocess.run(
                [
                    "docker",
                    "build",
                    "--network",
                    "none",
                    "--build-arg",
                    "MEMORY_BASE=" + base_tag,
                    "--label",
                    "io.prosaic.lab.owner=" + owner,
                    "--tag",
                    tag,
                    "--iidfile",
                    str(context / "image.id"),
                    str(context),
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if build.returncode:
                raise RuntimeError(
                    "memory consumer build failed: " + build.stderr[-3000:]
                )
            image = (context / "image.id").read_text().strip()
            command(
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--label",
                "io.prosaic.lab.owner=" + owner,
                image,
                "python",
                "-I",
                "/srv/memory_smoke.py",
            )
    finally:
        command("docker", "image", "rm", base_tag)
    result = {
        "base_image_id": args.base_image,
        "image_id": image,
        "tag": tag,
        "architecture": base["Architecture"],
        "candidate_only": True,
        "offline_build": True,
        "default_disabled_smoke": True,
        "lab_wheel_sha256": hashlib.sha256(args.lab_wheel.read_bytes()).hexdigest(),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
