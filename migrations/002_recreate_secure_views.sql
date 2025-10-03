-- =====================================================
-- RECRIAR VIEWS SEGURAS
-- =====================================================

-- View pública (dados básicos, sem informações sensíveis)
CREATE VIEW master.vw_users_public AS
SELECT
    user_id,
    user_email,
    user_is_active,
    person_name,
    person_type,
    person_status,
    company_id,
    establishment_code,
    role_name,
    role_display_name
FROM master.vw_users_complete
WHERE
    user_is_active = true
    AND user_deleted_at IS null;

-- View administrativa (com dados mascarados)
CREATE VIEW master.vw_users_admin AS
SELECT
    user_id,
    user_email,
    user_is_active,
    user_is_system_admin,
    user_last_login_at,
    user_created_at,
    person_name,
    person_tax_id,
    person_status,
    company_id,
    establishment_code,
    establishment_type,
    role_name,
    role_display_name,
    role_level,
    -- Campos mascarados de segurança
    CASE
        WHEN user_two_factor_secret IS NOT null THEN 'CONFIGURED'
        ELSE 'NOT_CONFIGURED'
    END AS two_factor_status,
    CASE
        WHEN user_two_factor_recovery_codes IS NOT null THEN 'AVAILABLE'
        ELSE 'NOT_AVAILABLE'
    END AS recovery_codes_status
FROM master.vw_users_complete
WHERE user_deleted_at IS null;
