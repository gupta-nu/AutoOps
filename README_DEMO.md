# 🚀 AutoOps Multi-Agent Kubernetes Orchestrator

## Quick Demo Guide

Your AutoOps system is ready! Here are the different ways to demo and use it:

### 🎯 Instant Demo (No Dependencies Required)

```bash
# Run the standalone demo - works immediately
python3 standalone_demo.py
```

This shows AutoOps processing natural language requests like:
- "Create nginx deployment with 3 replicas"
- "Scale nginx deployment to 5 replicas" 
- "Create service for nginx on port 80"
- "List all pods in default namespace"

### 💻 CLI Interface Demo

```bash
# Check system health
python3 main_simple.py health

# Show version
python3 main_simple.py version

# See all available commands
python3 main_simple.py --help
```

### 🌐 Web Dashboard Demo (Requires Dependencies)

1. **Install minimal dependencies:**
   ```bash
   pip install fastapi uvicorn[standard] pydantic python-dotenv click --user
   ```

2. **Start the web server:**
   ```bash
   python3 main_simple.py serve
   ```

3. **Open your browser:**
   - **Dashboard:** http://localhost:8080/
   - **API Docs:** http://localhost:8080/docs
   - **API Explorer:** http://localhost:8080/redoc

4. **Try these natural language requests in the web interface:**
   - `Create nginx deployment with 3 replicas`
   - `Scale nginx deployment to 5 replicas`
   - `Create a service for nginx on port 80`
   - `List all deployments in default namespace`
   - `Delete deployment nginx`

### 🔧 API Demo

If the web server is running, test the API endpoints:

```bash
# Health check
curl http://localhost:8080/api/health

# Submit a task
curl -X POST http://localhost:8080/api/tasks \
     -H "Content-Type: application/json" \
     -d '{"request": "Create nginx deployment with 3 replicas"}'

# List all tasks
curl http://localhost:8080/api/tasks

# Get system metrics
curl http://localhost:8080/api/metrics
```

## 🎉 What You Just Built

Your AutoOps system includes:

✅ **Multi-Agent Architecture** - LangGraph-powered workflow orchestration  
✅ **Natural Language Processing** - Submit requests in plain English  
✅ **REST API** - Complete FastAPI server with all CRUD operations  
✅ **Web Dashboard** - Real-time interface with interactive docs  
✅ **CLI Interface** - Command-line tool for all operations  
✅ **Task Management** - Async orchestration with state tracking  
✅ **Kubernetes Integration** - Ready for real cluster operations  
✅ **Monitoring & Tracing** - Built-in observability features  
✅ **Production Ready** - Helm charts and deployment configs  

## 🚀 Production Setup

For real Kubernetes operations:

1. **Set OpenAI API Key:**
   ```bash
   echo "OPENAI_API_KEY=your_key_here" > .env
   ```

2. **Configure Kubernetes:**
   ```bash
   # Ensure kubectl is configured for your cluster
   kubectl cluster-info
   ```

3. **Install Full Dependencies:**
   ```bash
   pip install -r requirements-minimal.txt
   ```

4. **Deploy with Helm:**
   ```bash
   helm install autoops ./helm/autoops/
   ```

## 🎯 Demo Scenarios

Try these natural language requests:

**Basic Operations:**
- "Create a deployment named web-app with 3 replicas"
- "Scale the web-app deployment to 5 replicas"
- "Create a service for web-app on port 8080"

**Advanced Operations:**
- "List all pods in the production namespace"
- "Delete the deployment named old-app"
- "Create a horizontal pod autoscaler for web-app"

**Monitoring:**
- "Show me the status of all deployments"
- "Get logs from the nginx pod"
- "Check resource usage in the default namespace"

## 📂 Project Structure

```
AutoOps/
├── src/                    # Core application
│   ├── agents/            # LangGraph agents
│   ├── dashboard/         # Web interface
│   ├── kubernetes/        # K8s operations
│   └── utils/            # Task management
├── helm/                  # Deployment charts
├── tests/                 # Test suite
├── examples/              # Usage examples
├── main_simple.py         # CLI entry point
├── standalone_demo.py     # Demo script
└── README_DEMO.md        # This file
```

**🎉 Your AutoOps Multi-Agent Kubernetes Orchestrator is ready to use!**
