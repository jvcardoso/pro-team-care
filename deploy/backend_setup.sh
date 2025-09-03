#!/bin/bash

# Script de instalação do Backend (FastAPI) para produção
echo "🚀 Instalando Backend Pro Team Care..."

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Execute como root: sudo $0${NC}"
    exit 1
fi

# Atualizar sistema
echo -e "${BLUE}📦 Atualizando sistema...${NC}"
apt update && apt upgrade -y

# Instalar Python 3.11 e dependências
echo -e "${BLUE}🐍 Instalando Python 3.11...${NC}"
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Instalar dependências do sistema
echo -e "${BLUE}🔧 Instalando dependências do sistema...${NC}"
apt install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    git \
    curl \
    htop \
    iotop \
    sysstat \
    postgresql-client

# Instalar Redis
echo -e "${BLUE}📦 Instalando Redis...${NC}"
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server

# Configurar Redis para produção
echo -e "${BLUE}⚙️ Configurando Redis...${NC}"
cat >> /etc/redis/redis.conf << EOF

# Configurações de Produção - Pro Team Care
maxmemory 512mb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 0
databases 1
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
EOF

systemctl restart redis-server

# Criar usuário do sistema para a aplicação
echo -e "${BLUE}👤 Criando usuário da aplicação...${NC}"
useradd -m -s /bin/bash procare
usermod -aG sudo procare

# Criar diretórios da aplicação
echo -e "${BLUE}📁 Criando diretórios da aplicação...${NC}"
mkdir -p /opt/pro_team_care
mkdir -p /var/log/pro_team_care
mkdir -p /var/run/pro_team_care
chown -R procare:procare /opt/pro_team_care
chown -R procare:procare /var/log/pro_team_care
chown -R procare:procare /var/run/pro_team_care

# Copiar código da aplicação (assumindo que está em /tmp)
echo -e "${BLUE}📋 Copiando código da aplicação...${NC}"
# Substitua pelo caminho real do seu código
# cp -r /caminho/para/seu/codigo/* /opt/pro_team_care/

# Configurar ambiente virtual
echo -e "${BLUE}🌍 Configurando ambiente virtual...${NC}"
sudo -u procare python3.11 -m venv /opt/pro_team_care/venv
sudo -u procare /opt/pro_team_care/venv/bin/pip install --upgrade pip

# Instalar dependências Python
echo -e "${BLUE}📦 Instalando dependências Python...${NC}"
sudo -u procare /opt/pro_team_care/venv/bin/pip install -r /opt/pro_team_care/requirements.txt

# Configurar arquivo .env de produção
echo -e "${BLUE}🔐 Criando arquivo .env de produção...${NC}"
cat > /opt/pro_team_care/.env << EOF
# ======================================
# 🔐 PRO TEAM CARE - CONFIGURAÇÕES DE PRODUÇÃO
# ======================================

# Configurações básicas
ENVIRONMENT=production
DEBUG=false
APP_NAME=Pro Team Care System
APP_VERSION=1.0.0

# Banco de dados
DB_CONNECTION=postgresql+asyncpg
DB_HOST=192.168.11.62
DB_PORT=5432
DB_USERNAME=prod_user
DB_PASSWORD=sua_senha_prod_aqui
DB_DATABASE=pro_team_care_prod
DB_SCHEMA=master

# Pool de conexões
DB_POOL_SIZE=10
DB_POOL_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Segurança JWT
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://192.168.11.83:80,http://192.168.11.83:443,https://seu-dominio.com
ALLOWED_HOSTS=192.168.11.83,seu-dominio.com,localhost

# API
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL=300

# Serviços externos
VIACEP_BASE_URL=https://viacep.com.br/ws
VIACEP_TIMEOUT=10
RECEITA_WS_BASE_URL=https://www.receitaws.com.br/v1
RECEITA_WS_TIMEOUT=15
EOF

chown procare:procare /opt/pro_team_care/.env
chmod 600 /opt/pro_team_care/.env

# Executar migrações do banco
echo -e "${BLUE}🗄️ Executando migrações do banco...${NC}"
cd /opt/pro_team_care
sudo -u procare /opt/pro_team_care/venv/bin/alembic upgrade head

# Criar serviço systemd
echo -e "${BLUE}⚙️ Criando serviço systemd...${NC}"
cat > /etc/systemd/system/procare-backend.service << EOF
[Unit]
Description=Pro Team Care Backend API
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service

[Service]
Type=exec
User=procare
Group=procare
WorkingDirectory=/opt/pro_team_care
Environment=PATH=/opt/pro_team_care/venv/bin
ExecStart=/opt/pro_team_care/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
RestartSec=5
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Recarregar systemd e iniciar serviço
systemctl daemon-reload
systemctl start procare-backend
systemctl enable procare-backend

# Configurar logrotate
echo -e "${BLUE}📝 Configurando rotação de logs...${NC}"
cat > /etc/logrotate.d/procare-backend << EOF
/var/log/pro_team_care/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 procare procare
    postrotate
        systemctl reload procare-backend
    endscript
}
EOF

# Configurar firewall
echo -e "${BLUE}🔥 Configurando firewall...${NC}"
apt install -y ufw
ufw allow 8000/tcp
ufw --force enable

# Configurar monitoramento
echo -e "${BLUE}📊 Configurando monitoramento...${NC}"
apt install -y prometheus-node-exporter
systemctl start prometheus-node-exporter
systemctl enable prometheus-node-exporter

# Verificar instalação
echo -e "${BLUE}✅ Verificando instalação...${NC}"
sleep 5
curl -s http://localhost:8000/api/v1/health | head -5

echo -e "${GREEN}🎉 Backend instalado e configurado com sucesso!${NC}"
echo
echo -e "${BLUE}📋 STATUS DOS SERVIÇOS:${NC}"
echo "  Backend: $(systemctl is-active procare-backend)"
echo "  Redis: $(systemctl is-active redis-server)"
echo "  Node Exporter: $(systemctl is-active prometheus-node-exporter)"
echo
echo -e "${BLUE}📊 URLs DE ACESSO:${NC}"
echo "  API: http://192.168.11.83:8000"
echo "  Documentação: http://192.168.11.83:8000/docs"
echo "  Health Check: http://192.168.11.83:8000/api/v1/health"
echo
echo -e "${BLUE}📋 COMANDOS ÚTEIS:${NC}"
echo "  Status: systemctl status procare-backend"
echo "  Logs: journalctl -u procare-backend -f"
echo "  Restart: systemctl restart procare-backend"
echo "  Reload: systemctl reload procare-backend"
echo
echo -e "${YELLOW}⚠️ PRÓXIMOS PASSOS:${NC}"
echo "1. Configure a senha do banco no arquivo /opt/pro_team_care/.env"
echo "2. Configure o domínio no arquivo .env (se usar HTTPS)"
echo "3. Configure o Nginx no servidor frontend para proxy reverso"
echo "4. Configure SSL/HTTPS se necessário"