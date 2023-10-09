FROM mambaorg/micromamba:latest

WORKDIR /app
COPY . /app/
RUN micromamba install -y -n base -f conda-linux-64.lock
RUN poetry install
CMD ["python", "src/main.py"]