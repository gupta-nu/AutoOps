"""
Task Manager - Asynchronous task orchestration with robust error handling
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
from enum import Enum
import redis.asyncio as redis

from opentelemetry import trace
from tenacity import retry, stop_after_attempt, wait_exponential

from ..monitoring.tracing_simple import get_tracer
from ..agents.state import TaskStatus, AutoOpsState
from config.settings import settings

tracer = get_tracer(__name__)


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Task:
    """Task representation for async execution"""
    
    def __init__(
        self,
        task_id: str,
        request: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[int] = None,
        callback: Optional[Callable] = None
    ):
        self.task_id = task_id
        self.request = request
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.timeout = timeout or settings.task_timeout_seconds
        self.callback = callback
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[AutoOpsState] = None
        self.error: Optional[str] = None
        self.retry_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "task_id": self.task_id,
            "request": self.request,
            "priority": self.priority.value,
            "status": self.status.value,
            "timeout": self.timeout,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        task = cls(
            task_id=data["task_id"],
            request=data["request"],
            priority=TaskPriority(data["priority"]),
            timeout=data.get("timeout")
        )
        task.status = TaskStatus(data["status"])
        task.created_at = datetime.fromisoformat(data["created_at"])
        task.started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        task.completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        task.error = data.get("error")
        task.retry_count = data.get("retry_count", 0)
        return task


class TaskManager:
    """
    Manages asynchronous task execution with priority queues, 
    error handling, and persistent state
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for state persistence"""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True
            )
        except Exception as e:
            # Fall back to in-memory storage if Redis is not available
            self.redis_client = None
    
    async def start(self, num_workers: int = None):
        """Start the task manager with worker processes"""
        if self.is_running:
            return
        
        num_workers = num_workers or settings.max_concurrent_tasks
        self.is_running = True
        
        # Start worker tasks
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_completed_tasks())
        self.workers.append(cleanup_task)
    
    async def stop(self):
        """Stop the task manager gracefully"""
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Cancel running tasks
        for task in self.running_tasks.values():
            task.cancel()
        
        self.workers.clear()
        self.running_tasks.clear()
    
    @tracer.start_as_current_span("task_manager_submit_task")
    async def submit_task(
        self, 
        request: str, 
        priority: TaskPriority = TaskPriority.NORMAL,
        task_id: Optional[str] = None,
        timeout: Optional[int] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """Submit a new task for execution"""
        task_id = task_id or str(uuid4())
        
        task = Task(
            task_id=task_id,
            request=request,
            priority=priority,
            timeout=timeout,
            callback=callback
        )
        
        # Persist task state
        await self._persist_task(task)
        
        # Add to queue with priority
        await self.task_queue.put((priority.value, task))
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific task"""
        task = await self._load_task(task_id)
        return task.to_dict() if task else None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task"""
        # Cancel running task
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        # Update task status
        task = await self._load_task(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            await self._persist_task(task)
            return True
        
        return False
    
    async def list_tasks(
        self, 
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering"""
        tasks = await self._load_all_tasks()
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return [t.to_dict() for t in tasks[:limit]]
    
    async def _worker(self, worker_name: str):
        """Worker process that executes tasks from the queue"""
        from ..agents.orchestrator import AutoOpsOrchestrator
        
        orchestrator = AutoOpsOrchestrator()
        
        with tracer.start_as_current_span(f"task_worker_{worker_name}"):
            while self.is_running:
                try:
                    # Get task from queue with timeout
                    try:
                        priority, task = await asyncio.wait_for(
                            self.task_queue.get(), timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        continue
                    
                    # Execute task
                    execution_task = asyncio.create_task(
                        self._execute_task(task, orchestrator)
                    )
                    self.running_tasks[task.task_id] = execution_task
                    
                    try:
                        await execution_task
                    finally:
                        if task.task_id in self.running_tasks:
                            del self.running_tasks[task.task_id]
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Log worker error but continue
                    pass
    
    @tracer.start_as_current_span("task_execution")
    async def _execute_task(self, task: Task, orchestrator):
        """Execute a single task with timeout and error handling"""
        span = trace.get_current_span()
        span.set_attribute("task_id", task.task_id)
        span.set_attribute("task_priority", task.priority.value)
        
        task.status = TaskStatus.EXECUTING
        task.started_at = datetime.utcnow()
        await self._persist_task(task)
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                orchestrator.process_request(task.request, task.task_id),
                timeout=task.timeout
            )
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            span.set_attribute("task_success", True)
            
            # Execute callback if provided
            if task.callback:
                try:
                    await task.callback(task, result)
                except Exception as e:
                    # Log callback error but don't fail the task
                    span.add_event("callback_error", {"error": str(e)})
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = f"Task timed out after {task.timeout} seconds"
            task.completed_at = datetime.utcnow()
            span.set_attribute("task_success", False)
            span.set_attribute("timeout", True)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            span.record_exception(e)
            span.set_attribute("task_success", False)
        
        finally:
            await self._persist_task(task)
    
    async def _cleanup_completed_tasks(self):
        """Cleanup completed tasks periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                tasks = await self._load_all_tasks()
                
                for task in tasks:
                    if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                        and task.completed_at and task.completed_at < cutoff_time):
                        await self._delete_task(task.task_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log cleanup error but continue
                pass
    
    async def _persist_task(self, task: Task):
        """Persist task state to Redis or memory"""
        if self.redis_client:
            try:
                await self.redis_client.set(
                    f"autoops:task:{task.task_id}",
                    json.dumps(task.to_dict()),
                    ex=86400  # 24 hour expiry
                )
            except Exception:
                # Fall back to in-memory storage
                pass
    
    async def _load_task(self, task_id: str) -> Optional[Task]:
        """Load task from Redis or memory"""
        if self.redis_client:
            try:
                data = await self.redis_client.get(f"autoops:task:{task_id}")
                if data:
                    return Task.from_dict(json.loads(data))
            except Exception:
                pass
        return None
    
    async def _load_all_tasks(self) -> List[Task]:
        """Load all tasks from storage"""
        tasks = []
        if self.redis_client:
            try:
                keys = await self.redis_client.keys("autoops:task:*")
                for key in keys:
                    data = await self.redis_client.get(key)
                    if data:
                        tasks.append(Task.from_dict(json.loads(data)))
            except Exception:
                pass
        return tasks
    
    async def _delete_task(self, task_id: str):
        """Delete task from storage"""
        if self.redis_client:
            try:
                await self.redis_client.delete(f"autoops:task:{task_id}")
            except Exception:
                pass
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get task manager metrics"""
        tasks = await self._load_all_tasks()
        
        metrics = {
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "executing_tasks": len([t for t in tasks if t.status == TaskStatus.EXECUTING]),
            "completed_tasks": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "cancelled_tasks": len([t for t in tasks if t.status == TaskStatus.CANCELLED]),
            "running_workers": len(self.workers),
            "active_tasks": len(self.running_tasks),
            "queue_size": self.task_queue.qsize()
        }
        
        return metrics


# Global task manager instance
task_manager = TaskManager()
