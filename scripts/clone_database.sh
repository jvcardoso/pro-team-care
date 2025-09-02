#!/bin/bash

# Script para clonar base PostgreSQL do Pro Team Care
# Autor: Sistema Pro Team Care
# Data: $(date +%Y-%m-%d)

# Configurações do banco (usar variáveis de ambiente para segurança)
DB_HOST="${DB_HOST:-192.168.11.62}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-Jvc@1702}"
SOURCE_DB="${SOURCE_DB:-pro_team_care_11}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== CLONE DATABASE PRO TEAM CARE ===${NC}"
echo -e "${YELLOW}Banco origem: ${SOURCE_DB}${NC}"
echo ""

# Solicitar nome do banco de destino
echo -e "${BLUE}Digite o nome do novo banco (destino):${NC}"
read -p "Nome do banco: " TARGET_DB

# Validar entrada
if [ -z "$TARGET_DB" ]; then
    echo -e "${RED}✗ Nome do banco não pode estar vazio!${NC}"
    exit 1
fi

# Validar formato do nome (apenas letras, números e underscore)
if [[ ! "$TARGET_DB" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo -e "${RED}✗ Nome do banco deve conter apenas letras, números e underscore!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Fonte: ${SOURCE_DB}${NC}"
echo -e "${YELLOW}Destino: ${TARGET_DB}${NC}"
echo ""

# Função para executar comandos PostgreSQL
run_psql() {
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d postgres "$@"
}

run_psql_db() {
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $1 "${@:2}"
}

# 1. Verificar se banco origem existe
echo -e "${BLUE}1. Verificando banco origem...${NC}"
if run_psql -t -c "SELECT 1 FROM pg_database WHERE datname='$SOURCE_DB';" | grep -q 1; then
    echo -e "${GREEN}✓ Banco $SOURCE_DB encontrado${NC}"
else
    echo -e "${RED}✗ Banco $SOURCE_DB não encontrado!${NC}"
    exit 1
fi

# 2. Verificar se banco destino já existe
echo -e "${BLUE}2. Verificando banco destino...${NC}"
if run_psql -t -c "SELECT 1 FROM pg_database WHERE datname='$TARGET_DB';" | grep -q 1; then
    echo -e "${YELLOW}⚠ Banco $TARGET_DB já existe!${NC}"
    read -p "Deseja sobrescrever? (s/N): " confirm
    if [[ $confirm =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}Removendo banco existente...${NC}"
        run_psql -c "DROP DATABASE IF EXISTS $TARGET_DB;"
    else
        echo -e "${RED}Operação cancelada pelo usuário${NC}"
        exit 1
    fi
fi

# 3. Criar novo banco
echo -e "${BLUE}3. Criando novo banco...${NC}"
run_psql -c "CREATE DATABASE $TARGET_DB OWNER postgres;"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Banco $TARGET_DB criado com sucesso${NC}"
else
    echo -e "${RED}✗ Erro ao criar banco $TARGET_DB${NC}"
    exit 1
fi

# 4. Fazer dump do banco origem
echo -e "${BLUE}4. Fazendo dump do banco origem...${NC}"
DUMP_FILE="/tmp/${SOURCE_DB}_backup_$(date +%Y%m%d_%H%M%S).sql"
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $SOURCE_DB --verbose --no-owner --no-privileges > $DUMP_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dump criado: $DUMP_FILE${NC}"
    echo -e "${BLUE}  Tamanho: $(du -h $DUMP_FILE | cut -f1)${NC}"
else
    echo -e "${RED}✗ Erro ao criar dump${NC}"
    exit 1
fi

# 5. Restaurar dump no banco destino
echo -e "${BLUE}5. Restaurando dump no banco destino...${NC}"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $TARGET_DB < $DUMP_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Restauração concluída com sucesso${NC}"
else
    echo -e "${RED}✗ Erro durante restauração${NC}"
    exit 1
fi

# 6. Verificar integridade
echo -e "${BLUE}6. Verificando integridade...${NC}"

# Contar tabelas
TABLES_SOURCE=$(run_psql_db $SOURCE_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='master';")
TABLES_TARGET=$(run_psql_db $TARGET_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='master';")

echo -e "${BLUE}  Tabelas no schema master:${NC}"
echo -e "  - Origem: $TABLES_SOURCE"
echo -e "  - Destino: $TABLES_TARGET"

if [ "$TABLES_SOURCE" = "$TABLES_TARGET" ]; then
    echo -e "${GREEN}✓ Número de tabelas conferem${NC}"
else
    echo -e "${YELLOW}⚠ Diferença no número de tabelas${NC}"
fi

# Verificar algumas tabelas importantes
echo -e "${BLUE}  Verificando dados principais:${NC}"
for table in users companies establishments; do
    if run_psql_db $TARGET_DB -t -c "SELECT 1 FROM master.$table LIMIT 1;" | grep -q 1; then
        COUNT=$(run_psql_db $TARGET_DB -t -c "SELECT COUNT(*) FROM master.$table;")
        echo -e "  - $table: $COUNT registros ${GREEN}✓${NC}"
    else
        echo -e "  - $table: ${YELLOW}Tabela não encontrada ou vazia${NC}"
    fi
done

# 7. Limpeza
echo -e "${BLUE}7. Limpeza...${NC}"
rm $DUMP_FILE
echo -e "${GREEN}✓ Arquivo de dump removido${NC}"

echo ""
echo -e "${GREEN}=== CLONAGEM CONCLUÍDA COM SUCESSO ===${NC}"
echo -e "${BLUE}Base $SOURCE_DB foi clonada para $TARGET_DB${NC}"
echo -e "${YELLOW}Agora você pode usar $TARGET_DB como backup de segurança${NC}"
echo ""
echo -e "${BLUE}Para usar a nova base no Laravel, atualize o .env:${NC}"
echo -e "DB_DATABASE=$TARGET_DB"