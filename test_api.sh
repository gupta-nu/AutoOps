#!/bin/bash

echo "Testing AutoOps API..."

# Start server in background
python main.py serve --port 8080 &
SERVER_PID=$!

echo "Server PID: $SERVER_PID"
echo "Waiting for server to start..."
sleep 3

echo "Testing endpoints:"

echo "1. Health endpoint:"
curl -s http://localhost:8080/api/health || echo "Health endpoint failed"

echo -e "\n2. Root endpoint:"
curl -s http://localhost:8080/ | head -5 || echo "Root endpoint failed"

echo -e "\n3. Tasks endpoint (GET):"
curl -s http://localhost:8080/api/tasks || echo "Tasks GET endpoint failed"

echo -e "\n4. Submit task via API:"
curl -s -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"request": "Create a deployment named nginx with nginx:latest image"}' || echo "Task submission failed"

echo -e "\n5. Dashboard:"
echo "Dashboard available at: http://localhost:8080/dashboard"

echo -e "\nStopping server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo "Test complete!"
