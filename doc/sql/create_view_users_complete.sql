-- =====================================================
-- SCRIPT: CREATE VIEW USERS COMPLETE
-- =====================================================
-- Creates a view with all users and their relationships
-- Includes: people, companies, establishments and roles
-- Usage: SELECT * FROM master.vw_users_complete;
-- =====================================================

CREATE OR REPLACE VIEW master.vw_users_complete AS
SELECT 
    -- USER DATA (USERS)
    u.id AS user_id,
    u.person_id AS user_person_id,
    u.email_address AS user_email,
    u.email_verified_at AS user_email_verified_at,
    u.is_active AS user_is_active,
    u.is_system_admin AS user_is_system_admin,
    u.preferences AS user_preferences,
    u.notification_settings AS user_notification_settings,
    u.two_factor_secret AS user_two_factor_secret,
    u.two_factor_recovery_codes AS user_two_factor_recovery_codes,
    u.last_login_at AS user_last_login_at,
    u.password_changed_at AS user_password_changed_at,
    u.created_at AS user_created_at,
    u.updated_at AS user_updated_at,
    u.deleted_at AS user_deleted_at,

    -- PERSON DATA (PEOPLE)
    p.id AS person_id,
    p.person_type AS person_type,
    p.name AS person_name,
    p.trade_name AS person_trade_name,
    p.tax_id AS person_tax_id,
    p.secondary_tax_id AS person_secondary_tax_id,
    p.birth_date AS person_birth_date,
    p.gender AS person_gender,
    p.marital_status AS person_marital_status,
    p.occupation AS person_occupation,
    p.incorporation_date AS person_incorporation_date,
    p.tax_regime AS person_tax_regime,
    p.legal_nature AS person_legal_nature,
    p.municipal_registration AS person_municipal_registration,
    p.status AS person_status,
    p.is_active AS person_is_active,
    p.metadata AS person_metadata,
    p.website AS person_website,
    p.description AS person_description,
    p.lgpd_consent_version AS person_lgpd_consent_version,
    p.lgpd_consent_given_at AS person_lgpd_consent_given_at,
    p.lgpd_data_retention_expires_at AS person_lgpd_data_retention_expires_at,
    p.created_at AS person_created_at,
    p.updated_at AS person_updated_at,
    p.deleted_at AS person_deleted_at,

    -- COMPANY DATA (COMPANIES)
    c.id AS company_id,
    c.person_id AS company_person_id,
    c.settings AS company_settings,
    c.metadata AS company_metadata,
    c.display_order AS company_display_order,
    c.created_at AS company_created_at,
    c.updated_at AS company_updated_at,
    c.deleted_at AS company_deleted_at,

    -- ESTABLISHMENT DATA (ESTABLISHMENTS)
    e.id AS establishment_id,
    e.person_id AS establishment_person_id,
    e.company_id AS establishment_company_id,
    e.code AS establishment_code,
    e.type AS establishment_type,
    e.category AS establishment_category,
    e.is_active AS establishment_is_active,
    e.is_principal AS establishment_is_principal,
    e.settings AS establishment_settings,
    e.operating_hours AS establishment_operating_hours,
    e.service_areas AS establishment_service_areas,
    e.created_at AS establishment_created_at,
    e.updated_at AS establishment_updated_at,
    e.deleted_at AS establishment_deleted_at,

    -- USER-ESTABLISHMENT RELATIONSHIP (USER_ESTABLISHMENTS)
    ue.id AS user_establishment_id,
    ue.role_id AS user_establishment_role_id,
    ue.is_primary AS user_establishment_is_primary,
    ue.status AS user_establishment_status,
    ue.assigned_by_user_id AS user_establishment_assigned_by_user_id,
    ue.assigned_at AS user_establishment_assigned_at,
    ue.expires_at AS user_establishment_expires_at,
    ue.permissions AS user_establishment_permissions,
    ue.created_at AS user_establishment_created_at,
    ue.updated_at AS user_establishment_updated_at,
    ue.deleted_at AS user_establishment_deleted_at,

    -- ROLE DATA (ROLES)
    r.id AS role_id,
    r.name AS role_name,
    r.display_name AS role_display_name,
    r.description AS role_description,
    r.level AS role_level,
    r.context_type AS role_context_type,
    r.is_active AS role_is_active,
    r.is_system_role AS role_is_system_role,
    r.settings AS role_settings,
    r.created_at AS role_created_at,
    r.updated_at AS role_updated_at,

    -- USER-ROLE RELATIONSHIP (USER_ROLES)
    ur.id AS user_role_id,
    ur.context_type AS user_role_context_type,
    ur.context_id AS user_role_context_id,
    ur.status AS user_role_status,
    ur.assigned_by_user_id AS user_role_assigned_by_user_id,
    ur.assigned_at AS user_role_assigned_at,
    ur.expires_at AS user_role_expires_at,
    ur.created_at AS user_role_created_at,
    ur.updated_at AS user_role_updated_at,
    ur.deleted_at AS user_role_deleted_at

FROM master.users u

    -- MANDATORY RELATIONSHIP: USER -> PERSON
    INNER JOIN master.people p ON u.person_id = p.id

    -- OPTIONAL RELATIONSHIP: USER -> ESTABLISHMENTS
    LEFT JOIN master.user_establishments ue ON u.id = ue.user_id AND ue.deleted_at IS NULL

    -- OPTIONAL RELATIONSHIP: ESTABLISHMENT -> ESTABLISHMENT DATA
    LEFT JOIN master.establishments e ON ue.establishment_id = e.id AND e.deleted_at IS NULL

    -- OPTIONAL RELATIONSHIP: ESTABLISHMENT -> COMPANY
    LEFT JOIN master.companies c ON e.company_id = c.id AND c.deleted_at IS NULL

    -- OPTIONAL RELATIONSHIP: USER -> ROLES
    LEFT JOIN master.user_roles ur ON u.id = ur.user_id AND ur.deleted_at IS NULL

    -- OPTIONAL RELATIONSHIP: ROLE -> ROLE DATA
    LEFT JOIN master.roles r ON ur.role_id = r.id

WHERE 
    u.deleted_at IS NULL 
    AND p.deleted_at IS NULL

ORDER BY 
    u.id, 
    ue.is_primary DESC NULLS LAST,
    e.is_principal DESC NULLS LAST,
    r.level ASC;

-- =====================================================
-- USAGE EXAMPLES
-- =====================================================

-- List all complete users
-- SELECT * FROM master.vw_users_complete;

-- Active users with companies
-- SELECT user_id, user_email, person_name, company_id, establishment_code, role_name
-- FROM master.vw_users_complete 
-- WHERE user_is_active = true AND company_id IS NOT NULL;

-- Count users by role
-- SELECT role_name, COUNT(DISTINCT user_id) as total_users
-- FROM master.vw_users_complete 
-- WHERE role_name IS NOT NULL
-- GROUP BY role_name;

-- Users without establishment
-- SELECT user_id, user_email, person_name
-- FROM master.vw_users_complete 
-- WHERE establishment_id IS NULL;

-- System admins only
-- SELECT user_id, user_email, person_name, role_display_name
-- FROM master.vw_users_complete 
-- WHERE user_is_system_admin = true;

-- =====================================================
-- VIEW INFORMATION
-- =====================================================
-- Name: master.vw_users_complete
-- Fields: 97 fields (all from related tables)
-- Records: Variable (based on table data)
-- Performance: Use indexes on JOIN columns for better performance
-- Standard: English naming following database table conventions
-- =====================================================