"""
Executor Agent - Executes Kubernetes operations based on execution plans
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from opentelemetry import trace
from tenacity import retry, stop_after_attempt, wait_exponential

from ..kubernetes.client import KubernetesClient
from ..monitoring.tracing import get_tracer
from .state import (
    AutoOpsState,
    ExecutionResult,
    KubernetesOperation,
    TaskStatus,
    AgentType
)
from config.settings import settings

tracer = get_tracer(__name__)


class ExecutorAgent:
    """
    Executor Agent that executes Kubernetes operations from execution plans
    """
    
    def __init__(self):
        self.k8s_client = KubernetesClient()
        self.max_concurrent_operations = settings.max_concurrent_tasks
    
    @tracer.start_as_current_span("executor_agent_execute")
    async def execute(self, state: AutoOpsState) -> AutoOpsState:
        """
        Execute the operations in the execution plan
        """
        with tracer.start_as_current_span("execution_process") as span:
            span.set_attribute("request_id", str(state.request_id))
            
            if not state.execution_plan:
                state.executor_state.status = TaskStatus.FAILED
                state.add_error("No execution plan available")
                return state
            
            try:
                # Update executor state
                state.executor_state.status = TaskStatus.EXECUTING
                state.executor_state.current_task = "Executing Kubernetes operations"
                state.executor_state.last_updated = datetime.utcnow()
                state.current_step = "executing"
                
                plan = state.execution_plan
                span.set_attribute("operations_count", len(plan.operations))
                
                # Execute operations
                results = await self._execute_operations(plan.operations)
                state.execution_results.extend(results)
                
                # Check if all operations succeeded
                failed_operations = [r for r in results if r.status == TaskStatus.FAILED]
                
                if failed_operations:
                    state.executor_state.status = TaskStatus.FAILED
                    state.executor_state.last_action = f"Execution failed: {len(failed_operations)} operations failed"
                    for result in failed_operations:
                        state.add_error(f"Operation failed: {result.error}")
                else:
                    state.executor_state.status = TaskStatus.COMPLETED
                    state.executor_state.last_action = f"Successfully executed {len(results)} operations"
                
                state.executor_state.last_updated = datetime.utcnow()
                state.update_timestamp()
                
                span.set_attribute("successful_operations", len(results) - len(failed_operations))
                span.set_attribute("failed_operations", len(failed_operations))
                
                return state
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                state.executor_state.status = TaskStatus.FAILED
                state.executor_state.last_action = f"Execution error: {str(e)}"
                state.add_error(f"Executor error: {str(e)}")
                
                return state
    
    async def _execute_operations(self, operations: List[KubernetesOperation]) -> List[ExecutionResult]:
        """Execute operations with concurrency control"""
        semaphore = asyncio.Semaphore(self.max_concurrent_operations)
        
        async def execute_with_semaphore(operation: KubernetesOperation):
            async with semaphore:
                return await self._execute_single_operation(operation)
        
        # Execute operations concurrently
        tasks = [execute_with_semaphore(op) for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        execution_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                execution_results.append(
                    ExecutionResult(
                        operation=operations[i],
                        status=TaskStatus.FAILED,
                        error=str(result)
                    )
                )
            else:
                execution_results.append(result)
        
        return execution_results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _execute_single_operation(self, operation: KubernetesOperation) -> ExecutionResult:
        """Execute a single Kubernetes operation with retry logic"""
        result = ExecutionResult(operation=operation, status=TaskStatus.EXECUTING)
        
        with tracer.start_as_current_span("execute_k8s_operation") as span:
            span.set_attribute("operation.action", operation.action.value)
            span.set_attribute("operation.resource_type", operation.resource_type.value)
            span.set_attribute("operation.namespace", operation.namespace)
            if operation.resource_name:
                span.set_attribute("operation.resource_name", operation.resource_name)
            
            try:
                start_time = datetime.utcnow()
                
                # Execute based on operation type
                if operation.action.value == "CREATE":
                    response = await self.k8s_client.create_resource(
                        resource_type=operation.resource_type.value,
                        namespace=operation.namespace,
                        manifest=operation.manifest
                    )
                elif operation.action.value == "UPDATE":
                    response = await self.k8s_client.update_resource(
                        resource_type=operation.resource_type.value,
                        name=operation.resource_name,
                        namespace=operation.namespace,
                        manifest=operation.manifest
                    )
                elif operation.action.value == "DELETE":
                    response = await self.k8s_client.delete_resource(
                        resource_type=operation.resource_type.value,
                        name=operation.resource_name,
                        namespace=operation.namespace
                    )
                elif operation.action.value == "SCALE":
                    replicas = operation.parameters.get("replicas", 1)
                    response = await self.k8s_client.scale_deployment(
                        name=operation.resource_name,
                        namespace=operation.namespace,
                        replicas=replicas
                    )
                elif operation.action.value == "GET":
                    response = await self.k8s_client.get_resource(
                        resource_type=operation.resource_type.value,
                        name=operation.resource_name,
                        namespace=operation.namespace
                    )
                elif operation.action.value == "LIST":
                    response = await self.k8s_client.list_resources(
                        resource_type=operation.resource_type.value,
                        namespace=operation.namespace
                    )
                elif operation.action.value == "PATCH":
                    response = await self.k8s_client.patch_resource(
                        resource_type=operation.resource_type.value,
                        name=operation.resource_name,
                        namespace=operation.namespace,
                        patch=operation.manifest
                    )
                else:
                    raise ValueError(f"Unsupported operation: {operation.action}")
                
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                result.status = TaskStatus.COMPLETED
                result.result = response
                result.completed_at = end_time
                result.duration = duration
                
                span.set_attribute("operation.success", True)
                span.set_attribute("operation.duration", duration)
                
            except Exception as e:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                result.status = TaskStatus.FAILED
                result.error = str(e)
                result.completed_at = end_time
                result.duration = duration
                
                span.record_exception(e)
                span.set_attribute("operation.success", False)
                span.set_attribute("operation.error", str(e))
                
                raise  # Re-raise for retry logic
        
        return result
    
    async def rollback_operations(self, results: List[ExecutionResult]) -> List[ExecutionResult]:
        """Rollback operations in case of failure"""
        rollback_results = []
        
        # Reverse the order for rollback
        for result in reversed(results):
            if result.status == TaskStatus.COMPLETED and result.operation.action.value == "CREATE":
                # Create rollback operation (DELETE)
                rollback_op = KubernetesOperation(
                    action="DELETE",
                    resource_type=result.operation.resource_type,
                    resource_name=result.operation.resource_name,
                    namespace=result.operation.namespace
                )
                
                try:
                    rollback_result = await self._execute_single_operation(rollback_op)
                    rollback_results.append(rollback_result)
                except Exception as e:
                    rollback_results.append(
                        ExecutionResult(
                            operation=rollback_op,
                            status=TaskStatus.FAILED,
                            error=f"Rollback failed: {str(e)}"
                        )
                    )
        
        return rollback_results
