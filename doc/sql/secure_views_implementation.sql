-- =====================================================
-- SECURITY IMPLEMENTATION FOR USER VIEWS
-- =====================================================
-- Implements secure views based on security analysis
-- Addresses critical vulnerabilities while maintaining functionality
-- =====================================================

-- =====================================================
-- 1. PUBLIC VIEW (NON-SENSITIVE DATA ONLY)
-- =====================================================
CREATE OR REPLACE VIEW master.vw_users_public AS
SELECT 
    -- BASIC USER DATA (NON-SENSITIVE)
    u.id AS user_id,
    u.person_id AS user_person_id,
    u.email_address AS user_email,
    u.is_active AS user_is_active,
    CASE WHEN u.two_factor_secret IS NOT NULL THEN true ELSE false END AS user_has_2fa,
    u.last_login_at AS user_last_login_at,
    u.created_at AS user_created_at,

    -- PERSON DATA (PUBLIC INFO)
    p.id AS person_id,
    p.person_type AS person_type,
    p.name AS person_name,
    p.trade_name AS person_trade_name,
    -- MASKED TAX ID (show only last 4 digits for individuals)
    CASE 
        WHEN p.person_type = 'individual' THEN 
            CONCAT('***.**.***.', RIGHT(p.tax_id, 4))
        ELSE p.tax_id -- Companies keep full CNPJ
    END AS person_tax_id_masked,
    p.birth_date AS person_birth_date,
    p.gender AS person_gender,
    p.occupation AS person_occupation,
    p.is_active AS person_is_active,
    p.website AS person_website,

    -- COMPANY DATA (PUBLIC)
    c.id AS company_id,
    c.display_order AS company_display_order,

    -- ESTABLISHMENT DATA (PUBLIC)
    e.id AS establishment_id,
    e.code AS establishment_code,
    e.type AS establishment_type,
    e.category AS establishment_category,
    e.is_active AS establishment_is_active,
    e.is_principal AS establishment_is_principal,

    -- ROLE DATA (PUBLIC)
    r.id AS role_id,
    r.name AS role_name,
    r.display_name AS role_display_name,
    r.level AS role_level,
    r.is_active AS role_is_active

FROM master.users u
    INNER JOIN master.people p ON u.person_id = p.id
    LEFT JOIN master.user_establishments ue ON u.id = ue.user_id AND ue.deleted_at IS NULL
    LEFT JOIN master.establishments e ON ue.establishment_id = e.id AND e.deleted_at IS NULL
    LEFT JOIN master.companies c ON e.company_id = c.id AND c.deleted_at IS NULL
    LEFT JOIN master.user_roles ur ON u.id = ur.user_id AND ur.deleted_at IS NULL
    LEFT JOIN master.roles r ON ur.role_id = r.id

WHERE 
    u.deleted_at IS NULL 
    AND p.deleted_at IS NULL
    AND u.is_active = true  -- Only active users in public view

ORDER BY u.id, ue.is_primary DESC NULLS LAST, r.level ASC;

