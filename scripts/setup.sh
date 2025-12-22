#!/bin/bash
set -e

echo "🚀 WAOOAW Platform Setup"
echo "========================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

echo "✅ Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker Compose found"

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env file..."
    cat > backend/.env << 'ENV_EOF'
# Database
DATABASE_URL=postgresql://waooaw:waooaw_dev_password@postgres:5432/waooaw_db

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENV=development
DEBUG=true

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=dev_secret_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# API Keys (Add your keys here)
# OPENAI_API_KEY=your_key_here
ENV_EOF
    echo "✅ Created backend/.env"
else
    echo "✅ backend/.env already exists"
fi

# Install backend dependencies (if running locally)
if command -v python3 &> /dev/null; then
    echo "📦 Installing Python dependencies..."
    cd backend
    python3 -m pip install -r requirements.txt -r requirements-dev.txt --quiet
    cd ..
    echo "✅ Python dependencies installed"
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose -f infrastructure/docker/docker-compose.yml up -d

echo ""
echo "✅ WAOOAW Platform is starting!"
echo ""
echo "📍 Services:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/docs"
echo "   Adminer:   http://localhost:8081"
echo ""
echo "📊 Check logs: docker-compose -f infrastructure/docker/docker-compose.yml logs -f"
echo "🛑 Stop:       docker-compose -f infrastructure/docker/docker-compose.yml down"
echo ""
