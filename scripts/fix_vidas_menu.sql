-- =====================================================
-- Script: Corrigir Menu de Gestão de Vidas
-- Descrição: Remover duplicatas e submenu, manter apenas menu principal
-- Author: Sistema Pro Team Care
-- Date: 2025-10-03
-- =====================================================

BEGIN;

-- =====================================================
-- 1. REMOVER MENU DUPLICADO (ID 159 - criado por engano)
-- =====================================================

UPDATE master.menus
SET deleted_at = NOW()
WHERE id = 159;

-- =====================================================
-- 2. REMOVER SUBMENU (ID 147 - Lista de Vidas Ativas)
-- =====================================================

UPDATE master.menus
SET deleted_at = NOW()
WHERE id = 147;

-- =====================================================
-- 3. ATUALIZAR MENU PRINCIPAL (ID 146) PARA SER DIRETO
-- =====================================================

UPDATE master.menus
SET
    url = '/admin/vidas',
    path = '/admin/vidas',
    description = 'Visualização e gerenciamento de todas as vidas cadastradas nos contratos'
WHERE id = 146;

-- =====================================================
-- 4. VERIFICAR ORDEM NO MENU NEGÓCIO
-- =====================================================

-- Garantir que está após Contratos (sort_order = 40)
-- Empresas: 10
-- Estabelecimentos: 14
-- Clientes: 20
-- Contratos: 30
-- Vidas: 40 (já está correto)

-- =====================================================
-- 5. VERIFICAR RESULTADO
-- =====================================================

DO $$
DECLARE
    v_menu record;
BEGIN
    -- Verificar menu atualizado
    SELECT id, name, url, path, parent_id, sort_order INTO v_menu
    FROM master.menus
    WHERE id = 146 AND deleted_at IS NULL;

    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE '✅ MENU DE GESTÃO DE VIDAS CORRIGIDO';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Menu principal:';
    RAISE NOTICE '   ID: %', v_menu.id;
    RAISE NOTICE '   Nome: %', v_menu.name;
    RAISE NOTICE '   URL: %', v_menu.url;
    RAISE NOTICE '   Parent ID: % (Negócio)', v_menu.parent_id;
    RAISE NOTICE '   Ordem: %', v_menu.sort_order;
    RAISE NOTICE '';
    RAISE NOTICE '🗑️  Menus removidos:';
    RAISE NOTICE '   - ID 159 (duplicata)';
    RAISE NOTICE '   - ID 147 (submenu Lista de Vidas Ativas)';
    RAISE NOTICE '';
    RAISE NOTICE '📍 Estrutura do menu Negócio:';
    RAISE NOTICE '   1. Empresas (10)';
    RAISE NOTICE '   2. Estabelecimentos (14)';
    RAISE NOTICE '   3. Clientes (20)';
    RAISE NOTICE '   4. Gestão de Contratos (30)';
    RAISE NOTICE '   5. Gestão de Vidas (40) ← aqui';
    RAISE NOTICE '';
    RAISE NOTICE '🌐 URL: http://192.168.11.83:3000/admin/vidas';
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
END $$;

COMMIT;