-- =====================================================
-- 2. ADMIN VIEW (MASKED SENSITIVE DATA)
-- =====================================================
CREATE OR REPLACE VIEW master.vw_users_admin AS
SELECT 
    -- USER DATA (ADMIN - WITH MASKING)
    u.id AS user_id,
    u.person_id AS user_person_id,
    u.email_address AS user_email,
    u.email_verified_at AS user_email_verified_at,
    u.is_active AS user_is_active,
    u.is_system_admin AS user_is_system_admin,
    u.preferences AS user_preferences,
    u.notification_settings AS user_notification_settings,
    
    -- MASKED SENSITIVE FIELDS
    CASE WHEN u.two_factor_secret IS NOT NULL THEN '***CONFIGURED***' ELSE NULL END AS user_2fa_status,
    CASE WHEN u.two_factor_recovery_codes IS NOT NULL THEN '***AVAILABLE***' ELSE NULL END AS user_2fa_recovery_status,
    
    u.last_login_at AS user_last_login_at,
    u.password_changed_at AS user_password_changed_at,
    u.created_at AS user_created_at,
    u.updated_at AS user_updated_at,
    u.deleted_at AS user_deleted_at,

    -- PERSON DATA (COMPLETE FOR ADMIN)
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
    p.website AS person_website,
    p.description AS person_description,
    
    -- LGPD DATA (MASKED FOR COMPLIANCE)
    CASE WHEN p.lgpd_consent_version IS NOT NULL THEN 'V' || p.lgpd_consent_version ELSE 'NOT_PROVIDED' END AS person_lgpd_status,
    p.lgpd_consent_given_at AS person_lgpd_consent_date,
    
    p.created_at AS person_created_at,
    p.updated_at AS person_updated_at,
    p.deleted_at AS person_deleted_at,

    -- COMPANY DATA (COMPLETE)
    c.id AS company_id,
    c.person_id AS company_person_id,
    c.display_order AS company_display_order,
    c.created_at AS company_created_at,
    c.updated_at AS company_updated_at,
    c.deleted_at AS company_deleted_at,

    -- ESTABLISHMENT DATA (COMPLETE)
    e.id AS establishment_id,
    e.person_id AS establishment_person_id,
    e.company_id AS establishment_company_id,
    e.code AS establishment_code,
    e.type AS establishment_type,
    e.category AS establishment_category,
    e.is_active AS establishment_is_active,
    e.is_principal AS establishment_is_principal,
    e.created_at AS establishment_created_at,
    e.updated_at AS establishment_updated_at,
    e.deleted_at AS establishment_deleted_at,

    -- USER-ESTABLISHMENT RELATIONSHIP (PERMISSIONS MASKED)
    ue.id AS user_establishment_id,
    ue.role_id AS user_establishment_role_id,
    ue.is_primary AS user_establishment_is_primary,
    ue.status AS user_establishment_status,
    ue.assigned_by_user_id AS user_establishment_assigned_by_user_id,
    ue.assigned_at AS user_establishment_assigned_at,
    ue.expires_at AS user_establishment_expires_at,
    CASE WHEN ue.permissions IS NOT NULL THEN 'CONFIGURED' ELSE NULL END AS user_establishment_permissions_status,
    ue.created_at AS user_establishment_created_at,
    ue.updated_at AS user_establishment_updated_at,
    ue.deleted_at AS user_establishment_deleted_at,

    -- ROLE DATA (COMPLETE)
    r.id AS role_id,
    r.name AS role_name,
    r.display_name AS role_display_name,
    r.description AS role_description,
    r.level AS role_level,
    r.context_type AS role_context_type,
    r.is_active AS role_is_active,
    r.is_system_role AS role_is_system_role,
    r.created_at AS role_created_at,
    r.updated_at AS role_updated_at,

    -- USER-ROLE RELATIONSHIP (COMPLETE)
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
    INNER JOIN master.people p ON u.person_id = p.id
    LEFT JOIN master.user_establishments ue ON u.id = ue.user_id AND ue.deleted_at IS NULL
    LEFT JOIN master.establishments e ON ue.establishment_id = e.id AND e.deleted_at IS NULL
    LEFT JOIN master.companies c ON e.company_id = c.id AND c.deleted_at IS NULL
    LEFT JOIN master.user_roles ur ON u.id = ur.user_id AND ur.deleted_at IS NULL
    LEFT JOIN master.roles r ON ur.role_id = r.id

WHERE 
    u.deleted_at IS NULL 
    AND p.deleted_at IS NULL

ORDER BY u.id, ue.is_primary DESC NULLS LAST, r.level ASC;

-- =====================================================
-- 3. AUDIT LOG TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS master.user_data_access_log (
    id BIGSERIAL PRIMARY KEY,
    accessed_by_user_id BIGINT NOT NULL,
    accessed_user_id BIGINT,
    view_name VARCHAR(100) NOT NULL,
    access_type VARCHAR(50) NOT NULL, -- SELECT, COUNT, etc
    ip_address INET,
    user_agent TEXT,
    query_hash VARCHAR(64), -- MD5 of actual query for pattern detection
    sensitive_fields_accessed TEXT[], -- Array of sensitive field names
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_accessed_by_user FOREIGN KEY (accessed_by_user_id) REFERENCES master.users(id),
    CONSTRAINT fk_accessed_user FOREIGN KEY (accessed_user_id) REFERENCES master.users(id)
);

