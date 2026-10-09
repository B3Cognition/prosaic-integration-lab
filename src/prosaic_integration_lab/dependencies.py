"""Release artifact verification."""
import hashlib
import json
from pathlib import Path


def verify_dependencies(manifest_path: Path, artifact_dir: Path) -> None:
    data = json.loads(Path(manifest_path).read_text())
    for artifact in data['artifacts']:
        filename = artifact['filename']
        if not filename or Path(filename).name != filename or '\\' in filename:
            raise ValueError('invalid artifact filename')
        path = Path(artifact_dir) / filename
        if not path.is_file():
            raise ValueError(f'missing artifact: {filename}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != artifact['sha256']:
            raise ValueError(f'artifact checksum mismatch: {filename}')
