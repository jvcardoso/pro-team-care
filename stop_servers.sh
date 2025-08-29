#!/bin/bash

# =============================================================================
# Pro Team Care - Script para Parar Serviços
# =============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log "Parando serviços Pro Team Care..."

cd "$PROJECT_DIR"

# Parar backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        log_success "Backend parado (PID: $BACKEND_PID)"
    else
        log_error "Backend já estava parado"
    fi
    rm -f backend.pid
else
    # Tentar matar processos uvicorn na porta 8000
    pkill -f "uvicorn.*app.main:app" && log_success "Processos uvicorn encerrados"
fi

# Parar frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        log_success "Frontend parado (PID: $FRONTEND_PID)"
    else
        log_error "Frontend já estava parado"
    fi
    rm -f frontend.pid
else
    # Tentar matar processos vite na porta 3000
    pkill -f "vite.*--port 3000" && log_success "Processos Vite encerrados"
fi

# Limpar arquivos de log antigos (opcional)
if [ "$1" = "--clean-logs" ]; then
    rm -f backend.log frontend.log
    log_success "Logs limpos"
fi

log_success "Todos os serviços foram parados!"

echo
echo "Para reiniciar:"
echo "  ./start_full_stack.sh"