-- Indexes for audit log performance
CREATE INDEX IF NOT EXISTS idx_user_data_access_log_accessed_by ON master.user_data_access_log(accessed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_user_data_access_log_accessed_user ON master.user_data_access_log(accessed_user_id);
CREATE INDEX IF NOT EXISTS idx_user_data_access_log_created_at ON master.user_data_access_log(created_at);
CREATE INDEX IF NOT EXISTS idx_user_data_access_log_view_name ON master.user_data_access_log(view_name);

-- =====================================================
-- 4. ROW LEVEL SECURITY POLICIES
-- =====================================================

-- Enable RLS on original complete view (convert to table if needed)
-- Note: RLS works on tables, not views. Consider creating a function instead.

-- =====================================================
-- 5. SECURITY FUNCTIONS
-- =====================================================

-- Function to check if user can access another user's data
CREATE OR REPLACE FUNCTION master.can_access_user_data(
    requesting_user_id BIGINT,
    target_user_id BIGINT
) RETURNS BOOLEAN AS $$
DECLARE
    is_admin BOOLEAN;
    same_establishment BOOLEAN;
BEGIN
    -- Check if requesting user is system admin
    SELECT is_system_admin INTO is_admin
    FROM master.users 
    WHERE id = requesting_user_id AND is_active = true;
    
    IF is_admin THEN
        RETURN TRUE;
    END IF;
    
    -- Check if users share the same establishment
    SELECT EXISTS(
        SELECT 1 
        FROM master.user_establishments ue1
        JOIN master.user_establishments ue2 ON ue1.establishment_id = ue2.establishment_id
        WHERE ue1.user_id = requesting_user_id 
          AND ue2.user_id = target_user_id
          AND ue1.deleted_at IS NULL 
          AND ue2.deleted_at IS NULL
    ) INTO same_establishment;
    
    RETURN same_establishment OR (requesting_user_id = target_user_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to log data access
CREATE OR REPLACE FUNCTION master.log_user_data_access(
    accessed_by_user_id BIGINT,
    accessed_user_id BIGINT,
    view_name VARCHAR(100),
    access_type VARCHAR(50),
    sensitive_fields TEXT[] DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO master.user_data_access_log (
        accessed_by_user_id,
        accessed_user_id,
        view_name,
        access_type,
        sensitive_fields_accessed
    ) VALUES (
        accessed_by_user_id,
        accessed_user_id,
        view_name,
        access_type,
        sensitive_fields
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 6. SECURE WRAPPER FUNCTIONS
-- =====================================================

-- Secure function to get user data with access control
CREATE OR REPLACE FUNCTION master.get_user_data_secure(
    requesting_user_id BIGINT,
    target_user_id BIGINT DEFAULT NULL
) RETURNS TABLE(
    user_id BIGINT,
    user_email VARCHAR,
    person_name VARCHAR,
    company_id BIGINT,
    establishment_code VARCHAR,
    role_name VARCHAR,
    can_edit BOOLEAN
) AS $$
BEGIN
    -- Log the access attempt
    PERFORM master.log_user_data_access(
        requesting_user_id,
        target_user_id,
        'get_user_data_secure',
        'SELECT'
    );
    
    -- Return filtered data based on permissions
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

-- =====================================================
-- 7. USAGE EXAMPLES
-- =====================================================

/*
-- Public view (safe for all users)
SELECT * FROM master.vw_users_public WHERE user_id = 1;

-- Admin view (masked sensitive data)
SELECT * FROM master.vw_users_admin WHERE user_is_system_admin = true;

-- Secure function call (recommended)
SELECT * FROM master.get_user_data_secure(2, 1); -- User 2 accessing User 1's data

-- Check access permissions
SELECT master.can_access_user_data(2, 1); -- Can user 2 access user 1?

-- View audit log
SELECT * FROM master.user_data_access_log 
WHERE accessed_by_user_id = 2 
ORDER BY created_at DESC;
*/