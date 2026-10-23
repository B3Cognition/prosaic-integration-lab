ARG MEMORY_BASE
FROM ${MEMORY_BASE}
USER 0:0
COPY wheels/ /tmp/memory-wheels/
RUN python -m pip install --no-index --no-deps --force-reinstall /tmp/memory-wheels/*.whl && rm -rf /tmp/memory-wheels
COPY memory_smoke.py /srv/memory_smoke.py
ENV PYTHONPATH=""
USER 10001:10001
RUN python -I /srv/memory_smoke.py
CMD ["python", "-I", "-m", "lab_runner.memory"]
