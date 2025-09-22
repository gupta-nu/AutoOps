#!/bin/bash
# Simple AutoOps Demo - Works with current setup

echo "🚀 AutoOps Multi-Agent Kubernetes Orchestrator - Simple Demo"
echo "============================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "main_simple.py" ]; then
    echo "❌ Please run this from the AutoOps directory"
    exit 1
fi

echo "🎯 Demo Menu:"
echo "1. 🌐 Start Web Dashboard (Recommended)"
echo "2. 💻 CLI Quick Demo"
echo "3. 🔧 API Demo"
echo ""

read -p "Choose demo (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🌐 Starting AutoOps Web Dashboard"
        echo "================================="
        echo ""
        echo "Starting server on http://localhost:8080"
        echo "Press Ctrl+C to stop when done"
        echo ""
        echo "📝 Try these tasks in the web interface:"
        echo "   • 'Create nginx deployment with 3 replicas'"
        echo "   • 'Scale nginx deployment to 5 replicas'"
        echo "   • 'Create service for nginx on port 80'"
        echo "   • 'List all pods in default namespace'"
        echo ""
        python3 main_simple.py serve
        ;;
        
    2)
        echo ""
        echo "💻 CLI Quick Demo"
        echo "=================="
        echo ""
        
        echo "1. Health Check:"
        python3 main_simple.py health
        echo ""
        
        echo "2. Available Commands:"
        python3 main_simple.py --help
        echo ""
        
        echo "✅ CLI Demo completed!"
        echo ""
        echo "📖 Try these commands yourself:"
        echo "   python3 main_simple.py health"
        echo "   python3 main_simple.py version"
        echo "   python3 main_simple.py serve"
        ;;
        
    3)
        echo ""
        echo "🔧 API Demo"
        echo "==========="
        echo ""
        echo "1. Starting server in background..."
        python3 main_simple.py serve &
        SERVER_PID=$!
        echo "   Server PID: $SERVER_PID"
        
        sleep 3
        echo ""
        echo "2. Testing API endpoints:"
        
        echo "   📊 Health Check:"
        curl -s http://localhost:8080/api/health | python3 -m json.tool || echo "Server not ready yet"
        echo ""
        
        echo "   📝 Submit Task:"
        curl -s -X POST http://localhost:8080/api/tasks \
             -H "Content-Type: application/json" \
             -d '{"request": "Create nginx deployment with 3 replicas"}' | python3 -m json.tool || echo "Server not ready yet"
        echo ""
        
        echo "   📋 List Tasks:"
        curl -s http://localhost:8080/api/tasks | python3 -m json.tool || echo "Server not ready yet"
        echo ""
        
        echo "3. Stopping server..."
        kill $SERVER_PID 2>/dev/null
        echo ""
        echo "✅ API Demo completed!"
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Demo Complete!"
echo ""
echo "🔧 What you can do next:"
echo "   1. 🌐 Open http://localhost:8080 for web dashboard"
echo "   2. 💻 Use CLI: python3 main_simple.py --help"
echo "   3. 📚 Check API docs: http://localhost:8080/docs"
echo "   4. 🚀 Set OPENAI_API_KEY for AI features"
echo ""
echo "📂 Explore the project:"
echo "   • src/ - Core application code"
echo "   • examples/ - Usage examples"
echo "   • tests/ - Test suite"
echo "   • helm/ - Kubernetes deployment"
