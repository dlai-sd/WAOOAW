#!/bin/bash
# Install token alias (if present) so GH_TOKEN/GITHUB_TOKEN are available in shells.
if [ -f ".devcontainer/00-token-alias.sh" ]; then
    install -m 0755 .devcontainer/00-token-alias.sh /etc/profile.d/00-waooaw-token-alias.sh
fi

set -e

echo "🚀 WAOOAW Development Environment Setup"
echo ""

# Update package manager
echo "📦 Updating system packages..."
apt-get update -qq

# Install essential development tools
echo "📦 Installing development tools..."
apt-get install -y -qq \
    build-essential \
    curl \
    wget \
    vim \
    git \
    jq \
    tree \
    postgresql-client \
    libpq-dev \
    && echo "✅ System packages installed"

# Install Python development tools
echo "📦 Installing Python tools..."
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet \
    poetry \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    && echo "✅ Python tools installed"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ WAOOAW Development Environment Ready!                      ║"
echo "║  - Python 3.11                                                 ║"
echo "║  - Docker-in-Docker enabled                                   ║"
echo "║  - PostgreSQL client installed (for docker-compose)           ║"
echo "║  - Development tools installed                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Verify: python --version  (should show Python 3.11.x)"
echo "2. Verify: docker --version  (Docker enabled)"
echo "3. Start services: docker-compose -f docker-compose.dev.yml up -d"
echo "4. Install backend: pip install -r src/Plant/BackEnd/requirements.txt"
echo "5. Run backend: uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "💡 Use Docker Compose for PostgreSQL, Redis, and other services"
echo ""
