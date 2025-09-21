"""
Planner Agent - Interprets natural language requests and creates execution plans
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from opentelemetry import trace

from ..monitoring.tracing import get_tracer
from .state import (
    AutoOpsState, 
    ExecutionPlan, 
    KubernetesOperation, 
    KubernetesAction, 
    ResourceType, 
    TaskStatus,
    AgentType
)
from config.settings import settings

tracer = get_tracer(__name__)


class PlannerAgent:
    """
    Planner Agent that interprets natural language requests and creates
    detailed execution plans for Kubernetes operations.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1
        )
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the planner agent"""
        return """
You are an expert Kubernetes operations planner. Your role is to interpret natural language requests 
and create detailed, executable plans for Kubernetes operations.

Available Kubernetes Actions:
- CREATE: Create new resources
- UPDATE: Update existing resources  
- DELETE: Remove resources
- SCALE: Scale deployments/statefulsets
- PATCH: Apply patches to resources
- GET: Retrieve resource information
- LIST: List resources

Available Resource Types:
- pod, deployment, service, configmap, secret, ingress, namespace, node, persistentvolumeclaim, horizontalpodautoscaler

Your response MUST be a valid JSON object with the following structure:
{
    "description": "Human-readable description of the plan",
    "operations": [
        {
            "action": "CREATE|UPDATE|DELETE|SCALE|PATCH|GET|LIST",
            "resource_type": "pod|deployment|service|...",
            "resource_name": "name-of-resource",
            "namespace": "target-namespace",
            "manifest": {...kubernetes-manifest...},
            "parameters": {...additional-parameters...}
        }
    ],
    "estimated_duration": 60
}

Rules:
1. Break complex requests into multiple operations
2. Consider dependencies (e.g., create namespace before resources)
3. Include proper Kubernetes manifests for CREATE operations
4. Use appropriate naming conventions
5. Default namespace is "default" unless specified
6. Provide realistic time estimates in seconds
7. Validate resource specifications

Examples:
- "Deploy nginx" → CREATE deployment + CREATE service
- "Scale to 5 replicas" → SCALE deployment
- "Delete the api pods" → DELETE deployment

Be precise and ensure all operations are valid Kubernetes actions.
"""
    
    @tracer.start_as_current_span("planner_agent_plan")
    async def plan(self, state: AutoOpsState) -> AutoOpsState:
        """
        Create an execution plan based on the natural language request
        """
        with tracer.start_as_current_span("planning_process") as span:
            span.set_attribute("request", state.original_request)
            span.set_attribute("request_id", str(state.request_id))
            
            try:
                # Update planner state
                state.planner_state.status = TaskStatus.PLANNING
                state.planner_state.current_task = "Analyzing request and creating plan"
                state.planner_state.last_updated = datetime.utcnow()
                state.current_step = "planning"
                
                # Create messages for LLM
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=f"Request: {state.original_request}")
                ]
                
                # Get plan from LLM
                span.add_event("calling_llm_for_plan")
                response = await self.llm.ainvoke(messages)
                plan_data = self._parse_llm_response(response.content)
                
                # Create execution plan
                execution_plan = self._create_execution_plan(plan_data)
                state.execution_plan = execution_plan
                
                # Update state
                state.planner_state.status = TaskStatus.COMPLETED
                state.planner_state.last_action = f"Created plan with {len(execution_plan.operations)} operations"
                state.planner_state.last_updated = datetime.utcnow()
                state.update_timestamp()
                
                span.set_attribute("plan_operations_count", len(execution_plan.operations))
                span.add_event("planning_completed")
                
                return state
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                state.planner_state.status = TaskStatus.FAILED
                state.planner_state.last_action = f"Planning failed: {str(e)}"
                state.add_error(f"Planner error: {str(e)}")
                
                return state
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse and validate LLM response"""
        try:
            # Clean response (remove markdown formatting if present)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            plan_data = json.loads(response)
            
            # Validate required fields
            if "description" not in plan_data:
                raise ValueError("Missing 'description' field in plan")
            if "operations" not in plan_data:
                raise ValueError("Missing 'operations' field in plan")
            
            return plan_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
    
    def _create_execution_plan(self, plan_data: Dict) -> ExecutionPlan:
        """Create ExecutionPlan object from parsed data"""
        operations = []
        
        for op_data in plan_data.get("operations", []):
            operation = KubernetesOperation(
                action=KubernetesAction(op_data["action"].upper()),
                resource_type=ResourceType(op_data["resource_type"].lower()),
                resource_name=op_data.get("resource_name"),
                namespace=op_data.get("namespace", "default"),
                manifest=op_data.get("manifest"),
                parameters=op_data.get("parameters", {})
            )
            operations.append(operation)
        
        return ExecutionPlan(
            description=plan_data["description"],
            operations=operations,
            estimated_duration=plan_data.get("estimated_duration", 60)
        )
    
    async def validate_plan(self, plan: ExecutionPlan) -> List[str]:
        """Validate execution plan for potential issues"""
        issues = []
        
        # Check for resource naming conflicts
        resource_names = {}
        for op in plan.operations:
            if op.action in [KubernetesAction.CREATE] and op.resource_name:
                key = f"{op.namespace}/{op.resource_type}/{op.resource_name}"
                if key in resource_names:
                    issues.append(f"Duplicate resource creation: {key}")
                resource_names[key] = op
        
        # Check for missing dependencies
        for op in plan.operations:
            if op.action == KubernetesAction.CREATE and op.resource_type != ResourceType.NAMESPACE:
                # Check if namespace exists in plan
                ns_created = any(
                    other_op.action == KubernetesAction.CREATE 
                    and other_op.resource_type == ResourceType.NAMESPACE
                    and other_op.resource_name == op.namespace
                    for other_op in plan.operations
                )
                if op.namespace != "default" and not ns_created:
                    issues.append(f"Namespace '{op.namespace}' not created before use")
        
        return issues
