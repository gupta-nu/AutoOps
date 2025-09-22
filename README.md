# AutoOps: Multi-Agent Kubernetes Orchestrator

A  multi-agent system that interprets natural language requests and applies changes to Kubernetes clusters through intelligent planning and execution. Built with LangGraph for advanced agent workflows and FastAPI for modern web interfaces.

## Features

- **Multi-Agent Architecture**: Planner + Executor workflow using LangGraph with advanced state management
- **Natural Language Interface**: Process complex Kubernetes operations from plain English commands
- **Comprehensive Monitoring**: Built-in tracing, metrics collection, and real-time observability
- **Multiple Interfaces**: CLI, REST API, WebSocket dashboard, and standalone demo modes
- **Asynchronous Orchestration**: Robust task management with error handling and progress tracking
- **Real-time Dashboard**: Interactive web interface with live updates and task monitoring
- **Production Ready**: Helm charts, Docker containers, autoscaling, and comprehensive deployment configs
- **Developer Friendly**: Simplified setup, zero-dependency demo, and extensive documentation

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   🧠 Planner    │───▶│  ⚙️ Executor     │───▶│  ☸️ Kubernetes  │
│   Agent         │    │   Agent         │    │   Cluster       │
│  (LangGraph)    │    │  (LangGraph)    │    │   Operations    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 📈 Monitoring   │    │  🖥️ Dashboard    │    │  🔍 Task        │
│ & Tracing       │    │  (FastAPI)      │    │  Management     │
│ (OpenTelemetry) │    │  + WebSocket    │    │  + CLI          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Overview

- **Planner Agent**: Interprets natural language and creates execution plans
- **Executor Agent**: Implements plans through Kubernetes API operations  
- **Task Manager**: Handles async operations with progress tracking and error recovery
- **Web Dashboard**: Real-time monitoring with WebSocket updates and interactive controls
- **CLI Interface**: Command-line access for automation and scripting
- **Monitoring System**: Comprehensive observability with tracing and metrics

## Quick Start

### Option 1: Zero-Dependency Demo (Fastest)

Experience AutoOps without any setup:

```bash
# Clone and run standalone demo
git clone https://github.com/gupta-nu/AutoOps.git
cd AutoOps
python standalone_demo.py
```

### Option 2: Simple Setup (Recommended)

Get started quickly with minimal dependencies:

```bash
# Clone repository
git clone https://github.com/gupta-nu/AutoOps.git
cd AutoOps

# Install minimal dependencies
pip install fastapi uvicorn

# Run simplified version
python main_simple.py

# Access dashboard at http://localhost:8000
```

### Option 3: Full Installation (Production)

Complete setup with all features:

```bash
# Install all dependencies
pip install -r requirements.txt

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your settings:
# - OPENAI_API_KEY=your_openai_key
# - KUBECONFIG_PATH=~/.kube/config

# Run full system
python src/main.py
```

### Prerequisites

**Minimal Setup:**
- Python 3.9+

**Full Setup:**
- Python 3.9+
- Kubernetes cluster access (for real operations)
- OpenAI API key (for LLM features)
- Docker (for containerization)
- Helm (for deployment)

## Usage Examples

###  Web Dashboard
```bash
# Start the dashboard
python main_simple.py

# Open browser to http://localhost:8000
# Use the interactive interface for real-time monitoring
```

###  Command Line Interface
```bash
# Process natural language requests via main interfaces
python main_simple.py

# Or use full system CLI
python src/main.py "Deploy nginx with 3 replicas" 
python src/main.py "Scale frontend to 5 pods"

# Check system status
python main_simple.py health

# Access web dashboard
python main_simple.py serve
```

###  REST API
```bash
# Submit tasks via API
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"request": "Deploy redis with persistent storage"}'

# Check system health
curl http://localhost:8000/api/health

# Get metrics
curl http://localhost:8000/api/metrics
```

###  Python Integration
```python
from src.agents.orchestrator import AutoOpsOrchestrator

# Initialize orchestrator
orchestrator = AutoOpsOrchestrator()

# Process requests
result = await orchestrator.process_request(
    "Deploy a nginx pod with 3 replicas and expose it via LoadBalancer"
)

# Check result
print(f"Status: {result.status}")
print(f"Actions: {result.actions}")
```

