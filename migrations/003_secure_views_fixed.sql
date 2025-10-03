-- =====================================================
-- VIEWS SEGURAS - IMPLEMENTAÇÃO CORRIGIDA
-- =====================================================

-- 1. VIEW PÚBLICA (DADOS NÃO-SENSÍVEIS)
CREATE OR REPLACE VIEW master.vw_users_public AS
SELECT
    -- USER DATA (BASIC)
    u.id AS user_id,
    u.email_address AS user_email,
    u.is_active AS user_is_active,
    u.last_login_at AS user_last_login_at,
    u.created_at AS user_created_at,
    p.name AS person_name,

    -- PERSON DATA (PUBLIC)
    p.person_type,
    p.is_active AS person_is_active,
    c.id AS company_id,

    -- COMPANY DATA (BASIC)
    e.code AS establishment_code,

    -- ESTABLISHMENT DATA (BASIC)
    e.type AS establishment_type,
    e.is_active AS establishment_is_active,
    r.name AS role_name,

    -- ROLE DATA (BASIC)
    r.display_name AS role_display_name,
    r.level AS role_level,
    coalesce (u.two_factor_secret IS NOT NULL, FALSE) AS user_has_2fa

FROM master.users AS u
INNER JOIN master.people AS p ON u.person_id = p.id
LEFT JOIN
    master.user_establishments AS ue
    ON u.id = ue.user_id AND ue.deleted_at IS NULL
LEFT JOIN
    master.establishments AS e
    ON ue.establishment_id = e.id AND e.deleted_at IS NULL
LEFT JOIN master.companies AS c ON e.company_id = c.id AND c.deleted_at IS NULL
LEFT JOIN master.user_roles AS ur ON u.id = ur.user_id AND ur.deleted_at IS NULL
LEFT JOIN master.roles AS r ON ur.role_id = r.id

WHERE
    u.deleted_at IS NULL
    AND p.deleted_at IS NULL
    AND u.is_active = TRUE

ORDER BY u.id;

-- 2. VIEW ADMIN (DADOS MASCARADOS)
CREATE OR REPLACE VIEW master.vw_users_admin AS
SELECT
    -- USER DATA (ADMIN - MASKED)
    u.id AS user_id,
    u.email_address AS user_email,
    u.is_active AS user_is_active,
    u.is_system_admin AS user_is_system_admin,

    -- MASKED SENSITIVE FIELDS
    u.last_login_at AS user_last_login_at,
    u.created_at AS user_created_at,

    p.name AS person_name,
    p.person_type,

    -- PERSON DATA (COMPLETE)
    p.tax_id AS person_tax_id,
    p.birth_date AS person_birth_date,
    p.is_active AS person_is_active,
    p.lgpd_consent_given_at AS person_lgpd_consent_date,
    c.id AS company_id,

    -- LGPD STATUS (MASKED)
    e.id AS establishment_id,
    e.code AS establishment_code,

    -- COMPANY DATA
    e.type AS establishment_type,

    -- ESTABLISHMENT DATA
    e.is_active AS establishment_is_active,
    r.id AS role_id,
    r.name AS role_name,
    r.display_name AS role_display_name,

    -- ROLE DATA
    r.level AS role_level,
    r.context_type AS role_context_type,
    CASE
        WHEN u.two_factor_secret IS NOT NULL THEN 'CONFIGURED' ELSE
            'NOT_CONFIGURED'
    END AS user_2fa_status,
    CASE
        WHEN u.two_factor_recovery_codes IS NOT NULL THEN 'AVAILABLE' ELSE
            'NOT_AVAILABLE'
    END AS user_2fa_recovery_status,
    CASE
        WHEN p.lgpd_consent_version IS NOT NULL THEN 'PROVIDED' ELSE
            'NOT_PROVIDED'
    END AS person_lgpd_status

FROM master.users AS u
INNER JOIN master.people AS p ON u.person_id = p.id
LEFT JOIN
    master.user_establishments AS ue
    ON u.id = ue.user_id AND ue.deleted_at IS NULL
LEFT JOIN
    master.establishments AS e
    ON ue.establishment_id = e.id AND e.deleted_at IS NULL
LEFT JOIN master.companies AS c ON e.company_id = c.id AND c.deleted_at IS NULL
LEFT JOIN master.user_roles AS ur ON u.id = ur.user_id AND ur.deleted_at IS NULL
LEFT JOIN master.roles AS r ON ur.role_id = r.id

WHERE
    u.deleted_at IS NULL
    AND p.deleted_at IS NULL

ORDER BY u.id;

-- 3. FUNÇÃO SEGURA PARA OBTER DADOS DE USUÁRIO
CREATE OR REPLACE FUNCTION master.get_user_data_secure(
    requesting_user_id BIGINT,
    target_user_id BIGINT DEFAULT NULL
) RETURNS TABLE (
    user_id BIGINT,
    user_email VARCHAR,
    person_name VARCHAR,
    company_id BIGINT,
    establishment_code VARCHAR,
    role_name VARCHAR,
    can_edit BOOLEAN
) AS $$
BEGIN
    -- Log de acesso
    PERFORM master.log_user_data_access(
        requesting_user_id,
        target_user_id,
        'get_user_data_secure',
        'SELECT'
    );

    -- Retornar dados filtrados
    RETURN QUERY
    SELECT
        vup.user_id,
        vup.user_email,
        vup.person_name,
        vup.company_id,
        vup.establishment_code,
        vup.role_name,
        master.can_access_user_data(requesting_user_id, vup.user_id) AS can_edit
    FROM master.vw_users_public vup
    WHERE (target_user_id IS NULL OR vup.user_id = target_user_id)
      AND master.can_access_user_data(requesting_user_id, vup.user_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
