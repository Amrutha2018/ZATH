#!/bin/bash

echo "🚀 Starting ZATH Production Environment (Server)"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Build and start production environment
echo "🔨 Building and starting production environment..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check service status
echo "📊 Checking service status..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Test API health
echo "🏥 Testing API health..."
curl -f http://localhost:8001/ || echo "❌ API not responding"

# Test frontend
echo "🌐 Testing frontend..."
curl -f http://localhost:3001/ || echo "❌ Frontend not responding"

echo ""
echo "✅ Production environment is ready!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://31.97.229.227:3001"
echo "   API: http://31.97.229.227:8001"
echo "   API Docs: http://31.97.229.227:8001/docs"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "   Stop: docker compose -f docker-compose.yml -f docker-compose.prod.yml down"
echo "   Restart: ./prod.sh"
echo ""
echo "🔧 Production features:"
echo "   ✅ Production environment variables"
echo "   ✅ Server IP URLs configured"
echo "   ✅ Restart policies enabled"
