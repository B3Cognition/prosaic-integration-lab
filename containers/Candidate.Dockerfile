ARG PYTHON_IMAGE=python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
FROM ${PYTHON_IMAGE}
WORKDIR /srv/lab
COPY dependencies/requirements.lock dependencies/requirements.lock
RUN python -m pip install --require-hashes -r dependencies/requirements.lock
ARG SDK_MANIFEST_SHA256
COPY .cache/wheels/${SDK_MANIFEST_SHA256}/ /srv/wheels/
COPY dependencies/releases.json dependencies/releases.json
COPY src/ src/
COPY scripts/ scripts/
COPY lab_runner/ lab_runner/
COPY assets/ assets/
RUN python scripts/install_dependencies.py --manifest dependencies/releases.json --wheel-dir /srv/wheels --expected-sha ${SDK_MANIFEST_SHA256}
RUN python scripts/audit_install.py --manifest dependencies/releases.json --wheel-dir /srv/wheels --expected-sha ${SDK_MANIFEST_SHA256}
ENV PYTHONPATH=/srv/lab/src:/srv/lab
ENV PYTHONDONTWRITEBYTECODE=1
RUN groupadd --gid 10001 lab && useradd --uid 10001 --gid 10001 --no-create-home lab
USER 10001:10001
CMD ["python", "-m", "prosaic_integration_lab", "--version"]
LABEL io.prosaic.lab.dependency-mode="candidate"
LABEL io.prosaic.lab.sdk-manifest=${SDK_MANIFEST_SHA256}
LABEL io.prosaic.lab.candidate-manifest=${SDK_MANIFEST_SHA256}
