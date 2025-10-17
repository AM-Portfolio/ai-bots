from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
import logging

logger = logging.getLogger(__name__)


def setup_tracing(app, service_name: str = "ai-dev-agent"):
    resource = Resource(attributes={
        "service.name": service_name
    })
    
    provider = TracerProvider(resource=resource)
    
    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    trace.set_tracer_provider(provider)
    
    FastAPIInstrumentor.instrument_app(app)
    
    logger.info(f"Tracing initialized for {service_name}")
    
    return trace.get_tracer(__name__)


def get_tracer():
    return trace.get_tracer(__name__)
