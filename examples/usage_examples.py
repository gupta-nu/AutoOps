"""
Example usage scripts for AutoOps
"""

import asyncio
import os
from src.agents.orchestrator import AutoOpsOrchestrator
from src.utils.task_manager import task_manager, TaskPriority


async def example_basic_usage():
    """Basic usage example"""
    print("=== AutoOps Basic Usage Example ===")
    
    # Initialize orchestrator
    orchestrator = AutoOpsOrchestrator()
    
    # Example requests
    requests = [
        "Deploy nginx with 3 replicas",
        "Create a service for nginx on port 80",
        "Scale the nginx deployment to 5 replicas",
        "Create a ConfigMap named app-config with key=value pairs",
        "Delete the nginx deployment"
    ]
    
    for request in requests:
        print(f"\nProcessing: {request}")
        
        try:
            result = await orchestrator.process_request(request)
            
            if result.is_completed():
                print("✅ Request completed successfully")
                if result.execution_plan:
                    print(f"   Operations executed: {len(result.execution_plan.operations)}")
            elif result.is_failed():
                print("❌ Request failed")
                for error in result.errors:
                    print(f"   Error: {error}")
            else:
                print("⏳ Request in progress...")
                
        except Exception as e:
            print(f"❌ Exception: {e}")


async def example_task_manager():
    """Task manager usage example"""
    print("\n=== AutoOps Task Manager Example ===")
    
    # Start task manager
    await task_manager.start(num_workers=2)
    
    try:
        # Submit multiple tasks
        tasks = []
        requests = [
            ("Deploy redis with persistence", TaskPriority.HIGH),
            ("Create monitoring namespace", TaskPriority.NORMAL),
            ("Deploy prometheus in monitoring namespace", TaskPriority.NORMAL),
            ("Scale redis to 3 replicas", TaskPriority.LOW)
        ]
        
        for request, priority in requests:
            task_id = await task_manager.submit_task(
                request=request,
                priority=priority
            )
            tasks.append(task_id)
            print(f"Submitted task: {task_id[:8]} - {request}")
        
        # Monitor task progress
        print("\nMonitoring task progress...")
        completed_tasks = set()
        
        while len(completed_tasks) < len(tasks):
            for task_id in tasks:
                if task_id in completed_tasks:
                    continue
                    
                status = await task_manager.get_task_status(task_id)
                if status and status['status'] in ['completed', 'failed', 'cancelled']:
                    completed_tasks.add(task_id)
                    print(f"Task {task_id[:8]} {status['status']}")
                    
                    if status['status'] == 'failed':
                        print(f"  Error: {status.get('error', 'Unknown')}")
            
            await asyncio.sleep(2)
        
        # Show final metrics
        metrics = await task_manager.get_metrics()
        print(f"\nFinal metrics:")
        print(f"  Total tasks: {metrics['total_tasks']}")
        print(f"  Completed: {metrics['completed_tasks']}")
        print(f"  Failed: {metrics['failed_tasks']}")
        
    finally:
        await task_manager.stop()


async def example_complex_workflow():
    """Complex workflow example"""
    print("\n=== AutoOps Complex Workflow Example ===")
    
    orchestrator = AutoOpsOrchestrator()
    
    # Multi-step application deployment
    workflow_steps = [
        "Create namespace 'myapp'",
        "Create a ConfigMap in myapp namespace with database config",
        "Create a Secret in myapp namespace with database credentials",
        "Deploy PostgreSQL database in myapp namespace with persistent storage",
        "Create a service for PostgreSQL",
        "Deploy the main application with 3 replicas in myapp namespace",
        "Create a service for the main application",
        "Create an ingress for the application with SSL termination",
        "Create a HorizontalPodAutoscaler for the application"
    ]
    
    print(f"Executing {len(workflow_steps)} workflow steps...")
    
    for i, step in enumerate(workflow_steps, 1):
        print(f"\nStep {i}/{len(workflow_steps)}: {step}")
        
        try:
            result = await orchestrator.process_request(step)
            
            if result.is_completed():
                print("✅ Step completed")
                
                # Show execution details
                if result.execution_results:
                    for exec_result in result.execution_results:
                        op = exec_result.operation
                        print(f"   {op.action.value} {op.resource_type.value} '{op.resource_name}' in '{op.namespace}'")
            else:
                print("❌ Step failed")
                for error in result.errors:
                    print(f"   Error: {error}")
                break
                
        except Exception as e:
            print(f"❌ Exception in step {i}: {e}")
            break
    
    print("\nWorkflow completed!")


async def example_monitoring():
    """Monitoring and observability example"""
    print("\n=== AutoOps Monitoring Example ===")
    
    # Start task manager for monitoring
    await task_manager.start()
    
    try:
        # Submit some background tasks
        background_tasks = [
            "Deploy monitoring stack",
            "Configure alerting rules",
            "Deploy log aggregation",
        ]
        
        for request in background_tasks:
            await task_manager.submit_task(request, TaskPriority.NORMAL)
        
        # Monitor metrics periodically
        print("Monitoring system metrics...")
        for i in range(5):
            metrics = await task_manager.get_metrics()
            
            print(f"\nMetrics snapshot {i+1}:")
            print(f"  Active workers: {metrics['running_workers']}")
            print(f"  Queue size: {metrics['queue_size']}")
            print(f"  Total tasks: {metrics['total_tasks']}")
            print(f"  Executing: {metrics['executing_tasks']}")
            print(f"  Completed: {metrics['completed_tasks']}")
            print(f"  Failed: {metrics['failed_tasks']}")
            
            await asyncio.sleep(3)
    
    finally:
        await task_manager.stop()


async def main():
    """Run all examples"""
    # Set environment variables for examples
    os.environ.setdefault('OPENAI_API_KEY', 'your-api-key-here')
    os.environ.setdefault('DEV_MODE', 'true')
    
    print("AutoOps Examples")
    print("================")
    print("Note: Make sure to set your OPENAI_API_KEY environment variable")
    print("and have access to a Kubernetes cluster for full functionality.\n")
    
    try:
        await example_basic_usage()
        await example_task_manager()
        await example_complex_workflow()
        await example_monitoring()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nExample failed with error: {e}")
    
    print("\nExamples completed!")


if __name__ == "__main__":
    asyncio.run(main())
