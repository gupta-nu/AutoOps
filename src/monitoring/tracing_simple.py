"""
Simplified tracing module for AutoOps.
Provides basic tracing capabilities with fallback options.
"""
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Simple tracer implementation that can work without external dependencies
class SimpleTracer:
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"tracer.{name}")
    
    def start_span(self, name: str, **kwargs):
        return SimpleSpan(name, self.logger, **kwargs)
    
    def start_as_current_span(self, name: str, **kwargs):
        return SimpleSpan(name, self.logger, **kwargs)

class SimpleSpan:
    def __init__(self, name: str, logger: logging.Logger, **kwargs):
        self.name = name
        self.logger = logger
        self.attributes = kwargs
        
    def __enter__(self):
        self.logger.info(f"Starting span: {self.name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"Span {self.name} failed: {exc_val}")
        else:
            self.logger.info(f"Completed span: {self.name}")
    
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
        self.logger.debug(f"Span {self.name} attribute: {key}={value}")
    
    def set_status(self, status: str, description: str = ""):
        self.logger.info(f"Span {self.name} status: {status} - {description}")

def get_tracer(name: str) -> SimpleTracer:
    """Get a tracer instance with the given name."""
    return SimpleTracer(name)

def trace_function(span_name: Optional[str] = None):
    """Decorator to trace function calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            name = span_name or f"{func.__name__}"
            
            with tracer.start_span(name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status("OK")
                    return result
                except Exception as e:
                    span.set_status("ERROR", str(e))
                    raise
        return wrapper
    return decorator

def setup_tracing():
    """Setup tracing infrastructure."""
    logger.info("Tracing setup completed (simplified mode)")
    return True

def initialize_tracing():
    """Initialize tracing for the application."""
    logger.info("Initializing simplified tracing")
    return setup_tracing()

def instrument_fastapi(app):
    """Instrument FastAPI app (simplified mode - no-op)."""
    logger.info("FastAPI instrumentation completed (simplified mode)")
    return app
