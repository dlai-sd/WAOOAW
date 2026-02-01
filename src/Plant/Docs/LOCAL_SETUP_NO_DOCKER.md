# Local Setup (No Docker)

## Deprecated: Docker-only repository

WAOOAW is Docker-first (Docker-only). This document is intentionally deprecated to avoid accidental virtualenv/local-Python setups.

Use Docker Compose instead:

- `docker compose -f docker-compose.local.yml up --build`

If you need a special no-Docker workflow, please request it explicitly and we can design a supported path.


# Local Setup Without Docker

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (installed locally or remote)
- Redis (optional, can use fake Redis for testing)

## Quick Setup Steps

### 1. Install PostgreSQL (if not installed)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
Download from: https://www.postgresql.org/download/windows/

### 2. Create Database

```bash
# Access PostgreSQL
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE waooaw_db;
CREATE USER waooaw WITH PASSWORD 'waooaw_dev_password';
GRANT ALL PRIVILEGES ON DATABASE waooaw_db TO waooaw;
\q
```

### 3. Install Redis (Optional)

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Skip Redis:** Set `REDIS_URL=redis://fake` in environment

### 4. Set Up Plant Backend

```bash
cd /workspaces/WAOOAW/src/Plant/BackEnd

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://waooaw:waooaw_dev_password@localhost:5432/waooaw_db"
export REDIS_URL="redis://localhost:6379/0"
export PORT=8001
export ENVIRONMENT=development

# Run migrations (if any)
# alembic upgrade head

# Start server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 5. Set Up Plant Gateway (separate terminal)

```bash
cd /workspaces/WAOOAW/src/Plant/Gateway

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PLANT_BACKEND_URL="http://localhost:8001"
export REDIS_URL="redis://localhost:6379/1"
export PORT=8000
export ENVIRONMENT=development

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Set Up PP Backend (separate terminal)

```bash
cd /workspaces/WAOOAW/src/PP/BackEnd

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://waooaw:waooaw_dev_password@localhost:5432/waooaw_db"
export REDIS_URL="redis://localhost:6379/2"
export PORT=8015
export PLANT_GATEWAY_URL="http://localhost:8000"
export ENVIRONMENT=development

# Start server
uvicorn main:app --host 0.0.0.0 --port 8015 --reload
```

## Test URLs (After All Services Start)

| Service | URL | Test Command |
|---------|-----|--------------|
| Plant Backend | http://localhost:8001/docs | `curl http://localhost:8001/health` |
| Plant Gateway | http://localhost:8000/docs | `curl http://localhost:8000/health` |
| PP Backend | http://localhost:8015/docs | `curl http://localhost:8015/health` |

## Simplified Script (Run All in Background)

Create `start-local.sh`:

```bash
#!/bin/bash

# Start Plant Backend
cd src/Plant/BackEnd
source venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://waooaw:waooaw_dev_password@localhost:5432/waooaw_db"
export REDIS_URL="redis://localhost:6379/0"
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
PLANT_PID=$!
cd ../../..

# Start Plant Gateway
cd src/Plant/Gateway
source venv/bin/activate
export PLANT_BACKEND_URL="http://localhost:8001"
export REDIS_URL="redis://localhost:6379/1"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
GATEWAY_PID=$!
cd ../../..

# Start PP Backend
cd src/PP/BackEnd
source venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://waooaw:waooaw_dev_password@localhost:5432/waooaw_db"
export REDIS_URL="redis://localhost:6379/2"
export PLANT_GATEWAY_URL="http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8015 --reload &
PP_PID=$!
cd ../../..

echo "Services started:"
echo "Plant Backend: PID $PLANT_PID - http://localhost:8001"
echo "Plant Gateway: PID $GATEWAY_PID - http://localhost:8000"
echo "PP Backend: PID $PP_PID - http://localhost:8015"
echo ""
echo "To stop all: kill $PLANT_PID $GATEWAY_PID $PP_PID"
```

Make it executable:
```bash
chmod +x start-local.sh
./start-local.sh
```

## Stop Services

```bash
# Find processes
ps aux | grep uvicorn

# Kill by port
lsof -ti:8001 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:8015 | xargs kill -9
```

## Troubleshooting

### Port Already in Use
```bash
# Find what's using the port
lsof -i :8001
# Kill it
kill -9 <PID>
```

### Database Connection Error
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list  # macOS

# Test connection
psql -U waooaw -d waooaw_db -h localhost
```

### Module Not Found
```bash
# Ensure you're in virtual environment
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

## Development Tips

- Keep 3-4 terminals open (one per service + one for commands)
- Use `tmux` or `screen` for session management
- Check logs in each terminal for errors
- Services auto-reload on code changes (--reload flag)
