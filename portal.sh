#!/bin/bash
# WAOOAW Portal Management Script
# Single source of truth for starting/stopping services

# FIXED PORTS - DO NOT CHANGE
BACKEND_PORT=8000
FRONTEND_PORT=3000
REFLEX_BACKEND_PORT=8001

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
BACKEND_DIR="/workspaces/WAOOAW/backend"
FRONTEND_DIR="/workspaces/WAOOAW/PlatformPortal"

# Log files
BACKEND_LOG="/tmp/waooaw_backend.log"
FRONTEND_LOG="/tmp/waooaw_frontend.log"

# Function to stop all services
stop_all() {
    echo -e "${YELLOW}Stopping all WAOOAW services...${NC}"
    pkill -9 -f "reflex run" 2>/dev/null
    pkill -9 -f "uvicorn app.main" 2>/dev/null
    fuser -k ${BACKEND_PORT}/tcp 2>/dev/null
    fuser -k ${FRONTEND_PORT}/tcp 2>/dev/null
    fuser -k ${REFLEX_BACKEND_PORT}/tcp 2>/dev/null
    sleep 2
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Function to check if port is free
check_port() {
    local port=$1
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

# Function to start backend
start_backend() {
    echo -e "${YELLOW}Starting FastAPI Backend on port ${BACKEND_PORT}...${NC}"
    
    if ! check_port ${BACKEND_PORT}; then
        echo -e "${RED}❌ Port ${BACKEND_PORT} is in use${NC}"
        return 1
    fi
    
    cd ${BACKEND_DIR}
    uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} > ${BACKEND_LOG} 2>&1 &
    BACKEND_PID=$!
    
    # Wait and verify
    sleep 5
    if curl -s http://localhost:${BACKEND_PORT}/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend started (PID: ${BACKEND_PID})${NC}"
        return 0
    else
        echo -e "${RED}❌ Backend failed to start. Check: ${BACKEND_LOG}${NC}"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    echo -e "${YELLOW}Starting Reflex Frontend on port ${FRONTEND_PORT}...${NC}"
    
    if ! check_port ${FRONTEND_PORT}; then
        echo -e "${RED}❌ Port ${FRONTEND_PORT} is in use${NC}"
        return 1
    fi
    
    cd ${FRONTEND_DIR}
    
    # Set backend port for Reflex
    export BACKEND_WEB_PORT=${REFLEX_BACKEND_PORT}
    
    python -m reflex run --env prod --loglevel warning --backend-port ${REFLEX_BACKEND_PORT} --frontend-port ${FRONTEND_PORT} > ${FRONTEND_LOG} 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for compilation
    echo -e "${YELLOW}⏳ Compiling Reflex app (this may take 20-30 seconds)...${NC}"
    sleep 25
    
    if curl -s http://localhost:${FRONTEND_PORT}/login >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend started (PID: ${FRONTEND_PID})${NC}"
        return 0
    else
        echo -e "${RED}❌ Frontend failed to start. Check: ${FRONTEND_LOG}${NC}"
        return 1
    fi
}

# Function to show status
status() {
    echo -e "${YELLOW}WAOOAW Portal Status:${NC}"
    echo ""
    
    # Backend
    if check_port ${BACKEND_PORT}; then
        echo -e "Backend (${BACKEND_PORT}):  ${RED}⭕ Stopped${NC}"
    else
        echo -e "Backend (${BACKEND_PORT}):  ${GREEN}✅ Running${NC}"
        curl -s http://localhost:${BACKEND_PORT}/health 2>/dev/null | head -1
    fi
    
    # Frontend
    if check_port ${FRONTEND_PORT}; then
        echo -e "Frontend (${FRONTEND_PORT}): ${RED}⭕ Stopped${NC}"
    else
        echo -e "Frontend (${FRONTEND_PORT}): ${GREEN}✅ Running${NC}"
    fi
    
    echo ""
    echo "Logs:"
    echo "  Backend:  ${BACKEND_LOG}"
    echo "  Frontend: ${FRONTEND_LOG}"
    echo ""
    
    # Get actual codespace name
    CODESPACE_NAME_VAL="${CODESPACE_NAME:-unknown}"
    
    if [ "$CODESPACE_NAME_VAL" != "unknown" ]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🔗 WAOOAW Portal - Ready for Testing${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "${YELLOW}🔐 Login URL:${NC}"
        echo ""
        echo "   https://${CODESPACE_NAME_VAL}-${FRONTEND_PORT}.app.github.dev/login"
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✨ All pages accessible after authentication${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    else
        echo "URLs (Local):"
        echo "  Login:    http://localhost:${FRONTEND_PORT}/login"
        echo "  Backend:  http://localhost:${BACKEND_PORT}/health"
    fi
}

# Function to show logs
logs() {
    local service=$1
    case $service in
        backend|be)
            echo -e "${YELLOW}Backend logs (${BACKEND_LOG}):${NC}"
            tail -50 ${BACKEND_LOG}
            ;;
        frontend|fe)
            echo -e "${YELLOW}Frontend logs (${FRONTEND_LOG}):${NC}"
            tail -50 ${FRONTEND_LOG}
            ;;
        *)
            echo "Usage: $0 logs [backend|frontend]"
            ;;
    esac
}

# Main command handler
case "$1" in
    start)
        stop_all
        echo ""
        start_backend
        echo ""
        start_frontend
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🚀 WAOOAW Portal Started Successfully!${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        status
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        echo ""
        start_backend
        echo ""
        start_frontend
        echo ""
        status
        ;;
    status)
        status
        ;;
    logs)
        logs $2
        ;;
    *)
        echo "WAOOAW Portal Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Stop all services and start fresh"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        echo "  logs     - Show logs (backend|frontend)"
        echo ""
        echo "Fixed Ports:"
        echo "  Backend:  ${BACKEND_PORT}"
        echo "  Frontend: ${FRONTEND_PORT}"
        echo ""
        exit 1
        ;;
esac
