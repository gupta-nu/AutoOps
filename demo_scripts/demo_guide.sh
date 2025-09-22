#!/bin/bash
# AutoOps Demo Guide - Interactive Demonstration
# This script will guide you through all the features of your AutoOps system

echo "🚀 AutoOps Multi-Agent Kubernetes Orchestrator - Interactive Demo"
echo "================================================================="
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Please activate your virtual environment first:"
    echo "   source venv/bin/activate"
    exit 1
fi

echo "📋 Demo Options:"
echo "1. 🌐 Web Dashboard Demo (Recommended for beginners)"
echo "2. 💻 CLI Interface Demo"
echo "3. 🔧 API Endpoints Demo"
echo "4. 🎯 Complete Full-Stack Demo"
echo ""

read -p "Choose demo type (1-4): " demo_choice

case $demo_choice in
    1)
        echo ""
        echo "🌐 Starting Web Dashboard Demo..."
        echo "================================="
        echo ""
        echo "1. Starting AutoOps server..."
        python main_simple.py &
        SERVER_PID=$!
        echo "   Server PID: $SERVER_PID"
        
        sleep 3
        echo ""
        echo "2. 🎉 Your AutoOps dashboard is now running!"
        echo ""
        echo "   🌐 Web Dashboard: http://localhost:8080/"
        echo "   📚 API Docs: http://localhost:8080/docs"
        echo "   🔍 API Explorer: http://localhost:8080/redoc"
        echo ""
        echo "3. 🎯 Try these natural language requests in the dashboard:"
        echo "   • 'Create nginx deployment with 3 replicas'"
        echo "   • 'Scale nginx deployment to 5 replicas'"
        echo "   • 'Create a service for nginx on port 80'"
        echo "   • 'List all deployments in default namespace'"
        echo "   • 'Delete deployment nginx'"
        echo ""
        echo "4. 📊 Monitor operations in real-time!"
        echo ""
        echo "Press ENTER to stop the server when done..."
        read
        kill $SERVER_PID 2>/dev/null
        echo "✅ Demo completed!"
        ;;
        
    2)
        echo ""
        echo "💻 CLI Interface Demo"
        echo "===================="
        echo ""
        echo "1. Health Check:"
        python main_simple.py health
        echo ""
        
        echo "2. Submit a task:"
        echo "   Command: python main_simple.py task 'Create nginx deployment with 3 replicas'"
        python main_simple.py task "Create nginx deployment with 3 replicas"
        echo ""
        
        echo "3. List tasks:"
        python main_simple.py list
        echo ""
        
        echo "4. Try more commands:"
        echo "   python main_simple.py task 'Scale nginx to 5 replicas'"
        echo "   python main_simple.py task 'Create service for nginx on port 80'"
        echo "   python main_simple.py task 'List all pods'"
        echo ""
        echo "✅ CLI Demo completed!"
        ;;
        
    3)
        echo ""
        echo "🔧 API Endpoints Demo"
        echo "===================="
        echo ""
        echo "1. Starting server for API testing..."
        python main_simple.py &
        SERVER_PID=$!
        sleep 3
        
        echo "2. Testing API endpoints:"
        echo ""
        
        echo "   📊 Health Check:"
        curl -s http://localhost:8080/api/health | python -m json.tool
        echo ""
        
        echo "   📝 Submit Task:"
        curl -s -X POST http://localhost:8080/api/tasks \
             -H "Content-Type: application/json" \
             -d '{"request": "Create nginx deployment with 3 replicas"}' | python -m json.tool
        echo ""
        
        echo "   📋 List Tasks:"
        curl -s http://localhost:8080/api/tasks | python -m json.tool
        echo ""
        
        echo "   📈 System Metrics:"
        curl -s http://localhost:8080/api/metrics | python -m json.tool
        echo ""
        
        kill $SERVER_PID 2>/dev/null
        echo "✅ API Demo completed!"
        ;;
        
    4)
        echo ""
        echo "🎯 Complete Full-Stack Demo"
        echo "==========================="
        echo ""
        echo "This will run the comprehensive demo script..."
        ./complete_demo.sh
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Demo Complete!"
echo ""
echo "🔧 Next Steps for Production:"
echo "   1. Set OPENAI_API_KEY in .env file for AI-powered processing"
echo "   2. Configure kubectl for your Kubernetes cluster"
echo "   3. Deploy with: helm install autoops ./helm/autoops/"
echo ""
echo "📖 More Examples:"
echo "   • Check examples/ directory for sample requests"
echo "   • Read README.md for detailed documentation"
echo "   • Run tests with: python -m pytest tests/"
