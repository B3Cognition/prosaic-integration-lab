ARG PYTHON_IMAGE=python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
FROM ${PYTHON_IMAGE}
WORKDIR /srv/lab
COPY dependencies/requirements.lock dependencies/requirements.lock
RUN python -m pip install --require-hashes -r dependencies/requirements.lock
COPY .cache/wheels/ /srv/wheels/
COPY dependencies/releases.json dependencies/releases.json
ARG RELEASE_MANIFEST_SHA256=247a2b1b1d64b2f4ec318a6b6aec51c28b691fb41018044f8bac571c089d53c7
RUN python -c "import hashlib,os; from pathlib import Path; assert hashlib.sha256(Path('dependencies/releases.json').read_bytes()).hexdigest() == os.environ['RELEASE_MANIFEST_SHA256']"
LABEL io.prosaic.lab.release-manifest=${RELEASE_MANIFEST_SHA256}
LABEL io.prosaic.lab.dependency-mode="released"
COPY src/ src/
COPY scripts/ scripts/
COPY lab_runner/ lab_runner/
COPY assets/ assets/
RUN PYTHONPATH=src python -c "from pathlib import Path; from prosaic_integration_lab.dependencies import verify_dependencies; verify_dependencies(Path('dependencies/releases.json'), Path('/srv/wheels'))"
RUN python -m pip install --no-deps /srv/wheels/prosaic-*.whl /srv/wheels/prosaic_runtime-*.whl /srv/wheels/prosaic_harness-*.whl
RUN python -m pip install --no-deps /srv/wheels/prosaic_runtime_postgres-*.whl /srv/wheels/prosaic_harness_postgres-*.whl
RUN python scripts/audit_install.py dependencies/releases.json /srv/wheels
ENV PYTHONPATH=/srv/lab/src:/srv/lab
ENV PYTHONDONTWRITEBYTECODE=1
RUN groupadd --gid 10001 lab && useradd --uid 10001 --gid 10001 --no-create-home lab
USER 10001:10001
CMD ["python", "-m", "prosaic_integration_lab", "--version"]
