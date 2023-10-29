FROM mambaorg/micromamba:latest

ARG PORT
ENV PORT=$PORT

WORKDIR /app
COPY . /app/
# COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

# Determine the lock file based on the operating system and architecture
ARG TARGET_PLATFORM="linux-64"
RUN if [ "$TARGET_PLATFORM" = "linux-64" ]; then \
        COPY --chown=$MAMBA_USER:$MAMBA_USER conda-linux-64.lock /tmp/conda.lock; \
    elif [ "$TARGET_PLATFORM" = "linux-aarch64" ]; then \
        COPY --chown=$MAMBA_USER:$MAMBA_USER conda-linux-aarch64.lock /tmp/conda.lock; \
    elif [ "$TARGET_PLATFORM" = "osx-arm64" ]; then \
        COPY --chown=$MAMBA_USER:$MAMBA_USER conda-osx-arm64.lock /tmp/conda.lock; \
    fi

RUN micromamba install -y -n base -f /tmp/conda.lock && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
COPY . /app/
RUN poetry install
ENTRYPOINT /usr/local/bin/_entrypoint.sh poetry run uvicorn src.server:app --proxy-headers --host 0.0.0.0 --port $PORT
