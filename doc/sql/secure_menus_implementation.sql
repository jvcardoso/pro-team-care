-- =====================================================
-- SISTEMA SEGURO DE MENUS - VIEWS E OTIMIZAÇÕES
-- =====================================================
-- Implementa views seguras para menus seguindo padrão de usuários
-- Inclui controle hierárquico, contexto e permissões
-- =====================================================

-- =====================================================
-- 1. VIEW PÚBLICA DE MENUS (FILTRADA POR PERMISSÕES)
-- =====================================================
CREATE OR REPLACE VIEW master.vw_menus_public AS
SELECT 
    -- DADOS BÁSICOS DO MENU
    m.id AS menu_id,
    m.parent_id AS menu_parent_id,
    m.level AS menu_level,
    m.sort_order AS menu_sort_order,
    m.name AS menu_name,
    m.slug AS menu_slug,
    m.url AS menu_url,
    m.route_name AS menu_route_name,
    m.route_params AS menu_route_params,
    m.icon AS menu_icon,
    m.color AS menu_color,
    m.description AS menu_description,
    m.target AS menu_target,
    m.type AS menu_type,
    
    -- CONFIGURAÇÕES DE EXIBIÇÃO
    m.visible_in_menu AS menu_visible_in_menu,
    m.visible_in_breadcrumb AS menu_visible_in_breadcrumb,
    m.is_featured AS menu_is_featured,
    
    -- BADGE (se não sensível)
    CASE 
        WHEN m.badge_text IS NOT NULL AND LENGTH(m.badge_text) < 50 
        THEN m.badge_text 
        ELSE NULL 
    END AS menu_badge_text,
    m.badge_color AS menu_badge_color,
    
    -- CONTEXTO (SEM DADOS SENSÍVEIS)
    m.company_specific AS menu_company_specific,
    m.establishment_specific AS menu_establishment_specific,
    
    -- STATUS PÚBLICO
    m.is_active AS menu_is_active,
    m.is_visible AS menu_is_visible,
    m.created_at AS menu_created_at

FROM master.menus m
WHERE m.deleted_at IS NULL
  AND m.is_active = true
  AND m.is_visible = true
  AND m.dev_only = false  -- Não mostrar menus de desenvolvimento

ORDER BY m.level ASC, m.sort_order ASC;

-- =====================================================
-- 2. VIEW ADMIN DE MENUS (COM CONTROLE DE ACESSO)
-- =====================================================
CREATE OR REPLACE VIEW master.vw_menus_admin AS
SELECT 
    -- DADOS COMPLETOS DO MENU
    m.id AS menu_id,
    m.parent_id AS menu_parent_id,
    m.level AS menu_level,
    m.sort_order AS menu_sort_order,
    m.name AS menu_name,
    m.slug AS menu_slug,
    m.path AS menu_path,
    m.url AS menu_url,
    m.route_name AS menu_route_name,
    m.route_params AS menu_route_params,
    m.icon AS menu_icon,
    m.color AS menu_color,
    m.description AS menu_description,
    m.target AS menu_target,
    m.type AS menu_type,
    m.accepts_children AS menu_accepts_children,
    
    -- BADGE COMPLETO
    m.badge_text AS menu_badge_text,
    m.badge_color AS menu_badge_color,
    m.badge_expression AS menu_badge_expression,
    
    -- CONFIGURAÇÕES DE EXIBIÇÃO
    m.visible_in_menu AS menu_visible_in_menu,
    m.visible_in_breadcrumb AS menu_visible_in_breadcrumb,
    m.is_featured AS menu_is_featured,
    
    -- CONTROLE DE ACESSO (MASCARADO)
    CASE WHEN m.permission_name IS NOT NULL THEN 'HAS_PERMISSION' ELSE 'NO_PERMISSION' END AS menu_permission_status,
    CASE WHEN m.required_permissions IS NOT NULL THEN 'HAS_REQUIRED_PERMISSIONS' ELSE 'NO_REQUIRED_PERMISSIONS' END AS menu_required_permissions_status,
    CASE WHEN m.required_roles IS NOT NULL THEN 'HAS_REQUIRED_ROLES' ELSE 'NO_REQUIRED_ROLES' END AS menu_required_roles_status,
    
    -- CONTEXTO DETALHADO
    m.company_specific AS menu_company_specific,
    CASE WHEN m.allowed_companies IS NOT NULL THEN 'HAS_ALLOWED_COMPANIES' ELSE NULL END AS menu_allowed_companies_status,
    m.establishment_specific AS menu_establishment_specific,
    CASE WHEN m.allowed_establishments IS NOT NULL THEN 'HAS_ALLOWED_ESTABLISHMENTS' ELSE NULL END AS menu_allowed_establishments_status,
    
    -- METADADOS (RESUMO)
    CASE WHEN m.metadata IS NOT NULL THEN 'HAS_METADATA' ELSE NULL END AS menu_metadata_status,
    
    -- STATUS COMPLETO
    m.is_active AS menu_is_active,
    m.is_visible AS menu_is_visible,
    m.dev_only AS menu_dev_only,
    
    -- AUDITORIA
    m.created_at AS menu_created_at,
    m.updated_at AS menu_updated_at,
    m.created_by_user_id AS menu_created_by_user_id,
    m.updated_by_user_id AS menu_updated_by_user_id

