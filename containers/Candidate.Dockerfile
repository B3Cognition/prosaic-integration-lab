ARG BASE_IMAGE=prosaic-integration-lab:dev
FROM ${BASE_IMAGE}
USER 0
ARG CANDIDATE_MANIFEST_SHA256
COPY .cache/candidates/ /srv/candidates/
COPY dependencies/accounting-candidate.json /srv/lab/dependencies/accounting-candidate.json
RUN python -c "import hashlib,os; from pathlib import Path; assert hashlib.sha256(Path('/srv/lab/dependencies/accounting-candidate.json').read_bytes()).hexdigest() == os.environ['CANDIDATE_MANIFEST_SHA256']"
RUN PYTHONPATH=src python -c "from pathlib import Path; from prosaic_integration_lab.dependencies import verify_dependencies; verify_dependencies(Path('dependencies/accounting-candidate.json'),Path('/srv/candidates'))"
RUN python -m pip install --no-deps /srv/candidates/prosaic_runtime_postgres-0.1.1-py3-none-any.whl /srv/candidates/prosaic_harness_postgres-0.1.1-py3-none-any.whl
RUN python scripts/audit_install.py dependencies/accounting-candidate.json /srv/candidates
USER 10001:10001
LABEL io.prosaic.lab.dependency-mode="candidate"
LABEL io.prosaic.lab.candidate-manifest=${CANDIDATE_MANIFEST_SHA256}
