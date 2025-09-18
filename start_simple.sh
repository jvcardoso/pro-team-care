#!/bin/bash

# Script simples para iniciar o Pro Team Care
echo "🚀 Iniciando Pro Team Care..."
echo "🔍 Verificando sistema..."

# Verificar comandos necessários
check_system() {
    local missing_commands=()

    # Verificar Python
    if ! command -v python3 >/dev/null 2>&1; then
        missing_commands+=("python3")
    fi

    # Verificar se temos pelo menos um comando para verificar portas
    if ! command -v netstat >/dev/null 2>&1 && ! command -v ss >/dev/null 2>&1 && ! command -v lsof >/dev/null 2>&1; then
        missing_commands+=("netstat/ss/lsof")
    fi

    if [ ${#missing_commands[@]} -gt 0 ]; then
        echo -e "${RED}❌ Comandos necessários não encontrados: ${missing_commands[*]}${NC}"
        echo -e "${BLUE}💡 Instale com: sudo apt install net-tools python3${NC}"
        exit 1
    fi

    echo "✅ Sistema verificado - todos os comandos disponíveis"
}

# Cores simples
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(pwd)"

# Função para limpar cache
clean_cache() {
    echo "🧹 Limpando cache..."

    # Cache Python
    echo "  🐍 Limpando cache Python..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true

    # Cache Node.js (opcional - só se necessário)
    if [ -d "frontend" ]; then
        echo "  ⚛️  Limpando cache Node.js..."
        cd frontend
        rm -rf .vite 2>/dev/null || true
        npm cache clean --force 2>/dev/null || true
        cd ..
    fi

    echo "✅ Cache limpo"
}

# Função para matar processos existentes
kill_existing() {
    echo "🔄 Parando processos existentes..."

    # Matar processos específicos do projeto
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "vite.*--port 3000" 2>/dev/null || true

    # Matar processos nas portas específicas
    echo "🧹 Limpando portas 3000, 3001, 3002, 8000..."

    # Função para matar processo em uma porta específica
    kill_port() {
        local port=$1
        # Tentar com netstat primeiro
        local pids=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -v '-' | sort -u 2>/dev/null)

        if [ ! -z "$pids" ]; then
            for pid in $pids; do
                if [ "$pid" != "" ] && [ "$pid" != "0" ]; then
                    echo "  🔴 Matando processo $pid na porta $port"
                    kill -9 $pid 2>/dev/null || true
                fi
            done
        fi

        # Alternativa com ss se netstat não funcionar
        if command -v ss >/dev/null 2>&1; then
            local ss_pids=$(ss -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2 | grep -v '-' | sort -u 2>/dev/null)
            for pid in $ss_pids; do
                if [ "$pid" != "" ] && [ "$pid" != "0" ]; then
                    echo "  🔴 Matando processo $pid na porta $port (ss)"
                    kill -9 $pid 2>/dev/null || true
                fi
            done
        fi

        # Alternativa com lsof se disponível
        if command -v lsof >/dev/null 2>&1; then
            local lsof_pids=$(lsof -ti :$port 2>/dev/null || true)
            for pid in $lsof_pids; do
                if [ "$pid" != "" ] && [ "$pid" != "0" ]; then
                    echo "  🔴 Matando processo $pid na porta $port (lsof)"
                    kill -9 $pid 2>/dev/null || true
                fi
            done
        fi
    }

    # Limpar todas as portas que vamos usar
    kill_port 3000
    kill_port 3001
    kill_port 3002
    kill_port 8000

    # Matar qualquer vite antigo de qualquer projeto
    pkill -f "vite" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true

    # Aguardar processos terminarem
    sleep 3

    # Verificar se as portas estão livres
    echo "✅ Verificando se as portas estão livres..."
    for port in 3000 3001 3002 8000; do
        if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
            echo "  ⚠️  Porta $port ainda ocupada"
        else
            echo "  ✅ Porta $port livre"
        fi
    done
}

# Verificar sistema antes de tudo
check_system

# Mudar para o diretório do script se necessário
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar se estamos no diretório correto
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}❌ Estrutura do projeto não encontrada! Verifique se está no diretório correto.${NC}"
    echo -e "${BLUE}Diretório atual: $(pwd)${NC}"
    exit 1
fi

# Limpar variáveis de ambiente antigas que podem interferir
echo "🧹 Limpando variáveis de ambiente antigas..."
unset DB_HOST DB_PASSWORD DB_USERNAME DB_DATABASE DB_SCHEMA 2>/dev/null || true
echo "✅ Variáveis de ambiente limpas"

# Verificar se deve pular limpeza de cache
SKIP_CACHE=false
if [ "${1:-}" = "--skip-cache" ] || [ "${1:-}" = "-s" ]; then
    SKIP_CACHE=true
    echo -e "${YELLOW}⚡ Pulando limpeza de cache (--skip-cache)${NC}"
fi

# Limpar cache antes de iniciar (a menos que seja pulado)
if [ "$SKIP_CACHE" = false ]; then
    clean_cache
else
    echo -e "${BLUE}🧹 Pulando limpeza de cache...${NC}"
fi

# Parar processos existentes e limpar portas
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
echo -e "   Limpar cache: ./clean_cache.sh"
echo -e "   Início rápido (sem cache): ./start.sh --skip-cache"
echo -e "   Logs: tail -f backend.log (se existir)"
echo
echo "🔬 Testando conectividade dos serviços..."

# Testar backend
echo "  🔍 Testando backend..."
if command -v curl >/dev/null 2>&1; then
    if curl -s http://192.168.11.83:8000/api/v1/health >/dev/null 2>&1; then
        echo "  ✅ Backend respondendo"
    else
        echo "  ⚠️  Backend pode não estar respondendo ainda (aguarde alguns segundos)"
    fi
else
    echo "  ℹ️  curl não disponível - teste manual: http://192.168.11.83:8000/docs"
fi

# Testar frontend se disponível
if [ -f "frontend.pid" ]; then
    echo "  🔍 Testando frontend..."
    if command -v curl >/dev/null 2>&1; then
        if curl -s http://192.168.11.83:3000 >/dev/null 2>&1; then
            echo "  ✅ Frontend respondendo"
        else
            echo "  ⚠️  Frontend pode não estar respondendo ainda (aguarde alguns segundos)"
        fi
    else
        echo "  ℹ️  curl não disponível - teste manual: http://192.168.11.83:3000"
    fi
fi

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
