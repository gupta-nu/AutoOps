#!/usr/bin/env python3
"""
Standalone AutoOps Demo - Works without dependencies
This script demonstrates the core functionality of AutoOps
"""

import asyncio
import json
import sys
import os
import time
from typing import Dict, Any, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class DemoTaskManager:
    """Simple task manager for demo purposes"""
    
    def __init__(self):
        self.tasks = {}
        self.task_counter = 0
    
    def submit_task(self, request: str) -> str:
        """Submit a new task"""
        self.task_counter += 1
        task_id = f"task-{self.task_counter}"
        
        self.tasks[task_id] = {
            "id": task_id,
            "request": request,
            "status": "processing",
            "created_at": time.time(),
            "result": None
        }
        
        # Simulate processing
        result = self._process_task(request)
        self.tasks[task_id]["status"] = "completed"
        self.tasks[task_id]["result"] = result
        
        return task_id
    
    def _process_task(self, request: str) -> Dict[str, Any]:
        """Process a task request"""
        request_lower = request.lower()
        
        if "nginx" in request_lower and "deployment" in request_lower:
            if "create" in request_lower:
                return {
                    "action": "create_deployment",
                    "resource": "nginx",
                    "replicas": 3 if "3" in request else 1,
                    "status": "success",
                    "message": "Nginx deployment created successfully"
                }
            elif "scale" in request_lower:
                replicas = 5 if "5" in request else 3
                return {
                    "action": "scale_deployment",
                    "resource": "nginx",
                    "replicas": replicas,
                    "status": "success",
                    "message": f"Nginx deployment scaled to {replicas} replicas"
                }
        
        elif "service" in request_lower and "nginx" in request_lower:
            return {
                "action": "create_service",
                "resource": "nginx",
                "port": 80,
                "status": "success",
                "message": "Service created for nginx deployment"
            }
        
        elif "list" in request_lower and "pod" in request_lower:
            return {
                "action": "list_pods",
                "namespace": "default",
                "pods": [
                    {"name": "nginx-deployment-abc123", "status": "Running"},
                    {"name": "nginx-deployment-def456", "status": "Running"},
                    {"name": "nginx-deployment-ghi789", "status": "Running"}
                ],
                "status": "success",
                "message": "Listed 3 pods in default namespace"
            }
        
        else:
            return {
                "action": "unknown",
                "status": "success",
                "message": f"Processed request: {request}"
            }
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task details"""
        return self.tasks.get(task_id, {"error": "Task not found"})
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks"""
        return list(self.tasks.values())

def main():
    """Main demo function"""
    print("🚀 AutoOps Multi-Agent Kubernetes Orchestrator - Standalone Demo")
    print("================================================================")
    print()
    
    task_manager = DemoTaskManager()
    
    print("✅ AutoOps core system initialized")
    print("📊 Task manager ready")
    print()
    
    # Demo scenarios
    demo_tasks = [
        "Create nginx deployment with 3 replicas",
        "Scale nginx deployment to 5 replicas", 
        "Create service for nginx on port 80",
        "List all pods in default namespace"
    ]
    
    print("🎯 Running demo scenarios:")
    print("-" * 40)
    
    for i, task_request in enumerate(demo_tasks, 1):
        print(f"\n{i}. Processing: '{task_request}'")
        
        # Submit task
        task_id = task_manager.submit_task(task_request)
        print(f"   ✓ Task submitted: {task_id}")
        
        # Get result
        task = task_manager.get_task(task_id)
        result = task["result"]
        
        print(f"   ✓ Status: {result['status']}")
        print(f"   ✓ Action: {result['action']}")
        print(f"   ✓ Message: {result['message']}")
        
        # Add some details based on action
        if result["action"] == "create_deployment":
            print(f"   📦 Created deployment with {result['replicas']} replicas")
        elif result["action"] == "scale_deployment":
            print(f"   📈 Scaled to {result['replicas']} replicas")
        elif result["action"] == "create_service":
            print(f"   🌐 Service exposed on port {result['port']}")
        elif result["action"] == "list_pods":
            print(f"   📋 Found {len(result['pods'])} pods:")
            for pod in result["pods"]:
                print(f"       • {pod['name']} ({pod['status']})")
    
    print(f"\n📊 Demo Summary:")
    print(f"   • Total tasks processed: {len(demo_tasks)}")
    print(f"   • All tasks completed successfully")
    
    # Show task list
    print(f"\n📋 Task History:")
    tasks = task_manager.list_tasks()
    for task in tasks:
        print(f"   {task['id']}: {task['request']} -> {task['status']}")
    
    print("\n🎉 Demo completed successfully!")
    print("\n🔧 What AutoOps can do:")
    print("   • Process natural language Kubernetes requests")
    print("   • Create and manage deployments, services, pods")
    print("   • Scale applications dynamically")
    print("   • Monitor and track all operations")
    print("   • Provide real-time status and feedback")
    
    print("\n🚀 Next steps:")
    print("   1. Install full dependencies: pip install -r requirements-minimal.txt")
    print("   2. Start web dashboard: python3 main_simple.py serve")
    print("   3. Set OPENAI_API_KEY for AI-powered processing")
    print("   4. Configure kubectl for real Kubernetes cluster")
    
    print("\n📖 Try these commands:")
    print("   python3 main_simple.py health")
    print("   python3 main_simple.py version")
    print("   python3 standalone_demo.py")

if __name__ == "__main__":
    main()
