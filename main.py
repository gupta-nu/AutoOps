"""
Main entry point for AutoOps application
"""

import asyncio
import signal
import sys
import logging
from contextlib import asynccontextmanager

import click
import uvicorn
from dotenv import load_dotenv

from src.dashboard.app import app
from src.utils.task_manager import task_manager
from src.monitoring.tracing import initialize_tracing
from config.settings import settings


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoOpsApplication:
    """Main AutoOps application class"""
    
    def __init__(self):
        self.is_running = False
        self.tasks = []
    
    async def start(self):
        """Start the AutoOps application"""
        logger.info("Starting AutoOps application...")
        
        try:
            # Initialize tracing
            initialize_tracing()
            logger.info("OpenTelemetry tracing initialized")
            
            # Start task manager
            await task_manager.start()
            logger.info("Task manager started")
            
            self.is_running = True
            logger.info("AutoOps application started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start AutoOps application: {e}")
            raise
    
    async def stop(self):
        """Stop the AutoOps application"""
        logger.info("Stopping AutoOps application...")
        
        try:
            self.is_running = False
            
            # Stop task manager
            await task_manager.stop()
            logger.info("Task manager stopped")
            
            logger.info("AutoOps application stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping AutoOps application: {e}")
    
    async def health_check(self):
        """Check application health"""
        try:
            metrics = await task_manager.get_metrics()
            return {
                "status": "healthy" if self.is_running else "unhealthy",
                "task_manager": metrics,
                "version": "1.0.0"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "version": "1.0.0"
            }


# Global application instance
autoops_app = AutoOpsApplication()


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan manager"""
    # Startup
    await autoops_app.start()
    yield
    # Shutdown
    await autoops_app.stop()


# Update FastAPI app with lifespan
app.router.lifespan_context = lifespan


@click.group()
def cli():
    """AutoOps Multi-Agent Kubernetes Orchestrator"""
    pass


@cli.command()
@click.option('--host', default=settings.dashboard_host, help='Host to bind the server to')
@click.option('--port', default=settings.dashboard_port, help='Port to bind the server to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--workers', default=1, help='Number of worker processes')
def serve(host, port, reload, workers):
    """Start the AutoOps server"""
    logger.info(f"Starting AutoOps server on {host}:{port}")
    
    # Load environment variables
    load_dotenv()
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload or settings.dev_mode,
        workers=workers if not reload else 1,
        log_level=settings.log_level.lower()
    )


@cli.command()
@click.argument('request')
@click.option('--priority', default='normal', help='Task priority (low, normal, high, critical)')
@click.option('--timeout', type=int, help='Task timeout in seconds')
def submit(request, priority, timeout):
    """Submit a task via CLI"""
    async def _submit():
        from src.utils.task_manager import TaskPriority
        
        await autoops_app.start()
        
        try:
            task_id = await task_manager.submit_task(
                request=request,
                priority=TaskPriority(priority),
                timeout=timeout
            )
            
            click.echo(f"Task submitted: {task_id}")
            
            # Wait for completion
            while True:
                status = await task_manager.get_task_status(task_id)
                if status and status['status'] in ['completed', 'failed', 'cancelled']:
                    click.echo(f"Task {status['status']}: {task_id}")
                    if status['status'] == 'failed':
                        click.echo(f"Error: {status.get('error', 'Unknown error')}")
                    break
                await asyncio.sleep(1)
                
        finally:
            await autoops_app.stop()
    
    asyncio.run(_submit())


@cli.command()
@click.option('--limit', default=10, help='Number of tasks to show')
@click.option('--status', help='Filter by task status')
def list_tasks(limit, status):
    """List tasks"""
    async def _list():
        from src.agents.state import TaskStatus
        
        await autoops_app.start()
        
        try:
            task_status = TaskStatus(status) if status else None
            tasks = await task_manager.list_tasks(status=task_status, limit=limit)
            
            if not tasks:
                click.echo("No tasks found")
                return
            
            click.echo(f"{'ID':<8} {'Status':<12} {'Created':<20} {'Request'}")
            click.echo("-" * 80)
            
            for task in tasks:
                task_id = task['task_id'][:8]
                status = task['status']
                created = task['created_at'][:19]
                request = task['request'][:40] + '...' if len(task['request']) > 40 else task['request']
                
                click.echo(f"{task_id:<8} {status:<12} {created:<20} {request}")
                
        finally:
            await autoops_app.stop()
    
    asyncio.run(_list())


@cli.command()
@click.argument('task_id')
def cancel(task_id):
    """Cancel a task"""
    async def _cancel():
        await autoops_app.start()
        
        try:
            success = await task_manager.cancel_task(task_id)
            if success:
                click.echo(f"Task cancelled: {task_id}")
            else:
                click.echo(f"Task not found: {task_id}")
                
        finally:
            await autoops_app.stop()
    
    asyncio.run(_cancel())


@cli.command()
def health():
    """Check application health"""
    async def _health():
        await autoops_app.start()
        
        try:
            health_status = await autoops_app.health_check()
            click.echo(f"Status: {health_status['status']}")
            click.echo(f"Version: {health_status['version']}")
            
            if 'task_manager' in health_status:
                metrics = health_status['task_manager']
                click.echo(f"Total tasks: {metrics['total_tasks']}")
                click.echo(f"Active tasks: {metrics['active_tasks']}")
                click.echo(f"Queue size: {metrics['queue_size']}")
                
        finally:
            await autoops_app.stop()
    
    asyncio.run(_health())


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(autoops_app.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Run CLI
    cli()