FROM master.menus m
WHERE m.deleted_at IS NULL

ORDER BY m.level ASC, m.sort_order ASC;

-- =====================================================
-- 3. VIEW HIERÁRQUICA DE MENUS
-- =====================================================
CREATE OR REPLACE VIEW master.vw_menus_hierarchy AS
WITH RECURSIVE menu_hierarchy AS (
    -- Menus raiz (level 0)
    SELECT 
        m.id,
        m.parent_id,
        m.level,
        m.name,
        m.slug,
        m.url,
        m.sort_order,
        m.is_active,
        m.is_visible,
        ARRAY[m.id] as path_ids,
        m.name as path_names,
        0 as depth
    FROM master.menus m
    WHERE m.parent_id IS NULL 
      AND m.deleted_at IS NULL
    
    UNION ALL
    
    -- Menus filhos (recursivo)
    SELECT 
        m.id,
        m.parent_id,
        m.level,
        m.name,
        m.slug,
        m.url,
        m.sort_order,
        m.is_active,
        m.is_visible,
        mh.path_ids || m.id,
        mh.path_names || ' > ' || m.name,
        mh.depth + 1
    FROM master.menus m
    INNER JOIN menu_hierarchy mh ON m.parent_id = mh.id
    WHERE m.deleted_at IS NULL
      AND mh.depth < 10  -- Limitar recursão
)
SELECT 
    id AS menu_id,
    parent_id AS menu_parent_id,
    level AS menu_level,
    name AS menu_name,
    slug AS menu_slug,
    url AS menu_url,
    sort_order AS menu_sort_order,
    is_active AS menu_is_active,
    is_visible AS menu_is_visible,
    depth AS menu_depth,
    path_ids AS menu_path_ids,
    path_names AS menu_full_path
FROM menu_hierarchy
ORDER BY path_ids;

-- =====================================================
-- 4. FUNÇÃO PARA MENUS ACESSÍVEIS POR USUÁRIO
-- =====================================================
CREATE OR REPLACE FUNCTION master.get_accessible_menus(
    user_id_param BIGINT,
    context_type_param VARCHAR(50) DEFAULT NULL,
    context_id_param BIGINT DEFAULT NULL
) RETURNS TABLE(
    menu_id BIGINT,
    menu_name VARCHAR,
    menu_url VARCHAR,
    menu_level INTEGER,
    menu_sort_order INTEGER,
    menu_icon VARCHAR,
    menu_parent_id BIGINT,
    is_accessible BOOLEAN,
    access_reason TEXT
) AS $$
DECLARE
    is_system_admin BOOLEAN;
    user_roles TEXT[];
    user_companies BIGINT[];
    user_establishments BIGINT[];
