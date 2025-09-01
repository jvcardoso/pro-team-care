# ==========================================
# PRO TEAM CARE - LISTA DE INSTALAÇÃO
# Ambiente de Produção
# ==========================================

# 1. SISTEMA OPERACIONAL - ATUALIZAÇÕES
sudo apt update && sudo apt upgrade -y

# 2. UTILITÁRIOS ESSENCIAIS
sudo apt install -y curl wget git htop iotop ncdu ufw fail2ban unzip software-properties-common
apt-transport-https ca-certificates gnupg lsb-release

# 3. PYTHON 3.11 (Backend)
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip python3-setuptools

# 4. NODE.JS 18 (Frontend + OpenCode)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs npm

# 5. POSTGRESQL (Banco de Dados)
sudo apt install -y postgresql postgresql-contrib postgresql-server-dev-all

# 6. REDIS (Cache)
sudo apt install -y redis-server

# 7. NGINX (Web Server/Reverse Proxy)
sudo apt install -y nginx

# 8. SUPERVISOR (Gerenciamento de Processos) - OPCIONAL
sudo apt install -y supervisor

# 9. MONITORAMENTO - OPCIONAL
sudo apt install -y prometheus prometheus-node-exporter grafana

# 10. LOG AGGREGATION - OPCIONAL
sudo apt install -y rsyslog

# ==========================================
# VERIFICAÇÃO DAS INSTALAÇÕES
# ==========================================

# Verificar versões instaladas
python3.11 --version
node --version
npm --version
psql --version
redis-server --version
nginx -v
git --version

# Verificar status dos serviços
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status nginx

# ==========================================
# INSTALAÇÃO DO OPENCODE
# ==========================================

# Instalar OpenCode globalmente
npm install -g @anthropic/claude-code

# Verificar instalação
claude-code --version

# ==========================================
# DEPENDÊNCIAS ADICIONAIS DO PYTHON
# ==========================================

# Instalar dependências do projeto
cd /opt/pro-team-care
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ==========================================
# DEPENDÊNCIAS ADICIONAIS DO NODE.JS
# ==========================================

# Instalar dependências do frontend
cd frontend
npm install
cd ..

# ==========================================
# FERRAMENTAS DE DESENVOLVIMENTO (OPCIONAIS)
# ==========================================

# Docker (para containerização futura)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.
0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# ==========================================
# VERIFICAÇÃO FINAL
# ==========================================

# Testar se tudo está funcionando
echo "=== VERIFICAÇÃO DE INSTALAÇÕES ==="
echo "Python: $(python3.11 --version)"
echo "Node.js: $(node --version)"
echo "PostgreSQL: $(psql --version | head -1)"
echo "Redis: $(redis-server --version | head -1)"
echo "Nginx: $(nginx -v 2>&1)"
echo "OpenCode: $(claude-code --version 2>/dev/null || echo 'Não instalado')"
echo "Git: $(git --version)"
echo "Docker: $(docker --version 2>/dev/null || echo 'Não instalado')"
echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'Não instalado')"

---

## 📋 LISTA RESUMIDA POR CATEGORIA

### 🔧 OBRIGATÓRIAS

• ✅ Python 3.11
• ✅ Node.js 18 + npm
• ✅ PostgreSQL
• ✅ Redis
• ✅ Nginx
• ✅ OpenCode (npm install -g @anthropic/claude-code)

### 🛡️ SEGURANÇA

• ✅ ufw (firewall)
• ✅ fail2ban (proteção SSH)

### 📊 MONITORAMENTO (OPCIONAIS)

• 📈 htop, iotop, ncdu (monitoramento)
• 📊 prometheus, grafana (opcional)

### 🐳 CONTAINERIZAÇÃO (FUTURO)

• 🐳 Docker
• 🐳 Docker Compose

---

## ⚡ COMANDO ÚNICO PARA INSTALAÇÃO RÁPIDA

# Instalar tudo de uma vez (exceto Docker)
sudo apt update && sudo apt install -y curl wget git htop iotop ncdu ufw fail2ban python3.11
python3.11-venv python3.11-dev python3-pip postgresql postgresql-contrib redis-server nginx
supervisor

# Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Instalar OpenCode
npm install -g @anthropic/claude-code

---

## 🔍 VERIFICAÇÃO PÓS-INSTALAÇÃO

Após instalar tudo, execute:

# Verificar versões
python3.11 --version && node --version && psql --version && redis-server --version && nginx -v
&& claude-code --version

# Verificar serviços
sudo systemctl status postgresql redis-server nginx

# Testar conectividade
sudo -u postgres psql -c "SELECT version();"
redis-cli ping

Esta lista cobre todas as aplicações necessárias para rodar o Pro Team Care em produção com
OpenCode para desenvolvimento e manutenção.