###  Demo Scenarios
```bash
# Run comprehensive demo
bash demo_scripts/complete_demo.sh

# Quick demo
bash demo_scripts/simple_demo.sh

# Interactive demo guide
bash demo_scripts/demo_guide.sh

# Standalone demo (no dependencies)
python standalone_demo.py
```

## Project Structure

```
AutoOps/
├──Core Components
│   ├── src/
│   │   ├── agents/              # LangGraph multi-agent system
│   │   │   ├── orchestrator.py  # Main orchestration logic
│   │   │   ├── planner.py      # Planning agent implementation
│   │   │   └── executor.py     # Execution agent implementation
│   │   ├── kubernetes/         # Kubernetes API integration
│   │   │   ├── client.py       # Simplified K8s client
│   │   │   └── operations.py   # K8s operations wrapper
│   │   ├── monitoring/         # Observability & tracing
│   │   │   ├── tracing.py      # Simplified OpenTelemetry
│   │   │   └── metrics.py      # Custom metrics collection
│   │   ├── dashboard/          # FastAPI web interface
│   │   │   ├── api.py          # REST API endpoints
│   │   │   ├── websocket.py    # Real-time updates
│   │   │   └── static/         # Web UI assets
│   │   ├── tasks/              # Task management system
│   │   │   └── manager.py      # Async task handling
│   │   └── utils/              # Utility functions
│   │       ├── config.py       # Configuration management
│   │       └── logging.py      # Logging setup
│
├── Entry Points
│   ├── main_simple.py          # Simplified startup (recommended)
│   ├── standalone_demo.py      # Zero-dependency demo
│   └── src/main.py            # Full system startup
│
├── Deployment
│   └── helm/                  # Helm charts for K8s deployment
│       └── autoops/          # Complete Helm chart
│
├──Testing & Demos
│   ├── tests/                # Test suite
│   │   └── test_agents.py   # Agent testing
│   ├── demo_scripts/        # Demo automation scripts
│   │   ├── simple_demo.sh   # Quick demo
│   │   ├── complete_demo.sh # Full feature demo
│   │   └── demo_guide.sh    # Interactive demo guide
│   ├── standalone_demo.py   # Zero-dependency demo
│   └── examples/            # Usage examples
│
├── Configuration & Docs
│   ├── config/              # Configuration files
│   │   ├── .env.example     # Environment template
│   │   ├── settings.py      # Core settings
│   │   └── settings_simple.py # Simplified settings
│   ├── docs/               # Documentation
│   │   └── API.md          # API documentation
│   ├── README.md           # Main documentation (this file)
│   └── requirements.txt    # Python dependencies
```

## Configuration

### Environment Variables

Configure AutoOps through the `config/.env` file:

```bash
# Core Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
KUBECONFIG_PATH=~/.kube/config
ENVIRONMENT=development

# Dashboard Settings
DASHBOARD_PORT=8000
DASHBOARD_HOST=0.0.0.0
ENABLE_WEBSOCKET=true

# Monitoring & Tracing
ENABLE_TRACING=true
OTEL_EXPORTER_ENDPOINT=http://localhost:4318
LOG_LEVEL=INFO

# Task Management
MAX_CONCURRENT_TASKS=10
TASK_TIMEOUT=300
ENABLE_TASK_PERSISTENCE=true

# Kubernetes Settings
K8S_NAMESPACE=default
K8S_TIMEOUT=60
DRY_RUN=false
```

### Configuration Files

- `config/.env`: Environment variables and secrets
- `config/settings.py`: Core application settings
- `config/settings_simple.py`: Simplified configuration
- `helm/autoops/values.yaml`: Helm deployment values

### Runtime Configuration

```python
# Programmatic configuration
from src.utils.config import Config

config = Config()
config.set('dashboard.port', 8080)
config.set('k8s.dry_run', True)
```

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/gupta-nu/AutoOps.git
cd AutoOps

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements.txt
# Note: requirements-dev.txt will be created for additional dev tools

# Set up pre-commit hooks (if available)
# pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/e2e/           # End-to-end tests only

