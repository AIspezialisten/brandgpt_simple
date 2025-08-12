#!/bin/bash

set -e

echo "🚀 BrandGPT Deployment Script"
echo "================================"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Ollama is running on host
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "❌ Ollama is not running on localhost:11434"
    echo "Please install and start Ollama first:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  ollama pull hf.co/Qwen/Qwen3-Embedding-8B-GGUF"
    echo "  ollama pull mistral-small:24b"
    exit 1
fi

echo "✅ Docker is running"
echo "✅ Ollama is accessible"

# Check required models
echo "🔍 Checking Ollama models..."
if ! curl -s http://localhost:11434/api/tags | grep -q "hf.co/Qwen/Qwen3-Embedding-8B-GGUF"; then
    echo "⚠️  Warning: Embedding model not found. Pulling hf.co/Qwen/Qwen3-Embedding-8B-GGUF..."
    ollama pull hf.co/Qwen/Qwen3-Embedding-8B-GGUF
fi

if ! curl -s http://localhost:11434/api/tags | grep -q "mistral-small"; then
    echo "⚠️  Warning: LLM model not found. Pulling mistral-small:24b..."
    ollama pull mistral-small:24b
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data
chmod 755 data

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "✏️  You can customize .env if needed"
fi

# Stop any existing services
echo "🛑 Stopping any existing services..."
docker-compose down >/dev/null 2>&1 || true

# Start services
echo "🐳 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "📋 Service Status:"
    docker-compose ps
    echo ""
    echo "🌐 Application URLs:"
    echo "  - API: http://localhost:9700"
    echo "  - Documentation: http://localhost:9700/docs"
    echo "  - Health Check: http://localhost:9700/health"
    echo ""
    echo "📊 Checking application health..."
    
    # Wait a bit more and test health endpoint
    sleep 5
    if curl -s http://localhost:9700/health | grep -q "healthy"; then
        echo "✅ Application is healthy and ready!"
    else
        echo "⚠️  Application may still be starting. Check logs with: docker-compose logs -f"
    fi
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📚 Next steps:"
    echo "  - Visit http://localhost:9700/docs to explore the API"
    echo "  - Check logs: docker-compose logs -f"
    echo "  - Stop services: docker-compose down"
    echo "  - View this deployment guide: cat DEPLOYMENT.md"
else
    echo "❌ Some services failed to start. Check logs:"
    docker-compose logs
    exit 1
fi