FROM python:3.13

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG RELEASE=dev

WORKDIR /app
EXPOSE 8080

# Copy files over
RUN groupadd -g 1000 app \
&& useradd -m -u 1000 -g app -s /bin/bash app \
&& chown -R app:app /app \
&& chmod -R u=rwX,go=rX /usr/local/bin

COPY --chown=app:app ./app/ /app/app/

RUN pip install --no-cache-dir poetry==2.1.2
COPY pyproject.toml /app/

# We're already installing to a container (docker), we don't need
# to use another container (virtualenv) so install to system

RUN poetry config virtualenvs.create false \
&& poetry install --no-interaction --without dev \
&& rm -rf /root/.cache/pypoetry

ENV PYTHONPATH=/app
ENV RELEASE=$RELEASE

RUN pip install opentelemetry-instrumentation==0.49b2 opentelemetry-distro opentelemetry-exporter-otlp
RUN opentelemetry-bootstrap -a install
# OTEL default variables
ENV OTEL_TRACES_EXPORTER=console,otlp
ENV OTEL_METRICS_EXPORTER=console
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces

USER app

CMD ["opentelemetry-instrument", "uvicorn", "app.main:main", "--factory", "--reload", "--host=0.0.0.0", "--port=8000", "--workers=1"]
