-- =====================================================
-- IMPLEMENTAÇÃO: SISTEMA HIERÁRQUICO DE PERMISSÕES
-- =====================================================
-- Implementa controle de acesso hierárquico completo
-- ROOT > ADMIN EMPRESA > ADMIN ESTABELECIMENTO > USUÁRIO COMUM
-- =====================================================

-- =====================================================
-- 1. FUNÇÃO PRINCIPAL DE CONTROLE HIERÁRQUICO
-- =====================================================

CREATE OR REPLACE FUNCTION master.get_accessible_users_hierarchical(
    requesting_user_id BIGINT
) RETURNS TABLE(
    accessible_user_id BIGINT,
    access_level VARCHAR(20), -- 'full', 'company', 'establishment', 'self'
    reason TEXT
) AS $$
DECLARE
    is_root BOOLEAN;
    user_company_contexts BIGINT[];
    user_establishment_contexts BIGINT[];
    max_company_role_level INTEGER;
    max_establishment_role_level INTEGER;
BEGIN
    -- 1. Verificar se é ROOT/SYSTEM ADMIN
    SELECT is_system_admin INTO is_root
    FROM master.users
    WHERE id = requesting_user_id;

    IF is_root THEN
        -- ROOT: Acesso a todos os usuários
        RETURN QUERY
        SELECT
            u.id,
            'full'::VARCHAR(20),
            'System Administrator - Full Access'::TEXT
        FROM master.users u
        WHERE u.deleted_at IS NULL;
        RETURN;
    END IF;

    -- 2. Buscar contextos do usuário (empresas e estabelecimentos)
    SELECT
        ARRAY_AGG(DISTINCT ur.context_id) FILTER (WHERE ur.context_type = 'company'),
        ARRAY_AGG(DISTINCT ur.context_id) FILTER (WHERE ur.context_type = 'establishment'),
        MAX(r.level) FILTER (WHERE ur.context_type = 'company'),
        MAX(r.level) FILTER (WHERE ur.context_type = 'establishment')
    INTO
        user_company_contexts,
        user_establishment_contexts,
        max_company_role_level,
        max_establishment_role_level
    FROM master.user_roles ur
    JOIN master.roles r ON ur.role_id = r.id
    WHERE ur.user_id = requesting_user_id
      AND ur.deleted_at IS NULL;

    -- 3. ADMIN EMPRESA (Level 80+): Acesso a usuários de todas empresas que administra
    IF max_company_role_level >= 80 AND user_company_contexts IS NOT NULL THEN
        RETURN QUERY
        SELECT DISTINCT
            u.id,
            'company'::VARCHAR(20),
            ('Company Administrator - Access to Company ' || c.id)::TEXT
        FROM master.users u
        JOIN master.user_establishments ue ON u.id = ue.user_id
        JOIN master.establishments e ON ue.establishment_id = e.id
        JOIN master.companies c ON e.company_id = c.id
        WHERE c.id = ANY(user_company_contexts)
          AND u.deleted_at IS NULL
          AND ue.deleted_at IS NULL
          AND e.deleted_at IS NULL
          AND c.deleted_at IS NULL;

        -- Incluir usuários sem estabelecimento da mesma empresa
        RETURN QUERY
        SELECT DISTINCT
            u.id,
            'company'::VARCHAR(20),
            ('Company Administrator - Direct Company User')::TEXT
        FROM master.users u
        JOIN master.user_roles ur ON u.id = ur.user_id
        WHERE ur.context_type = 'company'
          AND ur.context_id = ANY(user_company_contexts)
          AND ur.deleted_at IS NULL
          AND u.deleted_at IS NULL
          AND u.id NOT IN (
              SELECT DISTINCT u2.id
              FROM master.users u2
              JOIN master.user_establishments ue2 ON u2.id = ue2.user_id
              WHERE ue2.deleted_at IS NULL
          );
        RETURN;
    END IF;

    -- 4. ADMIN ESTABELECIMENTO (Level 60-79): Acesso apenas a usuários dos estabelecimentos
    IF max_establishment_role_level >= 60 AND user_establishment_contexts IS NOT NULL THEN
        RETURN QUERY
        SELECT DISTINCT
            u.id,
            'establishment'::VARCHAR(20),
            ('Establishment Administrator - Access to Establishment ' || e.id)::TEXT
        FROM master.users u
        JOIN master.user_establishments ue ON u.id = ue.user_id
        JOIN master.establishments e ON ue.establishment_id = e.id
        WHERE e.id = ANY(user_establishment_contexts)
          AND u.deleted_at IS NULL
          AND ue.deleted_at IS NULL
          AND e.deleted_at IS NULL;
        RETURN;
    END IF;

    -- 5. USUÁRIO COMUM: Apenas próprios dados + colegas do estabelecimento
    RETURN QUERY
    SELECT
        requesting_user_id,
        'self'::VARCHAR(20),
        'Own Data Access'::TEXT
    UNION
    SELECT DISTINCT
        colleague.id,
        'establishment'::VARCHAR(20),
        ('Colleague in Establishment ' || e.id)::TEXT
    FROM master.users colleague
    JOIN master.user_establishments ue ON colleague.id = ue.user_id
    JOIN master.establishments e ON ue.establishment_id = e.id
    WHERE e.id IN (
        SELECT DISTINCT e2.id
        FROM master.user_establishments ue2
        JOIN master.establishments e2 ON ue2.establishment_id = e2.id
        WHERE ue2.user_id = requesting_user_id
          AND ue2.deleted_at IS NULL
    )
    AND colleague.deleted_at IS NULL
    AND ue.deleted_at IS NULL
    AND e.deleted_at IS NULL;

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 2. VIEW HIERÁRQUICA PARA CLASSIFICAÇÃO DE USUÁRIOS
-- =====================================================