# Run with coverage
pytest --cov=src --cov-report=html

# Run tests with live logging
pytest -s --log-cli-level=INFO
```

### Development Modes

```bash
# Development mode with auto-reload
python src/main.py --dev

# Debug mode with verbose logging
python src/main.py --debug

# Dry-run mode (no actual K8s operations)
python src/main.py --dry-run

# Simplified mode for testing
python main_simple.py --dev
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
pylint src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

### Building and Testing

```bash
# Build Docker image
docker build -t autoops:dev .

# Run integration tests with Docker (if docker-compose.yml exists)
docker-compose up -d
pytest tests/

# Test Helm chart
helm template ./helm/autoops --debug
helm install autoops-test ./helm/autoops --dry-run
```

## Deployment

### Local Development

```bash
# Using Docker Compose (if docker-compose.yml exists)
docker-compose up

# Using local Python
python main_simple.py
```

### Kubernetes Deployment

#### Option 1: Helm (Recommended)

```bash
# Add dependencies
helm dependency update ./helm/autoops

# Install with default values
helm install autoops ./helm/autoops

# Install with custom values
helm install autoops ./helm/autoops \
  --set image.tag=latest \
  --set config.openaiApiKey=sk-your-key \
  --set ingress.enabled=true

# Upgrade deployment
helm upgrade autoops ./helm/autoops

# Uninstall
helm uninstall autoops
```

#### Option 2: Raw Kubernetes Manifests (To be created)

```bash
# Create Kubernetes manifests based on Helm templates
helm template autoops ./helm/autoops > k8s-manifests.yaml

# Apply the generated manifests
kubectl apply -f k8s-manifests.yaml
```

### Production Configuration

```yaml
# helm/autoops/values.yaml
image:
  tag: "v1.0.0"
  pullPolicy: Always

config:
  environment: production
  logLevel: INFO
  enableTracing: true

resources:
  requests:
    memory: 512Mi
    cpu: 250m
  limits:
    memory: 1Gi
    cpu: 500m

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: autoops.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: autoops-tls
      hosts:
        - autoops.example.com
```

### Monitoring & Observability

```bash
# Deploy monitoring stack
helm install prometheus prometheus-community/kube-prometheus-stack
helm install jaeger jaegertracing/jaeger

# Configure AutoOps to use monitoring
export OTEL_EXPORTER_ENDPOINT=http://jaeger-collector:14268
export PROMETHEUS_ENDPOINT=http://prometheus-server:9090
```

### Scaling & Performance

```bash
# Horizontal scaling
kubectl scale deployment autoops --replicas=5

# Vertical scaling (update resources)
kubectl patch deployment autoops -p '{"spec":{"template":{"spec":{"containers":[{"name":"autoops","resources":{"requests":{"memory":"1Gi","cpu":"500m"}}}]}}}}'

# Enable cluster autoscaling (requires cluster autoscaler setup)
# kubectl apply -f k8s/cluster-autoscaler.yaml
```

## API Reference

### REST API Endpoints

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/api/health` | GET | System health check | `curl http://localhost:8000/api/health` |
| `/api/tasks` | GET | List all tasks | `curl http://localhost:8000/api/tasks` |
| `/api/tasks` | POST | Submit new task | `curl -X POST -H "Content-Type: application/json" -d '{"request":"deploy nginx"}' http://localhost:8000/api/tasks` |
| `/api/tasks/{id}` | GET | Get task details | `curl http://localhost:8000/api/tasks/123` |
| `/api/tasks/{id}` | DELETE | Cancel task | `curl -X DELETE http://localhost:8000/api/tasks/123` |
| `/api/metrics` | GET | System metrics | `curl http://localhost:8000/api/metrics` |
| `/api/agents/status` | GET | Agent status | `curl http://localhost:8000/api/agents/status` |

### WebSocket API

```javascript
// Connect to real-time updates
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Task update:', data);
};

// Send task via WebSocket
ws.send(JSON.stringify({
    type: 'task',
    request: 'Deploy postgres with persistent volume'
}));
```

### CLI Commands

