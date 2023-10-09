FROM mambaorg/micromamba:latest

WORKDIR /app
COPY . /app/
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1
COPY . /app/
RUN poetry install
CMD bash -c "uvicorn server:app --host 0.0.0.0 --port $PORT"