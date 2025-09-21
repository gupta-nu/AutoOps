# AutoOps API Documentation

## Overview

AutoOps provides a RESTful API for submitting and managing Kubernetes operations through natural language requests. The API is built with FastAPI and includes real-time WebSocket support for monitoring.

## Base URL

```
http://localhost:8080/api
```

## Authentication

Currently, the API does not require authentication for development. In production, you should implement proper authentication mechanisms.

## Endpoints

### Health Check

#### GET /api/health

Check the health status of the AutoOps system.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0"
}
```

### Task Management

#### POST /api/tasks

Submit a new task for execution.

**Request Body:**
```json
{
  "request": "Deploy nginx with 3 replicas",
  "priority": "normal",
  "timeout": 300
}
```

**Parameters:**
- `request` (string, required): Natural language description of the Kubernetes operation
- `priority` (string, optional): Task priority - "low", "normal", "high", "critical" (default: "normal")
- `timeout` (integer, optional): Task timeout in seconds (default: 300)

**Response:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "submitted",
  "message": "Task submitted successfully"
}
```

#### GET /api/tasks

List tasks with optional filtering.

**Query Parameters:**
- `status` (string, optional): Filter by task status - "pending", "executing", "completed", "failed", "cancelled"
- `limit` (integer, optional): Maximum number of tasks to return (default: 100)

**Response:**
```json
[
  {
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "request": "Deploy nginx with 3 replicas",
    "priority": "normal",
    "status": "completed",
    "created_at": "2024-01-01T12:00:00.000Z",
    "started_at": "2024-01-01T12:00:05.000Z",
    "completed_at": "2024-01-01T12:01:00.000Z",
    "error": null,
    "retry_count": 0
  }
]
```

#### GET /api/tasks/{task_id}

Get details of a specific task.

**Response:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "request": "Deploy nginx with 3 replicas",
  "priority": "normal",
  "status": "completed",
  "timeout": 300,
  "created_at": "2024-01-01T12:00:00.000Z",
  "started_at": "2024-01-01T12:00:05.000Z",
  "completed_at": "2024-01-01T12:01:00.000Z",
  "error": null,
  "retry_count": 0
}
```

#### DELETE /api/tasks/{task_id}

Cancel a specific task.

**Response:**
```json
{
  "message": "Task cancelled successfully"
}
```

### System Metrics

#### GET /api/metrics

Get system metrics and statistics.

**Response:**
```json
{
  "total_tasks": 150,
  "pending_tasks": 5,
  "executing_tasks": 3,
  "completed_tasks": 140,
  "failed_tasks": 2,
  "cancelled_tasks": 0,
  "running_workers": 4,
  "active_tasks": 3,
  "queue_size": 5
}
```

### Workflow Status

#### GET /api/workflow/{request_id}

Get detailed workflow status for a specific request.

**Response:**
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "current_step": "completed",
  "planner_status": "completed",
  "executor_status": "completed",
  "execution_plan": {
    "plan_id": "456e7890-e89b-12d3-a456-426614174000",
    "description": "Deploy nginx with 3 replicas",
    "operations": [
      {
        "action": "CREATE",
        "resource_type": "deployment",
        "resource_name": "nginx",
        "namespace": "default",
        "manifest": {...},
        "parameters": {}
      }
    ],
    "estimated_duration": 60,
    "created_at": "2024-01-01T12:00:00.000Z"
  },
  "execution_results": [
    {
      "operation_id": "789e0123-e89b-12d3-a456-426614174000",
      "operation": {...},
      "status": "completed",
      "result": {...},
      "error": null,
      "started_at": "2024-01-01T12:00:10.000Z",
      "completed_at": "2024-01-01T12:00:45.000Z",
      "duration": 35.0
    }
  ],
  "errors": [],
  "retry_count": 0,
  "created_at": "2024-01-01T12:00:00.000Z",
  "updated_at": "2024-01-01T12:00:45.000Z"
}
```

## WebSocket API

### Real-time Updates

#### WS /ws

Connect to the WebSocket endpoint for real-time updates.

**Message Types:**

1. **Task Updates:**
```json
{
  "type": "task_update",
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "timestamp": "2024-01-01T12:00:45.000Z"
}
```