CREATE OR REPLACE VIEW master.vw_users_hierarchical AS
SELECT
    vc.user_id,
    vc.user_email,
    vc.user_is_active,
    vc.user_is_system_admin,
    vc.person_name,
    vc.company_id,
    vc.establishment_code,
    vc.role_name,
    vc.role_display_name,
    vc.role_level,

    -- Classificação hierárquica
    CASE
        WHEN vc.user_is_system_admin THEN 'ROOT'
        WHEN EXISTS(
            SELECT 1 FROM master.user_roles ur2
            JOIN master.roles r2 ON ur2.role_id = r2.id
            WHERE ur2.user_id = vc.user_id
              AND r2.context_type = 'company'
              AND r2.level >= 80
              AND ur2.deleted_at IS NULL
        ) THEN 'ADMIN_EMPRESA'
        WHEN EXISTS(
            SELECT 1 FROM master.user_roles ur3
            JOIN master.roles r3 ON ur3.role_id = r3.id
            WHERE ur3.user_id = vc.user_id
              AND r3.context_type = 'establishment'
              AND r3.level >= 60
              AND ur3.deleted_at IS NULL
        ) THEN 'ADMIN_ESTABELECIMENTO'
        ELSE 'USUARIO_COMUM'
    END as hierarchy_level,

    -- Contextos de acesso (empresas)
    (SELECT ARRAY_AGG(DISTINCT ur4.context_id::text)
     FROM master.user_roles ur4
     JOIN master.roles r4 ON ur4.role_id = r4.id
     WHERE ur4.user_id = vc.user_id
       AND r4.context_type = 'company'
       AND ur4.deleted_at IS NULL
    ) as accessible_companies,

    -- Contextos de acesso (estabelecimentos)
    (SELECT ARRAY_AGG(DISTINCT ur5.context_id::text)
     FROM master.user_roles ur5
     JOIN master.roles r5 ON ur5.role_id = r5.id
     WHERE ur5.user_id = vc.user_id
       AND r5.context_type = 'establishment'
       AND ur5.deleted_at IS NULL
    ) as accessible_establishments

