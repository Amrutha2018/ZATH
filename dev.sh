#!/bin/bash

echo "🖥️  Starting ZATH Development Environment (Mac)"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Build and start development environment
echo "🔨 Building and starting development environment..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps

# Test API health
echo "🏥 Testing API health..."
curl -f http://localhost:8001/ || echo "❌ API not responding"

# Test frontend
echo "🌐 Testing frontend..."
curl -f http://localhost:3001/ || echo "❌ Frontend not responding"

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://localhost:3001"
echo "   API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
echo "   Stop: docker compose -f docker-compose.yml -f docker-compose.dev.yml down"
echo "   Restart: ./dev.sh"
echo ""
echo "🔧 Development features:"
echo "   ✅ Hot reload enabled"
echo "   ✅ Volume mounts for live code changes"
echo "   ✅ Localhost URLs for easy development"
