-- =====================================================
-- Script: Criar Menu de Gestão de Vidas
-- Descrição: Adiciona menu "Gestão de Vidas" ao sistema
-- Author: Sistema Pro Team Care
-- Date: 2025-10-03
-- =====================================================

BEGIN;

-- =====================================================
-- 1. INSERIR MENU PRINCIPAL DE VIDAS
-- =====================================================

INSERT INTO master.menus (
    id,
    name,
    slug,
    path,
    url,
    icon,
    parent_id,
    sort_order,
    description,
    permission_name
)
VALUES (
    159,                                   -- ID sequencial (max atual é 158)
    'Gestão de Vidas',                    -- Nome do menu
    'vidas',                               -- Slug
    '/admin/vidas',                        -- Path
    '/admin/vidas',                        -- URL
    'users',                               -- Ícone (Lucide icon)
    (SELECT id FROM master.menus WHERE path = '/admin' LIMIT 1),  -- Parent: menu "admin"
    40,                                    -- Ordem (após contratos)
    'Visualização e gerenciamento de todas as vidas cadastradas nos contratos',
    'contracts.view'                       -- Permissão necessária
)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 2. OBTER ID DO MENU CRIADO
-- =====================================================

DO $$
DECLARE
    v_menu_id INTEGER;
BEGIN
    SELECT id INTO v_menu_id
    FROM master.menus
    WHERE path = '/admin/vidas'
    LIMIT 1;

    IF v_menu_id IS NOT NULL THEN
        RAISE NOTICE '✅ Menu "Gestão de Vidas" criado com ID: %', v_menu_id;
    ELSE
        RAISE EXCEPTION '❌ Erro: Menu não foi criado';
    END IF;
END $$;

-- =====================================================
-- 3. INSERIR CÓDIGO DE PROGRAMA PARA ACESSO RÁPIDO
-- =====================================================

INSERT INTO master.program_codes (
    shortcode,
    module_code,
    program_type,
    label,
    description,
    route,
    icon,
    search_tokens,
    menu_id,
    is_active,
    required_permission
)
VALUES (
    'hc0050',                              -- Código: HC (Home Care) + 00 (Cadastro) + 50
    'HC',                                  -- Módulo: Home Care
    '00',                                  -- Tipo: 00 = Cadastro
    'Gestão de Vidas',                     -- Label
    'Visualização e gerenciamento de vidas dos contratos Home Care',
    '/admin/vidas',                        -- Rota
    'users',                               -- Ícone
    ARRAY['vidas', 'lives', 'beneficiarios', 'titulares', 'dependentes', 'funcionarios', 'home care'],
    (SELECT id FROM master.menus WHERE path = '/admin/vidas' LIMIT 1),
    TRUE,                                  -- Ativo
    'contracts.view'                       -- Permissão
)
ON CONFLICT (shortcode) DO NOTHING;

-- =====================================================
-- 4. VERIFICAR E EXIBIR RESULTADO
-- =====================================================

DO $$
DECLARE
    v_menu_count INTEGER;
    v_code_count INTEGER;
BEGIN
    -- Contar menus
    SELECT COUNT(*) INTO v_menu_count
    FROM master.menus
    WHERE path = '/admin/vidas';

    -- Contar códigos de programa
    SELECT COUNT(*) INTO v_code_count
    FROM master.program_codes
    WHERE shortcode = 'hc0050';

    -- Exibir resultado
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE '✅ MENU DE GESTÃO DE VIDAS CONFIGURADO';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Menu criado: % registro(s)', v_menu_count;
    RAISE NOTICE '🔢 Código de programa: % registro(s)', v_code_count;
    RAISE NOTICE '';
    RAISE NOTICE '🌐 URL: http://192.168.11.83:3000/admin/vidas';
    RAISE NOTICE '⌨️  Acesso rápido: Ctrl+Alt+X → digite "hc0050" ou "vidas"';
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
END $$;

COMMIT;
