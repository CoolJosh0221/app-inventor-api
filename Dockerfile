FROM mambaorg/micromamba:latest

ARG PORT
ENV PORT=$PORT

WORKDIR /app
COPY . /app/
# COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

# Determine the lock file based on the operating system and architecture
ARG CONDA_LOCK_NAME="conda-linux-64.lock"

COPY --chown=$MAMBA_USER:$MAMBA_USER . /app/
RUN micromamba install -y -n base -f ./${CONDA_LOCK_NAME} && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN poetry install
ENTRYPOINT /usr/local/bin/_entrypoint.sh poetry run uvicorn src.server:app --proxy-headers --host 0.0.0.0 --port $PORT
