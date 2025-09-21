"""
Configuration management for AutoOps
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    
    # Kubernetes Configuration
    kubeconfig_path: Optional[str] = Field(None, env="KUBECONFIG_PATH")
    kubernetes_namespace: str = Field("default", env="KUBERNETES_NAMESPACE")
    
    # OpenTelemetry Configuration
    otel_service_name: str = Field("autoops", env="OTEL_SERVICE_NAME")
    otel_exporter_otlp_endpoint: str = Field(
        "http://localhost:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_exporter_jaeger_endpoint: str = Field(
        "http://localhost:14268/api/traces", env="OTEL_EXPORTER_JAEGER_ENDPOINT"
    )
    otel_resource_attributes: str = Field(
        "service.name=autoops,service.version=1.0.0", env="OTEL_RESOURCE_ATTRIBUTES"
    )
    
    # Dashboard Configuration
    dashboard_host: str = Field("0.0.0.0", env="DASHBOARD_HOST")
    dashboard_port: int = Field(8080, env="DASHBOARD_PORT")
    dashboard_debug: bool = Field(False, env="DASHBOARD_DEBUG")
    
    # Redis Configuration
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = Field(0, env="REDIS_DB")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./autoops.db", env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Task Configuration
    max_concurrent_tasks: int = Field(10, env="MAX_CONCURRENT_TASKS")
    task_timeout_seconds: int = Field(300, env="TASK_TIMEOUT_SECONDS")
    retry_max_attempts: int = Field(3, env="RETRY_MAX_ATTEMPTS")
    retry_delay_seconds: float = Field(1.0, env="RETRY_DELAY_SECONDS")
    
    # Development Settings
    dev_mode: bool = Field(False, env="DEV_MODE")
    reload_on_change: bool = Field(False, env="RELOAD_ON_CHANGE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        return Settings(_env_file=str(env_file))
    return Settings()


# Global settings instance
settings = get_settings()
