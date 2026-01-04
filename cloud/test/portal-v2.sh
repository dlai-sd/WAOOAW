#!/bin/bash
# WAOOAW Platform Portal v2 - Codespace Management Script
# Single source of truth for starting/stopping v2 services in GitHub Codespaces

# FIXED PORTS - DO NOT CHANGE
BACKEND_PORT=8000
PP_BACKEND_PORT=3000
PP_FRONTEND_PORT=3001

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directories
BACKEND_DIR="/workspaces/WAOOAW/WaooawPortal/backend"
PLATFORM_PORTAL_DIR="/workspaces/WAOOAW/PlatformPortal"

# Log files
BACKEND_LOG="/tmp/waooaw_backend_v2.log"
PLATFORM_PORTAL_LOG="/tmp/waooaw_platform_portal_v2.log"

# Function to stop all services
stop_all() {
    echo -e "${YELLOW}Stopping all WAOOAW v2 services...${NC}"
    pkill -9 -f "reflex run" 2>/dev/null
    pkill -9 -f "uvicorn app.main" 2>/dev/null
    fuser -k ${BACKEND_PORT}/tcp 2>/dev/null
    fuser -k ${PP_BACKEND_PORT}/tcp 2>/dev/null
    fuser -k ${PP_FRONTEND_PORT}/tcp 2>/dev/null
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
    echo -e "${YELLOW}Starting FastAPI Backend v2 on port ${BACKEND_PORT}...${NC}"
    
    if ! check_port ${BACKEND_PORT}; then
        echo -e "${RED}❌ Port ${BACKEND_PORT} is in use${NC}"
        return 1
    fi
    
    cd ${BACKEND_DIR}
    
    # Load environment variables from .env.local
    if [ -f .env.local ]; then
        export $(cat .env.local | xargs)
        echo -e "${CYAN}   Loaded .env.local${NC}"
    fi
    
    # Activate virtual environment if exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${CYAN}   Activated virtual environment${NC}"
    fi
    
    nohup uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload > ${BACKEND_LOG} 2>&1 &
    BACKEND_PID=$!
    
    # Wait and verify
    sleep 5
    if curl -s http://localhost:${BACKEND_PORT}/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend started (PID: ${BACKEND_PID})${NC}"
        curl -s http://localhost:${BACKEND_PORT}/health | head -1
        return 0
    else
        echo -e "${RED}❌ Backend failed to start. Check: ${BACKEND_LOG}${NC}"
        return 1
    fi
}

# Function to start Platform Portal v2
start_platform_portal() {
    echo -e "${YELLOW}Starting Platform Portal v2 (Reflex)...${NC}"
    echo -e "${CYAN}   Backend: port ${PP_BACKEND_PORT}${NC}"
    echo -e "${CYAN}   Frontend: port ${PP_FRONTEND_PORT}${NC}"
    
    if ! check_port ${PP_BACKEND_PORT}; then
        echo -e "${RED}❌ Port ${PP_BACKEND_PORT} is in use${NC}"
        return 1
    fi
    
    if ! check_port ${PP_FRONTEND_PORT}; then
        echo -e "${RED}❌ Port ${PP_FRONTEND_PORT} is in use${NC}"
        return 1
    fi
    
    cd ${PLATFORM_PORTAL_DIR}
    
    # Set environment for Codespace
    export CODESPACE_NAME="${CODESPACE_NAME}"
    
    nohup reflex run --loglevel info > ${PLATFORM_PORTAL_LOG} 2>&1 &
    PP_PID=$!
    
    # Wait for compilation
    echo -e "${YELLOW}⏳ Compiling Reflex app (this may take 15-20 seconds)...${NC}"
    sleep 18
    
    if curl -s http://localhost:${PP_FRONTEND_PORT} >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Platform Portal started (PID: ${PP_PID})${NC}"
        return 0
    else
        echo -e "${RED}❌ Platform Portal failed to start. Check: ${PLATFORM_PORTAL_LOG}${NC}"
        return 1
    fi
}