2. **Metrics Updates:**
```json
{
  "type": "metrics",
  "data": {
    "total_tasks": 150,
    "pending_tasks": 5,
    "executing_tasks": 3,
    "completed_tasks": 140,
    "failed_tasks": 2,
    "cancelled_tasks": 0,
    "running_workers": 4,
    "active_tasks": 3,
    "queue_size": 5
  },
  "timestamp": "2024-01-01T12:00:45.000Z"
}
```

## Error Responses

All endpoints return error responses in the following format:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

## Task Status Values

- `pending` - Task is queued and waiting to be processed
- `planning` - Planner agent is creating the execution plan
- `executing` - Executor agent is performing Kubernetes operations
- `completed` - Task completed successfully
- `failed` - Task failed due to an error
- `cancelled` - Task was cancelled by user request

## Priority Levels

- `low` - Low priority tasks (processed last)
- `normal` - Normal priority tasks (default)
- `high` - High priority tasks (processed before normal)
- `critical` - Critical priority tasks (processed first)

## Example Usage

### Python Client Example

```python
import requests
import json

# Submit a task
response = requests.post('http://localhost:8080/api/tasks', json={
    'request': 'Deploy nginx with 3 replicas',
    'priority': 'normal'
})

task_data = response.json()
task_id = task_data['task_id']

# Monitor task status
while True:
    response = requests.get(f'http://localhost:8080/api/tasks/{task_id}')
    status = response.json()
    
    if status['status'] in ['completed', 'failed', 'cancelled']:
        print(f"Task {status['status']}: {task_id}")
        break
    
    time.sleep(2)
```

### cURL Examples

**Submit a task:**
```bash
curl -X POST "http://localhost:8080/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{"request": "Deploy nginx with 3 replicas", "priority": "normal"}'
```

**Get task status:**
```bash
curl -X GET "http://localhost:8080/api/tasks/123e4567-e89b-12d3-a456-426614174000"
```

**List tasks:**
```bash
curl -X GET "http://localhost:8080/api/tasks?status=completed&limit=10"
```

**Get metrics:**
```bash
curl -X GET "http://localhost:8080/api/metrics"
```

## Natural Language Examples

AutoOps can understand various natural language requests for Kubernetes operations:

### Deployment Operations
- "Deploy nginx with 3 replicas"
- "Create a deployment named api-server with 5 replicas using image myapp:latest"
- "Deploy redis with persistence enabled"

### Scaling Operations
- "Scale nginx to 5 replicas"
- "Scale the api deployment to 10 replicas"
- "Increase replicas for frontend to 3"

### Service Operations
- "Create a service for nginx on port 80"
- "Expose the api deployment on port 8080"
- "Create a LoadBalancer service for the frontend"

### ConfigMap and Secret Operations
- "Create a ConfigMap named app-config with database settings"
- "Create a secret with database credentials"
- "Update the app-config ConfigMap with new values"

### Ingress Operations
- "Create an ingress for the api service with SSL"
- "Setup ingress routing for multiple services"
- "Configure ingress with custom annotations"

### Cleanup Operations
- "Delete the nginx deployment"
- "Remove all resources in the test namespace"
- "Clean up failed pods"

### Complex Operations
- "Deploy a complete LAMP stack with persistence"
- "Setup monitoring with Prometheus and Grafana"
- "Create a development environment with database and cache"

## Rate Limiting

Currently, there are no built-in rate limits, but the system is designed to handle concurrent requests efficiently through the task queue system.

## Monitoring and Observability

The API includes built-in monitoring capabilities:

- **Health checks** at `/api/health`
- **Metrics endpoint** at `/api/metrics`
- **Real-time updates** via WebSocket at `/ws`
- **OpenTelemetry tracing** for distributed tracing
- **Structured logging** for debugging and audit trails

## Security Considerations

For production deployment:

1. **Authentication**: Implement proper authentication (JWT, OAuth2, etc.)
2. **Authorization**: Add role-based access control
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Input Validation**: Validate and sanitize all inputs
5. **Network Security**: Use HTTPS and proper network policies
6. **Secrets Management**: Use Kubernetes secrets or external secret management
7. **Audit Logging**: Enable comprehensive audit logging

## Error Handling

The system includes comprehensive error handling:

- **Validation errors** for malformed requests
- **Timeout errors** for long-running operations
- **Kubernetes API errors** for cluster communication issues
- **Agent errors** for planning and execution failures
- **Retry mechanisms** for transient failures