BEGIN
    -- 1. Verificar se é system admin
    SELECT is_system_admin INTO is_system_admin
    FROM master.users 
    WHERE id = user_id_param;
    
    -- 2. Buscar roles do usuário
    SELECT ARRAY_AGG(r.name) INTO user_roles
    FROM master.user_roles ur
    JOIN master.roles r ON ur.role_id = r.id
    WHERE ur.user_id = user_id_param 
      AND ur.deleted_at IS NULL;
    
    -- 3. Buscar empresas do usuário
    SELECT ARRAY_AGG(DISTINCT e.company_id) INTO user_companies
    FROM master.user_establishments ue
    JOIN master.establishments e ON ue.establishment_id = e.id
    WHERE ue.user_id = user_id_param 
      AND ue.deleted_at IS NULL
      AND e.deleted_at IS NULL;
    
    -- 4. Buscar estabelecimentos do usuário
    SELECT ARRAY_AGG(DISTINCT ue.establishment_id) INTO user_establishments
    FROM master.user_establishments ue
    WHERE ue.user_id = user_id_param 
      AND ue.deleted_at IS NULL;
    
    -- 5. Retornar menus acessíveis
    RETURN QUERY
    SELECT 
        m.id,
        m.name,
        m.url,
        m.level,
        m.sort_order,
        m.icon,
        m.parent_id,
        CASE
            -- System admin vê tudo (exceto dev_only se não especificado)
            WHEN is_system_admin AND NOT m.dev_only THEN true
            
            -- Menu global sem restrições específicas
            WHEN NOT m.company_specific AND NOT m.establishment_specific 
                 AND m.required_roles IS NULL THEN true
            
            -- Menu específico de empresa
            WHEN m.company_specific AND user_companies IS NOT NULL 
                 AND (m.allowed_companies IS NULL 
                      OR EXISTS(SELECT 1 FROM jsonb_array_elements_text(m.allowed_companies) AS allowed_company
                               WHERE allowed_company::BIGINT = ANY(user_companies))) THEN true
            
            -- Menu específico de estabelecimento  
            WHEN m.establishment_specific AND user_establishments IS NOT NULL
                 AND (m.allowed_establishments IS NULL
                      OR EXISTS(SELECT 1 FROM jsonb_array_elements_text(m.allowed_establishments) AS allowed_establishment
                               WHERE allowed_establishment::BIGINT = ANY(user_establishments))) THEN true
            
            -- Menu com roles requeridos
            WHEN m.required_roles IS NOT NULL AND user_roles IS NOT NULL
                 AND EXISTS(SELECT 1 FROM jsonb_array_elements_text(m.required_roles) AS required_role
                           WHERE required_role = ANY(user_roles)) THEN true
            
            ELSE false
        END,
        CASE
            WHEN is_system_admin THEN 'System Administrator Access'
            WHEN NOT m.company_specific AND NOT m.establishment_specific THEN 'Global Menu Access'
            WHEN m.company_specific THEN 'Company Context Access'
            WHEN m.establishment_specific THEN 'Establishment Context Access'
            WHEN m.required_roles IS NOT NULL THEN 'Role-based Access'
            ELSE 'Access Denied'
        END
    FROM master.menus m
    WHERE m.deleted_at IS NULL
      AND m.is_active = true
      AND m.is_visible = true
    ORDER BY m.level, m.sort_order;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 5. VIEW DE MENUS POR CONTEXTO DO USUÁRIO
