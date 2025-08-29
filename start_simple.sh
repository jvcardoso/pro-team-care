#!/bin/bash

# Script simples para iniciar o Pro Team Care
echo "🚀 Iniciando Pro Team Care..."

# Cores simples
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(pwd)"

# Função para matar processos existentes
kill_existing() {
    echo "🔄 Parando processos existentes..."
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "vite.*--port 3000" 2>/dev/null || true
    sleep 2
}

# Verificar se estamos no diretório correto
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}❌ Execute este script no diretório do projeto!${NC}"
    exit 1
fi

# Parar processos existentes
kill_existing

# Iniciar backend
echo -e "${BLUE}🔧 Iniciando Backend...${NC}"
if [ -d "venv" ]; then
    . venv/bin/activate
    
    # Testar se funciona
    python3 -c "import app.main" 2>/dev/null || {
        echo -e "${RED}❌ Erro ao carregar aplicação Python${NC}"
        exit 1
    }
    
    # Iniciar uvicorn em background
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    sleep 3
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Backend rodando (PID: $BACKEND_PID)${NC}"
        echo -e "${BLUE}📖 API Docs: http://192.168.11.83:8000/docs${NC}"
    else
        echo -e "${RED}❌ Falha ao iniciar backend${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Ambiente virtual não encontrado!${NC}"
    exit 1
fi

# Verificar Node.js para frontend
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js encontrado: $NODE_VERSION${NC}"
    
    if [ -d "frontend" ]; then
        echo -e "${BLUE}🎨 Iniciando Frontend...${NC}"
        cd frontend
        
        # Instalar dependências se necessário
        if [ ! -d "node_modules" ]; then
            echo "📦 Instalando dependências..."
            npm install
        fi
        
        # Criar .env se não existir
        if [ ! -f ".env" ]; then
            echo "VITE_API_URL=http://192.168.11.83:8000" > .env
        fi
        
        # Iniciar em background
        npm run dev -- --host 0.0.0.0 --port 3000 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../frontend.pid
        
        sleep 5
        
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo -e "${GREEN}✅ Frontend rodando (PID: $FRONTEND_PID)${NC}"
            echo -e "${BLUE}🎨 Frontend: http://192.168.11.83:3000${NC}"
        else
            echo -e "${RED}⚠️ Frontend pode ter falhado${NC}"
        fi
        
        cd ..
    fi
elif [ -f "$HOME/.nvm/nvm.sh" ]; then
    echo "🔄 Carregando NVM..."
    . "$HOME/.nvm/nvm.sh"
    
    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✅ Node.js via NVM: $NODE_VERSION${NC}"
        # Repetir lógica do frontend aqui se necessário
    else
        echo -e "${RED}⚠️ Node.js não disponível - apenas backend${NC}"
    fi
else
    echo -e "${RED}⚠️ Node.js não encontrado - apenas backend${NC}"
fi

echo
echo "=========================================="
echo -e "${GREEN}🎉 Pro Team Care iniciado com sucesso!${NC}"
echo "=========================================="
echo
echo -e "${BLUE}🌐 URLS DE ACESSO:${NC}"
echo -e "   Backend API: http://192.168.11.83:8000"
echo -e "   Documentação: http://192.168.11.83:8000/docs"
echo -e "   Health Check: http://192.168.11.83:8000/api/v1/health"

if command -v node >/dev/null 2>&1 && [ -d "frontend" ]; then
    echo -e "   Frontend App: http://192.168.11.83:3000"
fi

echo
echo -e "${BLUE}📊 CONTROLE:${NC}"
echo -e "   Para parar: ./stop_servers.sh"
echo -e "   Logs: tail -f backend.log (se existir)"
echo
echo -e "${GREEN}💡 Pressione Ctrl+C para parar todos os serviços${NC}"

# Função cleanup para Ctrl+C
cleanup() {
    echo
    echo "🔄 Parando serviços..."
    
    if [ -f backend.pid ]; then
        BACKEND_PID=$(cat backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm backend.pid
    fi
    
    if [ -f frontend.pid ]; then
        FRONTEND_PID=$(cat frontend.pid)  
        kill $FRONTEND_PID 2>/dev/null || true
        rm frontend.pid
    fi
    
    echo -e "${GREEN}✅ Serviços parados!${NC}"
    exit 0
}

# Capturar Ctrl+C
trap cleanup INT

# Manter script rodando
while true; do
    sleep 1
done