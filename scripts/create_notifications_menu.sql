-- Script para criar o menu "Notificações" como filho de "Templates & Exemplos"
-- Executa: psql -h 192.168.11.62 -U postgres -d pro_team_care_11 -f create_notifications_menu.sql

BEGIN;

-- Verificar se o menu pai existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM master.menus WHERE id = 100 AND name = 'Templates & Exemplos') THEN
        RAISE EXCEPTION 'Menu pai "Templates & Exemplos" (ID: 100) não encontrado';
    END IF;
END $$;

-- Buscar próximo ID disponível
WITH next_id AS (
    SELECT COALESCE(MAX(id), 0) + 1 AS new_id
    FROM master.menus
)

-- Inserir o menu Notificações
INSERT INTO master.menus (
    id,
    parent_id,
    level,
    sort_order,
    name,
    slug,
    url,
    icon,
    description,
    target,
    type,
    accepts_children,
    visible_in_menu,
    visible_in_breadcrumb,
    is_featured,
    company_specific,
    establishment_specific,
    is_active,
    is_visible,
    dev_only,
    created_at
)
SELECT
    next_id.new_id,
    100,                                    -- parent_id (Templates & Exemplos)
    1,                                      -- level
    1,                                      -- sort_order
    'Notificações',                         -- name
    'notificacoes',                         -- slug
    '/admin/notification-demo',             -- url
    'Bell',                                 -- icon
    'Exemplos de notificações e modais',   -- description
    '_self',                                -- target
    'menu',                                 -- type
    false,                                  -- accepts_children
    true,                                   -- visible_in_menu
    true,                                   -- visible_in_breadcrumb
    false,                                  -- is_featured
    false,                                  -- company_specific
    false,                                  -- establishment_specific
    true,                                   -- is_active
    true,                                   -- is_visible
    false,                                  -- dev_only
    CURRENT_TIMESTAMP                       -- created_at
FROM next_id;

-- Verificar resultado
SELECT
    id,
    parent_id,
    name,
    slug,
    url,
    icon,
    is_active,
    is_visible,
    visible_in_menu
FROM master.menus
WHERE
    name = 'Notificações'
    OR id = 100
ORDER BY level, sort_order;

COMMIT;

-- Mensagem de sucesso
SELECT 'Menu "Notificações" criado com sucesso!' AS resultado;
