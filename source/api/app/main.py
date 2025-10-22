"""Main app module that assembles all downstream modules into one.


ATTENTION: DO NOT IMPORT ANYTHING FROM APP CONTEXT WITHIN THE MAIN
SCOPE OF THIS MODULE. DOING SO IS LIKELY TO ADD RACES.
"""

import logging
import os

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from psycopg2.errors import OperationalError
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def main() -> FastAPI:
    """Generate a new application instance.

    Args:
        None

    Returns:
        FastAPI application context, built with all middleware and
        routes.
    """
    from app import APP_NAME
    from app.common import exceptions as E
    from app.common.logging import build_logger
    from app.exception_handlers import (
        generic_exception_handler,
        integrity_error_handler,
        method_not_allowed_handler,
        rbac_error_handler,
        server_unavailable_handler,
        validation_exception_handler,
    )
    from app.users.expections import UserNotAuthorized
    from app.users.router import user_router

    app = FastAPI(
        default_response_class=JSONResponse,
        openapi_url="/api/openapi.json",
        swagger_ui_parameters={"docExpansion": "none"},
    )

    # Custom exception handlers
    app.add_exception_handler(E.RaisableHTTPException, generic_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(OperationalError, server_unavailable_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        status.HTTP_405_METHOD_NOT_ALLOWED, method_not_allowed_handler  # type: ignore[arg-type]
    )
    app.add_exception_handler(UserNotAuthorized, rbac_error_handler)  # type: ignore[arg-type]

    if os.environ.get("ENVIRONMENT") != "testing":
        # trace is a singleton.
        tracer = TracerProvider()
        trace.set_tracer_provider(tracer)

        # Both locally and in environments we use a sidecar container.
        tracer.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=os.environ.get(
                        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces"
                    )
                )
            )
        )

        StarletteInstrumentor.instrument_app(app)
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(enable_commenter=True, commenter_options={})
        Psycopg2Instrumentor().instrument(enable_commenter=True, commenter_options={})
        HTTPXClientInstrumentor().instrument()

        configuration = {
            "system.memory.usage": ["used", "free", "cached"],
            "system.cpu.time": ["idle", "user", "system", "irq"],
            "system.network.io": ["transmit", "receiver"],
            "process.runtime.memory": ["rss", "vms"],
            "process.runtime.cpu.time": ["user", "system"],
            "process.runtime.context_switches": ["involuntary", "voluntary"],
        }
        SystemMetricsInstrumentor(config=configuration).instrument()  # type: ignore[arg-type]

    build_logger(level=os.environ.get("LOG_LEVEL", "INFO"))
    # settings.tracing_implementation = "opentelemetry"

    instrumentator = Instrumentator()
    instrumentator.instrument(app, metric_namespace=APP_NAME)
    instrumentator.expose(app, include_in_schema=False, should_gzip=True)

    app.include_router(user_router)

    openapi_schema = get_openapi(
        title=APP_NAME,
        description="Ecommerce app",
        version=os.environ.get("RELEASE", "unknown"),
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema

    return app
