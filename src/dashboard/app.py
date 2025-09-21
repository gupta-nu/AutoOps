"""
FastAPI Dashboard for AutoOps real-time monitoring
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..agents.orchestrator import AutoOpsOrchestrator
from ..utils.task_manager import task_manager, TaskPriority
from ..monitoring.tracing import instrument_fastapi, initialize_tracing
from config.settings import settings


class TaskRequest(BaseModel):
    """Request model for task submission"""
    request: str
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[int] = None


class TaskResponse(BaseModel):
    """Response model for task submission"""
    task_id: str
    status: str
    message: str


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Initialize FastAPI app
app = FastAPI(
    title="AutoOps Dashboard",
    description="Real-time monitoring dashboard for AutoOps multi-agent system",
    version="1.0.0"
)

# Initialize tracing
initialize_tracing()
instrument_fastapi(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager
manager = ConnectionManager()

# Global orchestrator instance
orchestrator = AutoOpsOrchestrator()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await task_manager.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await task_manager.stop()


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AutoOps Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stat-value { font-size: 2em; font-weight: bold; color: #3498db; }
            .task-form { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .task-list { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .task-item { border-bottom: 1px solid #eee; padding: 10px 0; }
            .task-status { padding: 4px 8px; border-radius: 4px; color: white; font-size: 0.8em; }
            .status-pending { background: #f39c12; }
            .status-executing { background: #3498db; }
            .status-completed { background: #27ae60; }
            .status-failed { background: #e74c3c; }
            .status-cancelled { background: #95a5a6; }
            input, textarea, select, button { margin: 5px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #3498db; color: white; cursor: pointer; }
            button:hover { background: #2980b9; }
            .log { background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 4px; max-height: 300px; overflow-y: auto; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AutoOps Dashboard</h1>
                <p>Multi-Agent Kubernetes Orchestrator</p>
            </div>
            
            <div class="stats" id="stats">
                <!-- Stats will be populated by JavaScript -->
            </div>
            
            <div class="task-form">
                <h3>Submit New Task</h3>
                <textarea id="taskRequest" placeholder="Enter your Kubernetes request in natural language..." rows="3" style="width: 100%;"></textarea>
                <select id="taskPriority">
                    <option value="normal">Normal Priority</option>
                    <option value="low">Low Priority</option>
                    <option value="high">High Priority</option>
                    <option value="critical">Critical Priority</option>
                </select>
                <button onclick="submitTask()">Submit Task</button>
            </div>
            
            <div class="task-list">
                <h3>Recent Tasks</h3>
                <div id="taskList">
                    <!-- Tasks will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="task-list">
                <h3>Real-time Log</h3>
                <div class="log" id="logOutput">
                    Connecting to WebSocket...
                </div>
            </div>
        </div>

        <script>
            let ws = null;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                
                ws.onopen = function(event) {
                    addLog('WebSocket connected');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = function(event) {
                    addLog('WebSocket disconnected. Reconnecting...');
                    setTimeout(connectWebSocket, 3000);
                };
                
                ws.onerror = function(error) {
                    addLog('WebSocket error: ' + error);
                };
            }
            
            function handleWebSocketMessage(data) {
                if (data.type === 'task_update') {
                    addLog(`Task ${data.task_id}: ${data.status}`);
                    loadTasks();
                } else if (data.type === 'metrics') {
                    updateStats(data.data);
                }
            }
            
            function addLog(message) {
                const log = document.getElementById('logOutput');
                const timestamp = new Date().toLocaleTimeString();
                log.innerHTML += `<div>[${timestamp}] ${message}</div>`;
                log.scrollTop = log.scrollHeight;
            }
            
            function updateStats(metrics) {
                const statsContainer = document.getElementById('stats');
                statsContainer.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-value">${metrics.total_tasks}</div>
                        <div>Total Tasks</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${metrics.executing_tasks}</div>
                        <div>Executing</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${metrics.completed_tasks}</div>
                        <div>Completed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${metrics.failed_tasks}</div>
                        <div>Failed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${metrics.active_tasks}</div>
                        <div>Active Workers</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${metrics.queue_size}</div>
                        <div>Queue Size</div>
                    </div>
                `;
            }
            
            async function submitTask() {
                const request = document.getElementById('taskRequest').value.trim();
                const priority = document.getElementById('taskPriority').value;
                
                if (!request) {
                    alert('Please enter a request');
                    return;
                }
                
                try {
                    const response = await fetch('/api/tasks', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            request: request,
                            priority: priority
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        document.getElementById('taskRequest').value = '';
                        addLog(`Task submitted: ${result.task_id}`);
                        loadTasks();
                    } else {
                        addLog(`Error: ${result.detail}`);
                    }
                } catch (error) {
                    addLog(`Error submitting task: ${error}`);
                }
            }
            
            async function loadTasks() {
                try {
                    const response = await fetch('/api/tasks?limit=10');
                    const tasks = await response.json();
                    
                    const taskList = document.getElementById('taskList');
                    taskList.innerHTML = tasks.map(task => `
                        <div class="task-item">
                            <div><strong>${task.task_id}</strong></div>
                            <div>${task.request.substring(0, 100)}${task.request.length > 100 ? '...' : ''}</div>
                            <div>
                                <span class="task-status status-${task.status}">${task.status.toUpperCase()}</span>
                                Priority: ${task.priority} | 
                                Created: ${new Date(task.created_at).toLocaleString()}
                                ${task.error ? `| Error: ${task.error}` : ''}
                            </div>
                        </div>
                    `).join('');
                } catch (error) {
                    addLog(`Error loading tasks: ${error}`);
                }
            }
            
            async function loadMetrics() {
                try {
                    const response = await fetch('/api/metrics');
                    const metrics = await response.json();
                    updateStats(metrics);
                } catch (error) {
                    console.error('Error loading metrics:', error);
                }
            }
            
            // Initialize
            connectWebSocket();
            loadTasks();
            loadMetrics();
            
            // Refresh data periodically
            setInterval(loadTasks, 5000);
            setInterval(loadMetrics, 2000);
        </script>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(1)
            
            # Send metrics update
            metrics = await task_manager.get_metrics()
            await manager.send_message({
                "type": "metrics",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/tasks", response_model=TaskResponse)
async def submit_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    """Submit a new task for execution"""
    try:
        task_id = await task_manager.submit_task(
            request=task_request.request,
            priority=task_request.priority,
            timeout=task_request.timeout
        )
        
        # Notify WebSocket clients
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "task_update",
                "task_id": task_id,
                "status": "submitted",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message="Task submitted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 100):
    """List tasks with optional filtering"""
    try:
        from ..agents.state import TaskStatus
        task_status = TaskStatus(status) if status else None
        tasks = await task_manager.list_tasks(status=task_status, limit=limit)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get details of a specific task"""
    task = await task_manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str, background_tasks: BackgroundTasks):
    """Cancel a specific task"""
    success = await task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Notify WebSocket clients
    background_tasks.add_task(
        manager.broadcast,
        {
            "type": "task_update",
            "task_id": task_id,
            "status": "cancelled",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {"message": "Task cancelled successfully"}


@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        metrics = await task_manager.get_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/workflow/{request_id}")
async def get_workflow_status(request_id: str):
    """Get workflow status for a specific request"""
    try:
        status = await orchestrator.get_workflow_status(request_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.dashboard_host,
        port=settings.dashboard_port,
        reload=settings.dev_mode
    )
