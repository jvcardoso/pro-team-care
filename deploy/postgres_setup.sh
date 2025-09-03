#!/bin/bash

# Script de instalação do PostgreSQL para produção
echo "🐘 Instalando PostgreSQL para Pro Team Care..."

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

# Instalar PostgreSQL
echo -e "${BLUE}🐘 Instalando PostgreSQL 15...${NC}"
apt install -y postgresql-15 postgresql-contrib-15

# Iniciar e habilitar PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Configurar senha do postgres
echo -e "${BLUE}🔐 Configurando senha do usuário postgres...${NC}"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'sua_senha_segura_aqui';"

# Criar banco de dados
echo -e "${BLUE}🗄️ Criando banco de dados...${NC}"
sudo -u postgres createdb pro_team_care_prod

# Configurar PostgreSQL para produção
echo -e "${BLUE}⚙️ Configurando PostgreSQL para produção...${NC}"

# Backup do arquivo original
cp /etc/postgresql/15/main/postgresql.conf /etc/postgresql/15/main/postgresql.conf.backup

# Configurações de produção
cat >> /etc/postgresql/15/main/postgresql.conf << EOF

# Configurações de Produção - Pro Team Care
max_connections = 100
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
max_parallel_maintenance_workers = 2

# Logging
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_statement = 'ddl'
log_duration = on
log_lock_waits = on
log_min_duration_statement = 1000

# Segurança
password_encryption = scram-sha-256
ssl = on
EOF

# Configurar pg_hba.conf para conexões locais seguras
echo -e "${BLUE}🔒 Configurando autenticação...${NC}"
cat > /etc/postgresql/15/main/pg_hba.conf << EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   pro_team_care_prod  prod_user                           scram-sha-256
host    pro_team_care_prod  prod_user   192.168.11.0/24         scram-sha-256
host    pro_team_care_prod  prod_user   127.0.0.1/32            scram-sha-256
local   all             all                                     peer
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
EOF

# Reiniciar PostgreSQL
echo -e "${BLUE}🔄 Reiniciando PostgreSQL...${NC}"
systemctl restart postgresql

# Criar usuário da aplicação
echo -e "${BLUE}👤 Criando usuário da aplicação...${NC}"
sudo -u postgres psql -c "CREATE USER prod_user WITH ENCRYPTED PASSWORD 'sua_senha_prod_aqui';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE pro_team_care_prod TO prod_user;"

# Configurar backup automático
echo -e "${BLUE}💾 Configurando backup automático...${NC}"
mkdir -p /var/backups/postgresql
cat > /etc/cron.daily/postgres_backup << EOF
#!/bin/bash
BACKUP_DIR="/var/backups/postgresql"
DATE=\$(date +%Y%m%d_%H%M%S)
sudo -u postgres pg_dump pro_team_care_prod > \$BACKUP_DIR/pro_team_care_prod_\$DATE.sql
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
EOF
chmod +x /etc/cron.daily/postgres_backup

# Configurar monitoramento básico
echo -e "${BLUE}📊 Configurando monitoramento...${NC}"
apt install -y htop iotop sysstat

# Configurar firewall
echo -e "${BLUE}🔥 Configurando firewall...${NC}"
apt install -y ufw
ufw allow 5432/tcp
ufw --force enable

# Verificar instalação
echo -e "${BLUE}✅ Verificando instalação...${NC}"
sudo -u postgres psql -c "SELECT version();"
sudo -u postgres psql -l

echo -e "${GREEN}🎉 PostgreSQL instalado e configurado com sucesso!${NC}"
echo
echo -e "${BLUE}📋 PRÓXIMOS PASSOS:${NC}"
echo "1. Execute as migrações do Alembic no servidor backend"
echo "2. Configure a senha do usuário 'prod_user' no arquivo .env do backend"
echo "3. Teste a conexão: psql -h localhost -U prod_user -d pro_team_care_prod"
echo
echo -e "${YELLOW}🔐 SENHAS IMPORTANTES:${NC}"
echo "- Usuário postgres: [sua_senha_segura_aqui]"
echo "- Usuário prod_user: [sua_senha_prod_aqui]"
echo
echo -e "${BLUE}📊 MONITORAMENTO:${NC}"
echo "- Status: systemctl status postgresql"
echo "- Logs: tail -f /var/log/postgresql/postgresql-15-main.log"
echo "- Conexões: sudo -u postgres psql -c 'SELECT * FROM pg_stat_activity;'"