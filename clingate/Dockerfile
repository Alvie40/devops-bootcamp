# One image, four entrypoints: docker build --build-arg APP=ingest_api|mllp_listener|clingate_worker|hl7_exporter
# TODO(P3): pin both base images by digest; sign and attest in CI.
FROM python:3.12-slim AS build
RUN pip install --no-cache-dir uv==0.12.9
WORKDIR /src
COPY pyproject.toml ./
COPY apps apps
COPY sim sim
RUN uv venv /opt/venv && uv pip install --python /opt/venv/bin/python .

FROM python:3.12-slim
RUN useradd --system --uid 10001 --no-create-home app
COPY --from=build /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ARG APP=ingest_api
ENV APP=${APP}
USER 10001
ENTRYPOINT ["sh", "-c", "exec python -m ${APP}"]
