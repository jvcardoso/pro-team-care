-- Script para criar o menu "Faturamento B2B" como filho de "Administração"
-- Executa: PGPASSWORD=Jvc@1702 psql -h 192.168.11.62 -U postgres -d pro_team_care_11 -f create_b2b_billing_menu.sql

BEGIN;

-- Verificar se o menu pai "Administração" existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM master.menus WHERE id = 20 AND name = 'Administração') THEN
        RAISE EXCEPTION 'Menu pai "Administração" (ID: 20) não encontrado';
    END IF;
END $$;

-- Buscar próximo ID disponível
WITH next_id AS (
    SELECT COALESCE(MAX(id), 0) + 1 AS new_id
    FROM master.menus
)

-- Inserir o menu Faturamento B2B
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
    20,                                     -- parent_id (Administração)
    2,                                      -- level
    30,                                     -- sort_order (após Segurança)
    'Faturamento B2B',                     -- name
    'faturamento-b2b',                     -- slug
    '/admin/faturamento/b2b',              -- url
    'CreditCard',                          -- icon
    'Dashboard de cobrança às empresas clientes',  -- description
    '_self',                               -- target
    'menu',                                -- type
    false,                                 -- accepts_children
    true,                                  -- visible_in_menu
    true,                                  -- visible_in_breadcrumb
    false,                                 -- is_featured
    false,                                 -- company_specific
    false,                                 -- establishment_specific
    true,                                  -- is_active
    true,                                  -- is_visible
    false,                                 -- dev_only
    CURRENT_TIMESTAMP                      -- created_at
FROM next_id;

-- Verificar resultado - mostrar estrutura da Administração
SELECT
    m.id,
    m.parent_id,
    m.level,
    m.sort_order,
    m.slug,
    m.url,
    m.icon,
    m.is_active,
    m.visible_in_menu,
    CASE
        WHEN m.level = 0 THEN m.name
        WHEN m.level = 1 THEN '  └─ ' || m.name
        WHEN m.level = 2 THEN '    └─ ' || m.name
        ELSE '      └─ ' || m.name
    END AS hierarchy_name
FROM master.menus AS m
WHERE
    m.id = 20
    OR m.parent_id = 20
    OR (m.parent_id IN (SELECT id FROM master.menus WHERE parent_id = 20))
ORDER BY
    CASE WHEN m.id = 20 THEN 0 ELSE m.level END,
    m.sort_order,
    m.id;

COMMIT;

-- Mensagem de sucesso
SELECT
    '🎉 Menu "Faturamento B2B" criado com sucesso!' AS resultado,
    'Acesse: /admin/faturamento/b2b' AS url,
    'Visível em: Administração > Faturamento B2B' AS localizacao;
