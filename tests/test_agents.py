"""
Test suite for AutoOps agents
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.agents.state import AutoOpsState, TaskStatus, KubernetesAction, ResourceType
from src.agents.planner import PlannerAgent
from src.agents.executor import ExecutorAgent
from src.agents.orchestrator import AutoOpsOrchestrator


@pytest.fixture
def sample_state():
    """Create a sample AutoOps state for testing"""
    return AutoOpsState(
        original_request="Deploy nginx with 3 replicas"
    )


@pytest.mark.asyncio
class TestPlannerAgent:
    """Test cases for the Planner Agent"""
    
    async def test_plan_simple_deployment(self, sample_state):
        """Test planning a simple deployment"""
        planner = PlannerAgent()
        
        # Mock the LLM response
        mock_response = Mock()
        mock_response.content = '''
        {
            "description": "Deploy nginx with 3 replicas",
            "operations": [
                {
                    "action": "CREATE",
                    "resource_type": "deployment",
                    "resource_name": "nginx",
                    "namespace": "default",
                    "manifest": {
                        "apiVersion": "apps/v1",
                        "kind": "Deployment",
                        "metadata": {"name": "nginx"},
                        "spec": {"replicas": 3}
                    }
                }
            ],
            "estimated_duration": 60
        }
        '''
        
        planner.llm.ainvoke = AsyncMock(return_value=mock_response)
        
        result = await planner.plan(sample_state)
        
        assert result.planner_state.status == TaskStatus.COMPLETED
        assert result.execution_plan is not None
        assert len(result.execution_plan.operations) == 1
        assert result.execution_plan.operations[0].action == KubernetesAction.CREATE
        assert result.execution_plan.operations[0].resource_type == ResourceType.DEPLOYMENT
    
    async def test_plan_validation(self, sample_state):
        """Test plan validation"""
        planner = PlannerAgent()
        
        # Create a plan with issues
        from src.agents.state import ExecutionPlan, KubernetesOperation
        
        plan = ExecutionPlan(
            description="Test plan",
            operations=[
                KubernetesOperation(
                    action=KubernetesAction.CREATE,
                    resource_type=ResourceType.DEPLOYMENT,
                    resource_name="test",
                    namespace="non-existent"
                )
            ]
        )
        
        issues = await planner.validate_plan(plan)
        assert len(issues) > 0
        assert "Namespace 'non-existent' not created before use" in issues[0]


@pytest.mark.asyncio
class TestExecutorAgent:
    """Test cases for the Executor Agent"""
    
    async def test_execute_operations(self, sample_state):
        """Test executing operations"""
        executor = ExecutorAgent()
        
        # Mock Kubernetes client
        executor.k8s_client.create_resource = AsyncMock(return_value={"status": "success"})
        
        # Create execution plan
        from src.agents.state import ExecutionPlan, KubernetesOperation
        
        sample_state.execution_plan = ExecutionPlan(
            description="Test execution",
            operations=[
                KubernetesOperation(
                    action=KubernetesAction.CREATE,
                    resource_type=ResourceType.DEPLOYMENT,
                    resource_name="test",
                    namespace="default",
                    manifest={"test": "manifest"}
                )
            ]
        )
        
        result = await executor.execute(sample_state)
        
        assert result.executor_state.status == TaskStatus.COMPLETED
        assert len(result.execution_results) == 1
        assert result.execution_results[0].status == TaskStatus.COMPLETED


@pytest.mark.asyncio
class TestOrchestrator:
    """Test cases for the AutoOps Orchestrator"""
    
    async def test_process_request(self):
        """Test processing a complete request"""
        orchestrator = AutoOpsOrchestrator()
        
        # Mock agents
        orchestrator.planner.plan = AsyncMock()
        orchestrator.executor.execute = AsyncMock()
        
        # Mock successful planning
        async def mock_plan(state):
            from src.agents.state import ExecutionPlan, KubernetesOperation
            state.execution_plan = ExecutionPlan(
                description="Mock plan",
                operations=[
                    KubernetesOperation(
                        action=KubernetesAction.CREATE,
                        resource_type=ResourceType.DEPLOYMENT,
                        resource_name="test",
                        namespace="default"
                    )
                ]
            )
            state.planner_state.status = TaskStatus.COMPLETED
            return state
        
        # Mock successful execution
        async def mock_execute(state):
            state.executor_state.status = TaskStatus.COMPLETED
            return state
        
        orchestrator.planner.plan = mock_plan
        orchestrator.executor.execute = mock_execute
        
        result = await orchestrator.process_request("Deploy test application")
        
        assert result.is_completed()
        assert not result.is_failed()


@pytest.mark.asyncio
class TestTaskManager:
    """Test cases for the Task Manager"""
    
    async def test_submit_task(self):
        """Test task submission"""
        from src.utils.task_manager import TaskManager, TaskPriority
        
        task_manager = TaskManager()
        await task_manager.start(num_workers=1)
        
        try:
            task_id = await task_manager.submit_task(
                request="Test request",
                priority=TaskPriority.NORMAL
            )
            
            assert task_id is not None
            
            # Check task status
            status = await task_manager.get_task_status(task_id)
            assert status is not None
            assert status['status'] in ['pending', 'executing']
            
        finally:
            await task_manager.stop()
    
    async def test_task_metrics(self):
        """Test task metrics"""
        from src.utils.task_manager import TaskManager
        
        task_manager = TaskManager()
        await task_manager.start(num_workers=1)
        
        try:
            metrics = await task_manager.get_metrics()
            
            assert 'total_tasks' in metrics
            assert 'pending_tasks' in metrics
            assert 'executing_tasks' in metrics
            assert 'completed_tasks' in metrics
            assert 'failed_tasks' in metrics
            
        finally:
            await task_manager.stop()


@pytest.mark.asyncio
class TestKubernetesClient:
    """Test cases for Kubernetes Client"""
    
    async def test_create_resource(self):
        """Test resource creation (mocked)"""
        from src.kubernetes.client import KubernetesClient
        
        client = KubernetesClient()
        
        # Mock the Kubernetes API client
        client.apps_v1.create_namespaced_deployment = Mock(
            return_value=Mock(to_dict=lambda: {"status": "created"})
        )
        
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "test"},
            "spec": {"replicas": 1}
        }
        
        result = await client.create_resource(
            resource_type="deployment",
            namespace="default",
            manifest=manifest
        )
        
        assert result["status"] == "created"


if __name__ == "__main__":
    pytest.main([__file__])
