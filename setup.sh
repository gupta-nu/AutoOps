#!/bin/bash

# AutoOps Setup Script
# This script helps you set up the AutoOps development environment

set -e  # Exit on any error

echo "🤖 AutoOps Setup Script"
echo "======================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version is compatible"
else
    echo "❌ Python $python_version is not compatible. Please install Python 3.9 or higher"
    exit 1
fi

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs data config

# Copy environment configuration
if [ ! -f "config/.env" ]; then
    echo "⚙️  Setting up environment configuration..."
    cp config/.env.example config/.env
    echo "✅ Environment file created at config/.env"
    echo "📝 Please edit config/.env with your actual configuration values"
else
    echo "✅ Environment file already exists"
fi

# Check Docker (optional)
if command -v docker &> /dev/null; then
    echo "✅ Docker is available"
    
    # Build Docker image
    read -p "🐳 Would you like to build the Docker image? (y/n): " build_docker
    if [ "$build_docker" = "y" ] || [ "$build_docker" = "Y" ]; then
        echo "🔨 Building Docker image..."
        docker build -t autoops:latest .
        echo "✅ Docker image built successfully"
    fi
else
    echo "⚠️  Docker not found. Docker is optional but recommended for deployment"
fi

# Check kubectl (optional)
if command -v kubectl &> /dev/null; then
    echo "✅ kubectl is available"
    
    # Check cluster access
    if kubectl cluster-info &> /dev/null; then
        echo "✅ Kubernetes cluster access verified"
    else
        echo "⚠️  No Kubernetes cluster access. This is needed for full functionality"
    fi
else
    echo "⚠️  kubectl not found. This is needed for Kubernetes operations"
fi

# Check Helm (optional)
if command -v helm &> /dev/null; then
    echo "✅ Helm is available"
else
    echo "⚠️  Helm not found. This is needed for Kubernetes deployment"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit config/.env with your OpenAI API key and other settings"
echo "2. Ensure you have access to a Kubernetes cluster"
echo "3. Run the application:"
echo "   python main.py serve"
echo ""
echo "For development with auto-reload:"
echo "   python main.py serve --reload"
echo ""
echo "To run with Docker:"
echo "   docker-compose up"
echo ""
echo "To deploy to Kubernetes:"
echo "   helm install autoops ./helm/autoops"
echo ""
echo "For help and examples:"
echo "   python main.py --help"
echo "   python examples/usage_examples.py"
echo ""
echo "Happy automating! 🚀"
