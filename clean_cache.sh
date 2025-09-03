#!/bin/bash

# Script para limpeza de cache do Pro Team Care
echo "🧹 Limpando cache do Pro Team Care..."

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para limpar cache Python
clean_python_cache() {
    echo -e "${BLUE}🐍 Limpando cache Python...${NC}"

    # Cache de bytecode
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true

    # Cache do pytest
    rm -rf .pytest_cache 2>/dev/null || true

    # Cache do mypy
    rm -rf .mypy_cache 2>/dev/null || true

    echo -e "${GREEN}✅ Cache Python limpo${NC}"
}

# Função para limpar cache Node.js
clean_nodejs_cache() {
    echo -e "${BLUE}⚛️  Limpando cache Node.js...${NC}"

    if [ -d "frontend" ]; then
        cd frontend

        # Cache do Vite
        rm -rf .vite 2>/dev/null || true
        rm -rf dist 2>/dev/null || true

        # Cache do npm
        npm cache clean --force 2>/dev/null || true

        # Cache do Jest
        rm -rf coverage 2>/dev/null || true

        cd ..
        echo -e "${GREEN}✅ Cache Node.js limpo${NC}"
    else
        echo -e "${YELLOW}⚠️  Diretório frontend não encontrado${NC}"
    fi
}

# Função para limpar cache do sistema
clean_system_cache() {
    echo -e "${BLUE}🖥️  Limpando cache do sistema...${NC}"

    # Cache de logs antigos (opcional)
    find . -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true

    echo -e "${GREEN}✅ Cache do sistema limpo${NC}"
}

# Menu de opções
show_menu() {
    echo
    echo "=========================================="
    echo "🧹 LIMPEZA DE CACHE - PRO TEAM CARE"
    echo "=========================================="
    echo
    echo "Escolha o tipo de limpeza:"
    echo "1) 🐍 Apenas cache Python"
    echo "2) ⚛️  Apenas cache Node.js"
    echo "3) 🖥️  Apenas cache do sistema"
    echo "4) 🚀 LIMPAR TUDO (Python + Node.js + Sistema)"
    echo "5) ❌ Cancelar"
    echo
    read -p "Digite sua opção (1-5): " choice
    echo
}

# Executar limpeza baseada na escolha
case "${1:-}" in
    "python"|"-p"|"--python")
        clean_python_cache
        ;;
    "nodejs"|"-n"|"--nodejs")
        clean_nodejs_cache
        ;;
    "system"|"-s"|"--system")
        clean_system_cache
        ;;
    "all"|"-a"|"--all")
        clean_python_cache
        clean_nodejs_cache
        clean_system_cache
        ;;
    *)
        show_menu
        case $choice in
            1)
                clean_python_cache
                ;;
            2)
                clean_nodejs_cache
                ;;
            3)
                clean_system_cache
                ;;
            4)
                clean_python_cache
                clean_nodejs_cache
                clean_system_cache
                ;;
            5)
                echo -e "${YELLOW}❌ Operação cancelada${NC}"
                exit 0
                ;;
            *)
                echo -e "${YELLOW}⚠️  Opção inválida${NC}"
                exit 1
                ;;
        esac
        ;;
esac

echo
echo -e "${GREEN}🎉 Limpeza de cache concluída!${NC}"
echo
echo -e "${BLUE}💡 Dicas:${NC}"
echo "  • Execute './start.sh' para iniciar os serviços"
echo "  • Use './clean_cache.sh --all' para limpeza completa"
echo "  • Use './clean_cache.sh --python' para apenas Python"