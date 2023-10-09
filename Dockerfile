FROM mambaorg/micromamba:latest

WORKDIR /app
COPY . /app/
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1
COPY . /app/
RUN poetry install
ENTRYPOINT [ "/usr/local/bin/_entrypoint.sh", "poetry", "run", "gunicorn", "-w", "4", "--bind", "0.0.0.0:${PORT}", "src.server:app" ]
