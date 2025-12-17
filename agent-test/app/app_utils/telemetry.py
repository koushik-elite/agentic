# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""OpenTelemetry setup for LangGraph agents with GenAI instrumentation."""

import logging
import os

from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace.export import SpanExporter
from traceloop.sdk import Instruments, Traceloop

logger = logging.getLogger(__name__)

TELEMETRY_ENDPOINT = "https://telemetry.googleapis.com/v1/traces"


def setup_telemetry() -> str | None:
    """Configure OpenTelemetry for LangGraph agents with GenAI instrumentation."""
    bucket = os.environ.get("LOGS_BUCKET_NAME")
    capture_content = os.environ.get(
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false"
    )

    # Check if prompt/response logging is enabled
    if bucket and capture_content != "false":
        logger.info("Prompt-response logging enabled - mode: %s", capture_content)
        span_exporter = _setup_genai_telemetry(bucket)
    else:
        logger.info(
            "Prompt-response logging disabled (set LOGS_BUCKET_NAME and "
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT to enable)"
        )
        span_exporter = CloudTraceSpanExporter()

    # Set up LangGraph instrumentation
    _setup_langgraph_instrumentation(span_exporter)

    return bucket


def _setup_langgraph_instrumentation(exporter: SpanExporter) -> None:
    """Set up LangGraph instrumentation."""
    try:
        Traceloop.init(
            app_name="agent-test",
            disable_batch=False,
            telemetry_enabled=False,
            exporter=exporter,
            instruments={Instruments.LANGCHAIN},
        )
    except Exception as e:
        logger.error("Failed to initialize LangGraph instrumentation: %s", str(e))


def _setup_genai_telemetry(bucket: str) -> SpanExporter:
    """Set up full telemetry with GenAI instrumentation and Cloud Logging."""
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    from opentelemetry import _events, _logs, trace
    from opentelemetry.exporter.cloud_logging import CloudLoggingExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._events import EventLoggerProvider
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import OTELResourceDetector, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Configure prompt/response logging env vars
    os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_UPLOAD_FORMAT", "jsonl")
    os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK", "upload")
    os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental")
    commit_sha = os.environ.get("COMMIT_SHA", "dev")
    os.environ.setdefault(
        "OTEL_RESOURCE_ATTRIBUTES",
        f"service.namespace=agent-test,service.version={commit_sha}",
    )
    path = os.environ.get("GENAI_TELEMETRY_PATH", "completions")
    os.environ.setdefault(
        "OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH",
        f"gs://{bucket}/{path}",
    )

    # Get credentials and project
    credentials, project_id = google.auth.default()
    session = AuthorizedSession(credentials=credentials)

    # Build resource with GCP attributes
    resource = Resource(attributes={"gcp.project_id": project_id})
    resource = resource.merge(OTELResourceDetector().detect())
    try:
        from opentelemetry.resourcedetector.gcp_resource_detector import (
            GoogleCloudResourceDetector,
        )

        resource = resource.merge(
            GoogleCloudResourceDetector(raise_on_error=False).detect()
        )
    except ImportError:
        logger.debug(
            "opentelemetry-resourcedetector-gcp not installed - "
            "GCE/GKE/CloudRun resource attributes will be missing"
        )

    # Create OTLP exporter for Cloud Trace
    span_exporter = OTLPSpanExporter(session=session, endpoint=TELEMETRY_ENDPOINT)

    # Set up trace provider
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Set up logging provider with Cloud Logging exporter
    log_name = os.environ.get("GOOGLE_CLOUD_DEFAULT_LOG_NAME", "langgraph-otel")
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            CloudLoggingExporter(project_id=project_id, default_log_name=log_name)
        )
    )
    _logs.set_logger_provider(logger_provider)
    _events.set_event_logger_provider(EventLoggerProvider(logger_provider))

    # Set up GenAI SDK instrumentation for prompt/response capture
    try:
        from opentelemetry.instrumentation.google_genai import (
            GoogleGenAiSdkInstrumentor,
        )

        GoogleGenAiSdkInstrumentor().instrument()
    except ImportError:
        logger.warning(
            "opentelemetry-instrumentation-google-genai not installed - "
            "GenAI telemetry disabled"
        )

    return span_exporter
