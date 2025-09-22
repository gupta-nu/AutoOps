"""
Simplified Task Manager for AutoOps
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Dict, Optional, Callable, List
from uuid import uuid4, UUID

from ..monitoring.tracing_simple import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """Simple task representation"""
    
    def __init__(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        request: Optional[str] = None
    ):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.timeout = timeout
        self.request = request or "Custom function execution"
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None


class SimpleTaskManager:
    """Simplified task manager for AutoOps"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._started = False
        self.start_time = time.time()
    
    async def start(self):
        """Start the task manager"""
        self._started = True
        logger.info("Task manager started")
    
    async def stop(self):
        """Stop the task manager"""
        # Cancel all running tasks
        for task_id, asyncio_task in self.running_tasks.items():
            asyncio_task.cancel()
        
        self.running_tasks.clear()
        self._started = False
        logger.info("Task manager stopped")
        
    async def submit_task(
        self,
        func: Callable = None,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        task_id: Optional[str] = None,
        # Dashboard API compatibility
        request: Optional[str] = None
    ) -> str:
        """Submit a task for execution"""
        with tracer.start_as_current_span("task_manager_submit_task") as span:
            if task_id is None:
                task_id = str(uuid4())
            
            # If request is provided (from dashboard), create a simple processing function
            if request and func is None:
                func = self._process_request_task
                args = (request,)
            
            task = Task(
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs,
                priority=priority,
                timeout=timeout,
                request=request
            )
            
            self.tasks[task_id] = task
            
            # Start execution
            asyncio_task = asyncio.create_task(self._execute_task(task))
            self.running_tasks[task_id] = asyncio_task
            
            span.set_attribute("task_id", task_id)
            span.set_status("OK")
            
            return task_id
    
    async def _process_request_task(self, request: str):
        """Process a natural language request (placeholder for real LLM processing)"""
        logger.info(f"Processing request: {request}")
        # In a real implementation, this would use the orchestrator
        return f"Processed request: {request}"
    
    async def _execute_task(self, task: Task):
        """Execute a single task"""
        async with self.semaphore:
            with tracer.start_as_current_span("task_execution") as span:
                span.set_attribute("task_id", task.task_id)
                
                try:
                    task.status = TaskStatus.RUNNING
                    task.started_at = time.time()
                    
                    if asyncio.iscoroutinefunction(task.func):
                        result = await task.func(*task.args, **task.kwargs)
                    else:
                        result = task.func(*task.args, **task.kwargs)
                    
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = time.time()
                    
                    span.set_status("OK")
                    
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    task.completed_at = time.time()
                    
                    span.set_status("ERROR", str(e))
                    logger.error(f"Task {task.task_id} failed: {e}")
                
                finally:
                    # Clean up
                    if task.task_id in self.running_tasks:
                        del self.running_tasks[task.task_id]
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task"""
        task = self.tasks.get(task_id)
        return task.status if task else None
    
    async def get_task_result(self, task_id: str) -> Any:
        """Get the result of a completed task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.status == TaskStatus.COMPLETED:
            return task.result
        elif task.status == TaskStatus.FAILED:
            raise Exception(task.error)
        else:
            raise ValueError(f"Task {task_id} is not completed yet")
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id in self.running_tasks:
            asyncio_task = self.running_tasks[task_id]
            asyncio_task.cancel()
            
            task = self.tasks.get(task_id)
            if task:
                task.status = TaskStatus.CANCELLED
            
            return True
        return False
    
    async def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get information about all tasks"""
        return [
            {
                "task_id": task.task_id,
                "request": task.request,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error": task.error
            }
            for task in self.tasks.values()
        ]
    
    def list_tasks(self) -> List[Dict]:
        """Get all tasks as list of dictionaries for API compatibility."""
        tasks = []
        for task_id, task in self.tasks.items():
            tasks.append({
                "task_id": task_id,
                "request": task.request,
                "status": task.status.value,
                "priority": task.priority.value,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error": str(task.error) if task.error else None
            })
        return tasks
    
    def get_metrics(self) -> Dict:
        """Get system metrics for API compatibility."""
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        running_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0,
            "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }


# Global task manager instance
task_manager = SimpleTaskManager()
