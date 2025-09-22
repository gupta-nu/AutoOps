"""
Simplified main entry point for AutoOps application
"""

import asyncio
import signal
import sys
import logging
import os
from pathlib import Path

# Simple settings without complex dependencies
class SimpleSettings:
    def __init__(self):
        self.dashboard_host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
        self.dashboard_port = int(os.getenv("DASHBOARD_PORT", "8080"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

settings = SimpleSettings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / "config" / ".env"
    if env_file.exists():
        try:
            # Try to use python-dotenv if available
            from dotenv import load_dotenv
            load_dotenv(str(env_file))
            logger.info("Loaded environment from .env file")
        except ImportError:
            # Manual parsing if dotenv not available
            logger.info("Loading environment manually (dotenv not available)")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())


class AutoOpsApplication:
    """Simplified AutoOps application class"""
    
    def __init__(self):
        self.is_running = False
    
    async def start(self):
        """Start the AutoOps application"""
        logger.info("Starting AutoOps application...")
        self.is_running = True
        logger.info("AutoOps application started successfully")
    
    async def stop(self):
        """Stop the AutoOps application"""
        logger.info("Stopping AutoOps application...")
        self.is_running = False
        logger.info("AutoOps application stopped successfully")
    
    async def health_check(self):
        """Check application health"""
        return {
            "status": "healthy" if self.is_running else "unhealthy",
            "version": "1.0.0"
        }


# Global application instance
autoops_app = AutoOpsApplication()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoOps Multi-Agent Kubernetes Orchestrator")
    parser.add_argument("command", choices=["serve", "health", "version"], help="Command to run")
    parser.add_argument("--host", default=settings.dashboard_host, help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=settings.dashboard_port, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_env_file()
    
    if args.command == "serve":
        serve_command(args.host, args.port, args.reload)
    elif args.command == "health":
        asyncio.run(health())
    elif args.command == "version":
        print("AutoOps v1.0.0")


def serve_command(host: str, port: int, reload: bool):
    """Start the web server"""
    logger.info(f"Starting AutoOps server on {host}:{port}")
    
    try:
        import uvicorn
        from src.dashboard.app import app
        
        # Configure logging for uvicorn
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_config=log_config
        )
    except ImportError:
        logger.error("uvicorn not available. Trying alternative method...")
        try:
            import subprocess
            import sys
            # Try to run uvicorn via subprocess
            cmd = [sys.executable, "-m", "uvicorn", "src.dashboard.app:app", "--host", host, "--port", str(port)]
            if reload:
                cmd.append("--reload")
            subprocess.run(cmd)
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            logger.error("Please install uvicorn:")
            logger.error("  pip install uvicorn[standard] --user")
            logger.error("  or")
            logger.error("  python3 -m pip install uvicorn[standard] --user")
            return False
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return False
    
    return True


async def health():
    """Check application health"""
    await autoops_app.start()
    try:
        health_status = await autoops_app.health_check()
        print(f"Status: {health_status['status']}")
        print(f"Version: {health_status['version']}")
    finally:
        await autoops_app.stop()


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(autoops_app.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    # Setup signal handlers
    setup_signal_handlers()
    
    # Run main
    main()
