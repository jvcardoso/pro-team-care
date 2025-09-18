-- Script simples para criar menu Notificações
-- USE ESTE no DBeaver:

INSERT INTO master.menus (
    parent_id, level, sort_order, name, slug, url, icon, description,
    target, type, accepts_children, visible_in_menu, visible_in_breadcrumb,
    is_featured, company_specific, establishment_specific,
    is_active, is_visible, dev_only, created_at
) VALUES (
    100,                                    -- parent_id
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
);