# Function to show status
status() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}WAOOAW Platform Portal v2 - Status${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Backend
    if check_port ${BACKEND_PORT}; then
        echo -e "Backend API (${BACKEND_PORT}):     ${RED}⭕ Stopped${NC}"
    else
        echo -e "Backend API (${BACKEND_PORT}):     ${GREEN}✅ Running${NC}"
        BACKEND_ENV=$(curl -s http://localhost:${BACKEND_PORT}/health 2>/dev/null | grep -o '"environment":"[^"]*"' | cut -d'"' -f4)
        if [ ! -z "$BACKEND_ENV" ]; then
            echo -e "   Environment: ${CYAN}${BACKEND_ENV}${NC}"
        fi
    fi
    
    # Platform Portal Backend
    if check_port ${PP_BACKEND_PORT}; then
        echo -e "PP Backend (${PP_BACKEND_PORT}):       ${RED}⭕ Stopped${NC}"
    else
        echo -e "PP Backend (${PP_BACKEND_PORT}):       ${GREEN}✅ Running${NC}"
    fi
    
    # Platform Portal Frontend
    if check_port ${PP_FRONTEND_PORT}; then
        echo -e "PP Frontend (${PP_FRONTEND_PORT}):      ${RED}⭕ Stopped${NC}"
    else
        echo -e "PP Frontend (${PP_FRONTEND_PORT}):      ${GREEN}✅ Running${NC}"
    fi
    
    echo ""
    echo "Logs:"
    echo "  Backend:          ${BACKEND_LOG}"
    echo "  Platform Portal:  ${PLATFORM_PORTAL_LOG}"
    echo ""
    
    # Get actual codespace name
    CODESPACE_NAME_VAL="${CODESPACE_NAME:-unknown}"
    
    if [ "$CODESPACE_NAME_VAL" != "unknown" ]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🔗 WAOOAW Platform Portal v2 - Codespace URLs${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "${CYAN}Platform Portal (Start here):${NC}"
        echo "   https://${CODESPACE_NAME_VAL}-${PP_FRONTEND_PORT}.app.github.dev"
        echo ""
        echo -e "${CYAN}Backend API:${NC}"
        echo "   https://${CODESPACE_NAME_VAL}-${BACKEND_PORT}.app.github.dev"
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✨ Click 'Sign in with Google' to test OAuth flow${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    else
        echo "URLs (Local):"
        echo "  Platform Portal:  http://localhost:${PP_FRONTEND_PORT}"
        echo "  Backend API:      http://localhost:${BACKEND_PORT}"
    fi
}

# Function to show logs
logs() {
    local service=$1
    case $service in
        backend|be|api)
            echo -e "${YELLOW}Backend logs (${BACKEND_LOG}):${NC}"
            tail -50 ${BACKEND_LOG}
            ;;
        portal|pp|frontend)
            echo -e "${YELLOW}Platform Portal logs (${PLATFORM_PORTAL_LOG}):${NC}"
            tail -50 ${PLATFORM_PORTAL_LOG}
            ;;
        *)
            echo "Usage: $0 logs [backend|portal]"
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
        start_platform_portal
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🚀 WAOOAW Platform Portal v2 Started Successfully!${NC}"
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
        start_platform_portal
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
        echo "WAOOAW Platform Portal v2 Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Stop all services and start fresh"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status and URLs"
        echo "  logs     - Show logs (backend|portal)"
        echo ""
        echo "Fixed Ports:"
        echo "  Backend API:       ${BACKEND_PORT}"
        echo "  PP Backend:        ${PP_BACKEND_PORT}"
        echo "  PP Frontend:       ${PP_FRONTEND_PORT}"
        echo ""
        echo "Environment: GitHub Codespaces (test)"
        echo ""
        exit 1
        ;;
esac