FROM master.vw_users_complete vc
WHERE vc.user_is_active = true
GROUP BY
    vc.user_id, vc.user_email, vc.user_is_active, vc.user_is_system_admin,
    vc.person_name, vc.company_id, vc.establishment_code,
    vc.role_name, vc.role_display_name, vc.role_level
ORDER BY
    CASE
        WHEN vc.user_is_system_admin THEN 1
        WHEN EXISTS(SELECT 1 FROM master.user_roles ur JOIN master.roles r ON ur.role_id = r.id WHERE ur.user_id = vc.user_id AND r.level >= 80 AND ur.deleted_at IS NULL) THEN 2
        WHEN EXISTS(SELECT 1 FROM master.user_roles ur JOIN master.roles r ON ur.role_id = r.id WHERE ur.user_id = vc.user_id AND r.level >= 60 AND ur.deleted_at IS NULL) THEN 3
        ELSE 4
    END,
    vc.person_name;

-- =====================================================
-- 3. VIEWS SEGURAS PARA DIFERENTES NÍVEIS
-- =====================================================

-- View pública (dados básicos, sem informações sensíveis)
CREATE OR REPLACE VIEW master.vw_users_public AS
SELECT
    user_id, user_email, user_is_active,
    person_name, person_type, person_status,
    company_id, establishment_code,
    role_name, role_display_name
FROM master.vw_users_complete
WHERE user_is_active = true
  AND user_deleted_at IS NULL;

-- View administrativa (com dados mascarados)
CREATE OR REPLACE VIEW master.vw_users_admin AS
SELECT
    user_id, user_email, user_is_active, user_is_system_admin,
    user_last_login_at, user_created_at,
    person_name, person_tax_id, person_status,
    company_id, establishment_code, establishment_type,
    role_name, role_display_name, role_level,
    -- Campos mascarados de segurança
    CASE
        WHEN user_two_factor_secret IS NOT NULL THEN 'CONFIGURED'
        ELSE 'NOT_CONFIGURED'
    END as two_factor_status,
    CASE
        WHEN user_two_factor_recovery_codes IS NOT NULL THEN 'AVAILABLE'
        ELSE 'NOT_AVAILABLE'
    END as recovery_codes_status
FROM master.vw_users_complete
WHERE user_deleted_at IS NULL;

-- =====================================================
-- 4. FUNÇÃO PARA VERIFICAR PERMISSÃO ESPECÍFICA
-- =====================================================

-- Função antiga (mantida para compatibilidade)
CREATE OR REPLACE FUNCTION master.check_user_permission(
    requesting_user_id BIGINT,
    target_user_id BIGINT,
    required_permission TEXT DEFAULT 'read'
) RETURNS BOOLEAN AS $$
DECLARE
    has_access BOOLEAN := FALSE;
BEGIN
    -- Verificar se tem acesso ao usuário
    SELECT COUNT(*) > 0 INTO has_access
    FROM master.get_accessible_users_hierarchical(requesting_user_id)
    WHERE accessible_user_id = target_user_id;

    RETURN has_access;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Nova função para verificar permissões específicas (compatível com SecurityService)
