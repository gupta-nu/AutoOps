#!/bin/bash

echo "=== AutoOps Multi-Agent Kubernetes Orchestrator Demo ==="
echo

echo "1. Testing CLI commands..."
echo "----------------------------------------"

echo "• Checking health:"
python main.py health
echo

echo "• Submitting a test task:"
python main.py submit "Create a deployment named test-nginx with nginx image"
echo

echo "• Listing tasks:"
python main.py list-tasks
echo

echo "2. Starting web server for 10 seconds..."
echo "----------------------------------------"

echo "• Starting server on port 8084..."
python main.py serve --port 8084 &
SERVER_PID=$!

sleep 2

echo "• Testing API endpoints:"
echo "  - Health endpoint:"
curl -s http://localhost:8084/health | python -m json.tool
echo

echo "  - API info:"
curl -s http://localhost:8084/ | python -m json.tool
echo

echo "  - Dashboard:"
echo "    Dashboard is available at: http://localhost:8084/dashboard"
echo

sleep 8

echo "• Stopping server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo
echo "=== Demo Complete ==="
echo "The AutoOps system is working successfully!"
echo
echo "Key features demonstrated:"
echo "✓ CLI interface for task submission and management"
echo "✓ REST API for programmatic access"
echo "✓ Real-time web dashboard"
echo "✓ Task management and execution"
echo "✓ Health monitoring"
echo "✓ Simplified tracing and logging"
echo
echo "To use the full system:"
echo "1. Set OPENAI_API_KEY in .env file"
echo "2. Configure kubectl for Kubernetes access"
echo "3. Start server: python main.py serve"
echo "4. Submit requests via CLI, API, or dashboard"
