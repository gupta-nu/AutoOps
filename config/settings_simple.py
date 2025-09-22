"""
Simple configuration management for AutoOps
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Application settings using environment variables"""
    
    def __init__(self):
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Kubernetes Configuration
        self.kubeconfig_path = os.getenv("KUBECONFIG_PATH")
        self.kubernetes_namespace = os.getenv("KUBERNETES_NAMESPACE", "default")
        
        # OpenTelemetry Configuration
        self.otel_service_name = os.getenv("OTEL_SERVICE_NAME", "autoops")
        self.otel_exporter_otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )
        self.otel_exporter_jaeger_endpoint = os.getenv(
            "OTEL_EXPORTER_JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
        )
        self.otel_resource_attributes = os.getenv(
            "OTEL_RESOURCE_ATTRIBUTES", "service.name=autoops,service.version=1.0.0"
        )
        
        # Dashboard Configuration
        self.dashboard_host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
        self.dashboard_port = int(os.getenv("DASHBOARD_PORT", "8080"))
        self.dashboard_debug = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"
        
        # Redis Configuration
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        
        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./autoops.db")
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")
        
        # Security
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # Task Configuration
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
        self.task_timeout_seconds = int(os.getenv("TASK_TIMEOUT_SECONDS", "300"))
        self.retry_max_attempts = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
        self.retry_delay_seconds = float(os.getenv("RETRY_DELAY_SECONDS", "1.0"))
        
        # Development Settings
        self.dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        self.reload_on_change = os.getenv("RELOAD_ON_CHANGE", "false").lower() == "true"


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


# Load environment file if it exists
def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(str(env_file))
        except ImportError:
            # dotenv not available, manually parse
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())


# Load environment file
load_env_file()

# Global settings instance
settings = get_settings()
