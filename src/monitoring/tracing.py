"""
OpenTelemetry tracing configuration for AutoOps
"""

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config.settings import settings


def setup_tracing():
    """Initialize OpenTelemetry tracing"""
    
    # Create resource
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": "1.0.0",
    })
    
    # Set tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Configure exporters
    if settings.otel_exporter_otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )
    
    if settings.otel_exporter_jaeger_endpoint:
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
    
    # Auto-instrument libraries
    RequestsInstrumentor().instrument()
    LoggingInstrumentor().instrument()
    
    return tracer_provider


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance"""
    return trace.get_tracer(name)


def instrument_fastapi(app):
    """Instrument FastAPI application"""
    FastAPIInstrumentor.instrument_app(app)


# Initialize tracing on module import
_tracer_provider: Optional[TracerProvider] = None

def initialize_tracing():
    """Initialize tracing if not already done"""
    global _tracer_provider
    if _tracer_provider is None:
        _tracer_provider = setup_tracing()
    return _tracer_provider