-- =====================================================
CREATE OR REPLACE VIEW master.vw_menus_by_context AS
SELECT 
    m.id AS menu_id,
    m.name AS menu_name,
    m.level AS menu_level,
    m.parent_id AS menu_parent_id,
    
    -- Classificação de contexto
    CASE 
        WHEN m.company_specific = true THEN 'COMPANY'
        WHEN m.establishment_specific = true THEN 'ESTABLISHMENT'
        WHEN m.required_roles IS NOT NULL THEN 'ROLE_BASED'
        ELSE 'GLOBAL'
    END AS menu_context_type,
    
    -- Contadores de restrições
    CASE WHEN m.allowed_companies IS NOT NULL THEN jsonb_array_length(m.allowed_companies) ELSE 0 END AS allowed_companies_count,
    CASE WHEN m.allowed_establishments IS NOT NULL THEN jsonb_array_length(m.allowed_establishments) ELSE 0 END AS allowed_establishments_count,
    CASE WHEN m.required_roles IS NOT NULL THEN jsonb_array_length(m.required_roles) ELSE 0 END AS required_roles_count,
    
    -- Status de acesso
    NOT (m.company_specific OR m.establishment_specific OR m.required_roles IS NOT NULL) AS is_public_access,
    m.is_active AND m.is_visible AS is_available,
    
    m.sort_order AS menu_sort_order,
    m.created_at AS menu_created_at

FROM master.menus m
WHERE m.deleted_at IS NULL

ORDER BY 
    CASE 
        WHEN m.company_specific = true THEN 1
        WHEN m.establishment_specific = true THEN 2
        WHEN m.required_roles IS NOT NULL THEN 3
        ELSE 4
    END,
    m.level, 
    m.sort_order;

-- =====================================================
-- 6. ÍNDICES ADICIONAIS RECOMENDADOS
-- =====================================================

-- Otimizar função get_accessible_menus
CREATE INDEX IF NOT EXISTS idx_menus_access_optimization 
ON master.menus (is_active, is_visible, deleted_at, company_specific, establishment_specific)
WHERE deleted_at IS NULL;

-- Otimizar consultas por contexto
CREATE INDEX IF NOT EXISTS idx_menus_context_lookup
ON master.menus (company_specific, establishment_specific, deleted_at)
INCLUDE (id, name, level, sort_order)
WHERE deleted_at IS NULL;

-- Otimizar busca hierárquica
CREATE INDEX IF NOT EXISTS idx_menus_hierarchy_optimization
ON master.menus (parent_id, level, sort_order, is_active)
WHERE deleted_at IS NULL;

-- =====================================================
-- 7. SISTEMA DE AUDITORIA DE ACESSO A MENUS
-- =====================================================
CREATE TABLE IF NOT EXISTS master.menu_access_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    menu_id BIGINT NOT NULL,
    access_type VARCHAR(50) NOT NULL, -- 'VIEW', 'CLICK', 'LOAD'
    context_type VARCHAR(50), -- 'company', 'establishment', 'global'
    context_id BIGINT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_menu_access_log_user FOREIGN KEY (user_id) REFERENCES master.users(id),
    CONSTRAINT fk_menu_access_log_menu FOREIGN KEY (menu_id) REFERENCES master.menus(id)
);

-- Índices para auditoria de menus
CREATE INDEX IF NOT EXISTS idx_menu_access_log_user_date 
ON master.menu_access_log (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_menu_access_log_menu_date 
ON master.menu_access_log (menu_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_menu_access_log_cleanup 
ON master.menu_access_log (created_at)
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- =====================================================
-- 8. EXEMPLOS DE USO
-- =====================================================

/*
-- 1. Obter menus públicos
SELECT * FROM master.vw_menus_public;

-- 2. Obter menus para admin (dados mascarados)
SELECT * FROM master.vw_menus_admin WHERE menu_level <= 1;

-- 3. Ver hierarquia completa
SELECT * FROM master.vw_menus_hierarchy;

-- 4. Menus acessíveis para usuário específico
SELECT * FROM master.get_accessible_menus(2);  -- User ID 2

-- 5. Menus por contexto
SELECT menu_context_type, COUNT(*) as menu_count
FROM master.vw_menus_by_context
GROUP BY menu_context_type;

-- 6. Log de acesso a menu (exemplo de inserção)
INSERT INTO master.menu_access_log (user_id, menu_id, access_type, context_type, context_id)
VALUES (2, 1, 'VIEW', 'global', NULL);
*/