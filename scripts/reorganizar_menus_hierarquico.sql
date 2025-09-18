-- REORGANIZAR MENUS HIERÁRQUICOS
-- Administração > Negócio (Empresas, Estabelecimentos, Clientes)
-- Administração > Segurança (Usuários, Perfis, Auditoria, Menus)

-- Definir contexto admin para bypass de RLS
SELECT master.set_current_company_id(0);

-- =======================================================================
-- PASSO 1: CRIAR SUBMENUS PRINCIPAIS
-- =======================================================================

-- Inserir submenu 'Negócio' sob Administração (ID: 20)
INSERT INTO master.menus (
    parent_id, level, sort_order, name, slug, icon, description,
    type, accepts_children, visible_in_menu, is_active, is_visible,
    created_at, updated_at
) VALUES (
    20, 2, 10, 'Negócio', 'negocio', 'Briefcase', 'Gestão de empresas, estabelecimentos e clientes',
    'category', true, true, true, true,
    NOW(), NOW()
);

-- Inserir submenu 'Segurança' sob Administração (ID: 20)
INSERT INTO master.menus (
    parent_id, level, sort_order, name, slug, icon, description,
    type, accepts_children, visible_in_menu, is_active, is_visible,
    created_at, updated_at
) VALUES (
    20, 2, 20, 'Segurança', 'seguranca', 'Shield', 'Usuários, perfis, auditoria e menus',
    'category', true, true, true, true,
    NOW(), NOW()
);

-- =======================================================================
-- PASSO 2: OBTER IDS DOS NOVOS SUBMENUS
-- =======================================================================

-- Criar variáveis temporárias (usando função do PostgreSQL)
DO $$
DECLARE
    negocio_id INTEGER;
    seguranca_id INTEGER;
BEGIN
    -- Obter ID do submenu 'Negócio'
    SELECT id INTO negocio_id FROM master.menus
    WHERE parent_id = 20 AND name = 'Negócio';

    -- Obter ID do submenu 'Segurança'
    SELECT id INTO seguranca_id FROM master.menus
    WHERE parent_id = 20 AND name = 'Segurança';

    RAISE NOTICE 'Negócio ID: %, Segurança ID: %', negocio_id, seguranca_id;

    -- =======================================================================
    -- PASSO 3: MOVER MENUS PARA 'NEGÓCIO'
    -- =======================================================================

    -- Mover Empresas (ID: 14) para Negócio
    UPDATE master.menus
    SET parent_id = negocio_id, level = 3, sort_order = 1
    WHERE id = 14;

    -- Mover Estabelecimentos (ID: 136) para Negócio
    UPDATE master.menus
    SET parent_id = negocio_id, level = 3, sort_order = 2
    WHERE id = 136;

    -- Mover Clientes (ID: 138) para Negócio
    UPDATE master.menus
    SET parent_id = negocio_id, level = 3, sort_order = 3
    WHERE id = 138;

    RAISE NOTICE 'Menus de Negócio reorganizados';

    -- =======================================================================
    -- PASSO 4: MOVER MENUS PARA 'SEGURANÇA'
    -- =======================================================================

    -- Mover Usuários (ID: 21) para Segurança
    UPDATE master.menus
    SET parent_id = seguranca_id, level = 3, sort_order = 1
    WHERE id = 21;

    -- Mover Perfis e Permissões (ID: 22) para Segurança
    UPDATE master.menus
    SET parent_id = seguranca_id, level = 3, sort_order = 2
    WHERE id = 22;

    -- Mover Auditoria (ID: 23) para Segurança
    UPDATE master.menus
    SET parent_id = seguranca_id, level = 3, sort_order = 3
    WHERE id = 23;

    -- Criar menu 'Menus' em Segurança
    INSERT INTO master.menus (
        parent_id, level, sort_order, name, slug, url, icon, description,
        type, accepts_children, visible_in_menu, is_active, is_visible,
        created_at, updated_at
    ) VALUES (
        seguranca_id, 3, 4, 'Menus', 'menus', '/admin/menus', 'Menu', 'Gestão de menus do sistema',
        'page', false, true, true, true,
        NOW(), NOW()
    );

    RAISE NOTICE 'Menus de Segurança reorganizados';
END $$;

-- =======================================================================
-- PASSO 5: VERIFICAÇÃO E RELATÓRIO
-- =======================================================================

RAISE NOTICE '';
RAISE NOTICE '✅ REORGANIZAÇÃO DE MENUS CONCLUÍDA!';
RAISE NOTICE '===========================================';

-- Mostrar estrutura final
DO $$
DECLARE
    menu_rec RECORD;
    negocio_id INTEGER;
    seguranca_id INTEGER;
BEGIN
    -- Obter IDs
    SELECT id INTO negocio_id FROM master.menus WHERE parent_id = 20 AND name = 'Negócio';
    SELECT id INTO seguranca_id FROM master.menus WHERE parent_id = 20 AND name = 'Segurança';

    RAISE NOTICE '';
    RAISE NOTICE '📋 ESTRUTURA HIERÁRQUICA FINAL:';
    RAISE NOTICE '';
    RAISE NOTICE 'Administração (20)';

    -- Mostrar submenus de Administração
    FOR menu_rec IN
        SELECT id, name, icon, sort_order
        FROM master.menus
        WHERE parent_id = 20
        ORDER BY sort_order, name
    LOOP
        RAISE NOTICE '├── % (%) - %', menu_rec.name, menu_rec.id, menu_rec.icon;

        -- Mostrar itens do submenu
        FOR menu_rec IN
            SELECT id, name, url, icon, sort_order
            FROM master.menus
            WHERE parent_id = menu_rec.id
            ORDER BY sort_order, name
        LOOP
            RAISE NOTICE '│   ├── % (%) - % → %', menu_rec.name, menu_rec.id, menu_rec.icon, COALESCE(menu_rec.url, 'N/A');
        END LOOP;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE '🎉 Estrutura reorganizada com sucesso!';
    RAISE NOTICE '   📁 Negócio: Empresas, Estabelecimentos, Clientes';
    RAISE NOTICE '   🔒 Segurança: Usuários, Perfis, Auditoria, Menus';
END $$;
