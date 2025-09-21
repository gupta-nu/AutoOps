# AutoOps: Multi-Agent Kubernetes Orchestrator

A sophisticated multi-agent system that interprets natural language requests and applies changes to Kubernetes clusters through intelligent planning and execution.

## Features

- **Multi-Agent Architecture**: Planner + Executor workflow using LangGraph
- **Natural Language Interface**: Interpret and execute complex Kubernetes operations from plain English
- **OpenTelemetry Tracing**: Comprehensive monitoring of agent reasoning and actions
- **Asynchronous Orchestration**: Robust task management with error handling
- **Real-time Dashboard**: Monitor agent states and executed tasks
- **Production Ready**: Helm deployment with GPU scheduling and autoscaling

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Planner       │───▶│   Executor      │───▶│  Kubernetes     │
│   Agent         │    │   Agent         │    │  Cluster        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ OpenTelemetry   │    │  Dashboard      │    │  Monitoring     │
│ Tracing         │    │  (Real-time)    │    │  & Alerting     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.9+
- Kubernetes cluster access
- OpenAI API key
- Docker (for containerization)
- Helm (for deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/gupta-nu/AutoOps.git
cd AutoOps
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp config/.env.example config/.env
# Edit config/.env with your settings
```

4. Run the system:
```bash
python src/main.py
```

### Usage

Send natural language requests to the AutoOps system:

```python
from src.agents.orchestrator import AutoOpsOrchestrator

orchestrator = AutoOpsOrchestrator()

# Example requests
await orchestrator.process_request("Deploy a nginx pod with 3 replicas")
await orchestrator.process_request("Scale the frontend deployment to 5 replicas")
await orchestrator.process_request("Create a service for the api pods")
```

## Project Structure

```
AutoOps/
├── src/
│   ├── agents/           # LangGraph agents (Planner, Executor)
│   ├── kubernetes/       # Kubernetes API integration
│   ├── monitoring/       # OpenTelemetry tracing
│   ├── dashboard/        # Real-time web dashboard
│   └── utils/           # Utility functions
├── helm/                # Helm charts for deployment
├── config/              # Configuration files
├── tests/               # Test suites
└── docs/                # Documentation
```

## Configuration

Environment variables are managed through the `config/.env` file:

- `OPENAI_API_KEY`: OpenAI API key for LLM operations
- `KUBECONFIG_PATH`: Path to Kubernetes configuration
- `OTEL_EXPORTER_ENDPOINT`: OpenTelemetry collector endpoint
- `DASHBOARD_PORT`: Dashboard web interface port

## Development

### Running Tests

```bash
pytest tests/
```

### Development Mode

```bash
python src/main.py --dev
```

## Deployment

Deploy to Kubernetes using Helm:

```bash
helm install autoops ./helm/autoops
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