```bash
# Basic usage through main interfaces
python main_simple.py serve                    # Start web server
python main_simple.py health                   # Check health
python src/main.py "deploy nginx with 3 replicas"  # Submit request

# Task management (via web interface at /api/tasks)
curl http://localhost:8000/api/tasks           # List all tasks
curl http://localhost:8000/api/health          # Show system status

# Configuration
python -c "from src.utils.config import Config; print(Config().get_all())"  # Show configuration
```

## Troubleshooting

### Common Issues

#### 1. Connection Issues
```bash
# Check Kubernetes connectivity
kubectl cluster-info
kubectl get nodes

# Verify AutoOps can connect
python -c "from src.kubernetes.client import KubernetesClient; print(KubernetesClient().health_check())"
```

#### 2. OpenAI API Issues
```bash
# Verify API key
export OPENAI_API_KEY=your-key-here
python -c "import openai; print(openai.Model.list())"

# Use alternative LLM
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your-key-here
```

#### 3. Dashboard Not Loading
```bash
# Check if service is running
curl http://localhost:8000/api/health

# Check logs
python main_simple.py --debug

# Try different port
python main_simple.py --port 8080
```

#### 4. Task Execution Failures
```bash
# Check task logs via API
curl http://localhost:8000/api/tasks/<task-id>

# Enable dry-run mode
export DRY_RUN=true
python src/main.py "your command here"

# Validate Kubernetes permissions
kubectl auth can-i create pods
kubectl auth can-i create deployments
```

### Performance Optimization

#### Memory Usage
```bash
# Monitor memory usage
docker stats autoops

# Reduce memory footprint
export MAX_CONCURRENT_TASKS=5
export ENABLE_TASK_PERSISTENCE=false
```

#### Response Time
```bash
# Enable caching
export ENABLE_CACHE=true
export CACHE_TTL=300

# Use local LLM
export LLM_PROVIDER=local
export LOCAL_LLM_ENDPOINT=http://localhost:11434
```

### Debugging

#### Enable Debug Logging
```bash
# Environment variable
export LOG_LEVEL=DEBUG

# Command line
python src/main.py --debug

# Configuration file
echo "LOG_LEVEL=DEBUG" >> config/.env
```

#### Trace Requests
```bash
# Enable detailed tracing
export ENABLE_DETAILED_TRACING=true

# View traces in Jaeger
# Open http://localhost:16686
```

## FAQ

**Q: Can AutoOps work without OpenAI?**
A: Yes! Use the standalone demo (`python standalone_demo.py`) or configure alternative LLM providers.

**Q: Is it safe to use in production?**
A: AutoOps includes safety features like dry-run mode, input validation, and RBAC. Always test in staging first.

**Q: Can I extend AutoOps with custom agents?**
A: Absolutely! The LangGraph architecture makes it easy to add new agents. Check the source code in `src/agents/` for examples.

**Q: How do I backup task history?**
A: Task data is stored in the configured database. Enable `ENABLE_TASK_PERSISTENCE=true` and backup the data directory.

**Q: Can AutoOps manage multiple clusters?**
A: Yes, configure multiple kubeconfig contexts and specify them in requests: "deploy to staging cluster".

## Contributing

We welcome contributions! Here's how to get started:

### 1. Development Setup
```bash
git clone https://github.com/gupta-nu/AutoOps.git
cd AutoOps
pip install -r requirements.txt
# Additional dev tools can be installed as needed
```

### 2. Making Changes
- Create a feature branch: `git checkout -b feature/your-feature`
- Write tests for new functionality
- Ensure all tests pass: `pytest`
- Follow code style: `black . && isort . && flake8`

### 3. Submitting Changes
- Push branch: `git push origin feature/your-feature`
- Create Pull Request with detailed description
- Address review feedback
- Ensure CI passes

## License

MIT License - see [LICENSE](LICENSE) file for details.


## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for the multi-agent framework
- [FastAPI](https://fastapi.tiangolo.com/) for the modern web framework
- [Kubernetes Python Client](https://github.com/kubernetes-client/python) for cluster integration
- [OpenTelemetry](https://opentelemetry.io/) for observability standards

---

**AutoOps** - Bringing natural language to Kubernetes operations 🚀
