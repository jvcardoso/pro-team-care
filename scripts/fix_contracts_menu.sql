-- =====================================================
-- Script: Simplificar Menu de Gestão de Contratos
-- Descrição: Remover submenus e ter página única com abas
-- Author: Sistema Pro Team Care
-- Date: 2025-10-03
-- =====================================================

BEGIN;

-- =====================================================
-- 1. ATUALIZAR MENU PRINCIPAL PARA SER DIRETO
-- =====================================================

UPDATE master.menus
SET
    url = '/admin/contratos',
    path = '/admin/contratos',
    description = 'Gestão completa de contratos com dashboard e lista em abas'
WHERE id = 142;

-- =====================================================
-- 2. REMOVER SUBMENUS (soft delete via deleted_at)
-- =====================================================

UPDATE master.menus
SET deleted_at = NOW()
WHERE id IN (143, 144, 145);

-- =====================================================
-- 3. VERIFICAR RESULTADO
-- =====================================================

DO $$
DECLARE
    v_main_menu record;
    v_deleted_count int;
BEGIN
    -- Verificar menu principal
    SELECT name, url, path INTO v_main_menu
    FROM master.menus
    WHERE id = 142;

    -- Contar menus deletados
    SELECT COUNT(*) INTO v_deleted_count
    FROM master.menus
    WHERE id IN (143, 144, 145) AND deleted_at IS NOT NULL;

    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE '✅ MENU DE CONTRATOS SIMPLIFICADO';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Menu principal atualizado:';
    RAISE NOTICE '   Nome: %', v_main_menu.name;
    RAISE NOTICE '   URL: %', v_main_menu.url;
    RAISE NOTICE '   Path: %', v_main_menu.path;
    RAISE NOTICE '';
    RAISE NOTICE '🗑️  Submenus removidos: % de 3', v_deleted_count;
    RAISE NOTICE '';
    RAISE NOTICE '🌐 Acesse: http://192.168.11.83:3000/admin/contratos';
    RAISE NOTICE '   (página única com abas Dashboard e Lista)';
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
END $$;

COMMIT;