CREATE OR REPLACE FUNCTION master.check_user_permission_v2(
    user_id BIGINT,
    permission TEXT,
    context_type TEXT DEFAULT 'establishment',
    context_id BIGINT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    is_sys_admin BOOLEAN := FALSE;
    user_role_level INTEGER := 0;
    has_permission BOOLEAN := FALSE;
BEGIN
    -- 1. Verificar se é system admin (acesso total)
    SELECT u.is_system_admin INTO is_sys_admin
    FROM master.users u
    WHERE u.id = user_id AND u.deleted_at IS NULL;

    IF is_sys_admin THEN
        RETURN TRUE;
    END IF;

    -- 2. Verificar nível de role baseado no contexto
    IF context_type = 'establishment' AND context_id IS NOT NULL THEN
        SELECT COALESCE(MAX(r.level), 0) INTO user_role_level
        FROM master.user_roles ur
        JOIN master.roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_id
          AND ur.context_type = 'establishment'
          AND ur.context_id = context_id
          AND ur.deleted_at IS NULL;
    ELSIF context_type = 'company' AND context_id IS NOT NULL THEN
        SELECT COALESCE(MAX(r.level), 0) INTO user_role_level
        FROM master.user_roles ur
        JOIN master.roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_id
          AND ur.context_type = 'company'
          AND ur.context_id = context_id
          AND ur.deleted_at IS NULL;
    ELSE
        -- Contexto global ou sem contexto específico
        SELECT COALESCE(MAX(r.level), 0) INTO user_role_level
        FROM master.user_roles ur
        JOIN master.roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_id
          AND ur.deleted_at IS NULL;
    END IF;

    -- 3. Verificar permissões baseadas no tipo e nível
    CASE permission
        WHEN 'users.list' THEN
            -- Admin de estabelecimento (level >= 60) ou admin de empresa (level >= 80)
            has_permission := user_role_level >= 60;
        WHEN 'users.view' THEN
            has_permission := user_role_level >= 40;
        WHEN 'users.create' THEN
            has_permission := user_role_level >= 80;
        WHEN 'users.edit' THEN
            has_permission := user_role_level >= 60;
        WHEN 'users.delete' THEN
            has_permission := user_role_level >= 80;
        WHEN 'companies.list' THEN
            has_permission := user_role_level >= 60;
        WHEN 'companies.view' THEN
            has_permission := user_role_level >= 40;
        WHEN 'companies.create' THEN
            has_permission := user_role_level >= 80;
        WHEN 'companies.edit' THEN
            has_permission := user_role_level >= 80;
        WHEN 'establishments.list' THEN
            has_permission := user_role_level >= 40;
        WHEN 'establishments.view' THEN
            has_permission := user_role_level >= 40;
        WHEN 'establishments.create' THEN
            has_permission := user_role_level >= 80;
        WHEN 'establishments.edit' THEN
            has_permission := user_role_level >= 60;
        ELSE
            -- Permissão desconhecida - negar acesso
            has_permission := FALSE;
    END CASE;

    RETURN has_permission;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 5. ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índices para otimizar as consultas hierárquicas
CREATE INDEX IF NOT EXISTS idx_user_roles_context_type_id ON master.user_roles(context_type, context_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_roles_context_level ON master.roles(context_type, level);
CREATE INDEX IF NOT EXISTS idx_user_establishments_user_est ON master.user_establishments(user_id, establishment_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_establishments_company ON master.establishments(company_id) WHERE deleted_at IS NULL;

-- =====================================================
-- 6. COMENTÁRIOS E DOCUMENTAÇÃO
-- =====================================================

COMMENT ON FUNCTION master.get_accessible_users_hierarchical(BIGINT) IS
'Retorna lista de usuários acessíveis baseado na hierarquia de permissões do solicitante';

COMMENT ON VIEW master.vw_users_hierarchical IS
'View com classificação hierárquica de usuários e seus contextos de acesso';

COMMENT ON VIEW master.vw_users_public IS
'View pública com dados básicos de usuários, sem informações sensíveis';

COMMENT ON VIEW master.vw_users_admin IS
'View administrativa com dados mascarados para administradores';

COMMENT ON FUNCTION master.check_user_permission(BIGINT, BIGINT, TEXT) IS
'Verifica se um usuário tem permissão para acessar dados de outro usuário';

-- =====================================================
-- SCRIPT CONCLUÍDO
-- =====================================================
-- Para aplicar: psql -d pro_team_care_11 -f 001_create_hierarchical_functions.sql
-- =====================================================
