FROM mambaorg/micromamba:latest

ARG PORT
ENV PORT=$PORT

WORKDIR /app
COPY . /app/
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1
COPY . /app/
RUN poetry install
ENTRYPOINT /usr/local/bin/_entrypoint.sh poetry run uvicorn app.main:app --proxy-headers --host 0.0.0.0 --port $PORT
