"""
AutoOps Orchestrator - LangGraph workflow for multi-agent Kubernetes operations
"""

import asyncio
from typing import Dict, Any, Optional
from uuid import uuid4

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from opentelemetry import trace

from .state import AutoOpsState, TaskStatus
from .planner import PlannerAgent
from .executor import ExecutorAgent
from ..monitoring.tracing_simple import get_tracer, initialize_tracing
from config.settings import settings

tracer = get_tracer(__name__)


class AutoOpsOrchestrator:
    """
    Main orchestrator class that coordinates the multi-agent workflow
    using LangGraph for state management and execution flow.
    """
    
    def __init__(self):
        # Initialize tracing
        initialize_tracing()
        
        # Initialize agents
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        
        # Initialize workflow
        self.workflow = self._create_workflow()
        self.checkpointer = MemorySaver()
        
        # Compile the graph
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AutoOpsState)
        
        # Add nodes
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("validator", self._validator_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Define the flow
        workflow.set_entry_point("planner")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "planner",
            self._should_execute,
            {
                "execute": "validator",
                "error": "error_handler",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "validator",
            self._should_proceed_with_execution,
            {
                "execute": "executor",
                "error": "error_handler",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "executor",
            self._check_execution_result,
            {
                "success": END,
                "error": "error_handler",
                "retry": "executor"
            }
        )
        
        workflow.add_edge("error_handler", END)
        
        return workflow
    
    async def process_request(self, request: str, request_id: Optional[str] = None) -> AutoOpsState:
        """
        Process a natural language request through the multi-agent workflow
        """
        with tracer.start_as_current_span("orchestrator_process_request") as span:
            span.set_attribute("request", request)
            
            # Create initial state
            initial_state = AutoOpsState(
                request_id=uuid4() if not request_id else request_id,
                original_request=request
            )
            
            span.set_attribute("request_id", str(initial_state.request_id))
            
            try:
                # Execute the workflow
                config = {"configurable": {"thread_id": str(initial_state.request_id)}}
                
                result = await self.app.ainvoke(initial_state, config=config)
                
                span.set_attribute("workflow_completed", True)
                span.set_attribute("final_status", result.current_step)
                
                return result
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                # Update state with error
                initial_state.add_error(f"Orchestration error: {str(e)}")
                initial_state.planner_state.status = TaskStatus.FAILED
                initial_state.executor_state.status = TaskStatus.FAILED
                
                return initial_state
    
    async def _planner_node(self, state: AutoOpsState) -> AutoOpsState:
        """Planner agent node"""
        return await self.planner.plan(state)
    
    async def _executor_node(self, state: AutoOpsState) -> AutoOpsState:
        """Executor agent node"""
        return await self.executor.execute(state)
    
    async def _validator_node(self, state: AutoOpsState) -> AutoOpsState:
        """Validate the execution plan before execution"""
        with tracer.start_as_current_span("validator_node") as span:
            if not state.execution_plan:
                state.add_error("No execution plan to validate")
                return state
            
            try:
                # Validate plan
                issues = await self.planner.validate_plan(state.execution_plan)
                
                if issues:
                    state.add_error(f"Plan validation issues: {'; '.join(issues)}")
                    span.set_attribute("validation_passed", False)
                    span.set_attribute("issues_count", len(issues))
                else:
                    span.set_attribute("validation_passed", True)
                    state.current_step = "validated"
                
                return state
                
            except Exception as e:
                span.record_exception(e)
                state.add_error(f"Validation error: {str(e)}")
                return state
    
    async def _error_handler_node(self, state: AutoOpsState) -> AutoOpsState:
        """Handle errors and potentially retry"""
        with tracer.start_as_current_span("error_handler_node") as span:
            span.set_attribute("error_count", len(state.errors))
            span.set_attribute("retry_count", state.retry_count)
            
            # Log errors
            for error in state.errors:
                span.add_event("error", {"error": error})
            
            # Check if we should retry
            if state.retry_count < settings.retry_max_attempts:
                state.retry_count += 1
                state.current_step = "retrying"
                
                # Reset agent states for retry
                state.planner_state.status = TaskStatus.PENDING
                state.executor_state.status = TaskStatus.PENDING
                
                span.set_attribute("action", "retry")
            else:
                state.current_step = "failed"
                span.set_attribute("action", "failed")
            
            return state
    
    def _should_execute(self, state: AutoOpsState) -> str:
        """Determine if we should proceed to execution"""
        if state.planner_state.status == TaskStatus.FAILED:
            return "error"
        elif state.planner_state.status == TaskStatus.COMPLETED and state.execution_plan:
            return "execute"
        else:
            return "end"
    
    def _should_proceed_with_execution(self, state: AutoOpsState) -> str:
        """Determine if validation passed and we should execute"""
        if state.errors:
            return "error"
        elif state.current_step == "validated":
            return "execute"
        else:
            return "end"
    
    def _check_execution_result(self, state: AutoOpsState) -> str:
        """Check execution results and determine next action"""
        if state.executor_state.status == TaskStatus.FAILED:
            if state.retry_count < settings.retry_max_attempts:
                return "retry"
            else:
                return "error"
        elif state.executor_state.status == TaskStatus.COMPLETED:
            return "success"
        else:
            return "error"
    
    async def get_workflow_status(self, request_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow"""
        try:
            config = {"configurable": {"thread_id": request_id}}
            state = await self.app.aget_state(config)
            
            if state and state.values:
                autoops_state = AutoOpsState.parse_obj(state.values)
                return {
                    "request_id": str(autoops_state.request_id),
                    "current_step": autoops_state.current_step,
                    "planner_status": autoops_state.planner_state.status.value,
                    "executor_status": autoops_state.executor_state.status.value,
                    "execution_plan": autoops_state.execution_plan.dict() if autoops_state.execution_plan else None,
                    "execution_results": [r.dict() for r in autoops_state.execution_results],
                    "errors": autoops_state.errors,
                    "retry_count": autoops_state.retry_count,
                    "created_at": autoops_state.created_at.isoformat(),
                    "updated_at": autoops_state.updated_at.isoformat()
                }
            else:
                return {"error": "Workflow not found"}
                
        except Exception as e:
            return {"error": f"Failed to get workflow status: {str(e)}"}
    
    async def cancel_workflow(self, request_id: str) -> bool:
        """Cancel a running workflow"""
        try:
            # This is a simplified cancellation - in a real implementation,
            # you'd need to implement proper cancellation logic
            config = {"configurable": {"thread_id": request_id}}
            state = await self.app.aget_state(config)
            
            if state and state.values:
                autoops_state = AutoOpsState.parse_obj(state.values)
                autoops_state.planner_state.status = TaskStatus.CANCELLED
                autoops_state.executor_state.status = TaskStatus.CANCELLED
                autoops_state.current_step = "cancelled"
                
                # Update state
                await self.app.aupdate_state(config, autoops_state.dict())
                return True
            
            return False
            
        except Exception as e:
            return False
