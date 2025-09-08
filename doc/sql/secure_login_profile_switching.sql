-- =====================================================
-- SISTEMA DE LOGIN SEGURO E TROCA DE PERFIL
-- =====================================================
-- Implementa login seguro com capacidade de assumir múltiplos perfis/contextos
-- Suporta: Root assume qualquer perfil, Admin multi-empresa, Multi-estabelecimento
-- =====================================================

-- =====================================================
-- 1. TABELA DE SESSÕES SEGURAS
-- =====================================================
CREATE TABLE IF NOT EXISTS master.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    
    -- Contexto da sessão
    active_role_id BIGINT, -- Role atualmente ativo
    active_context_type VARCHAR(50), -- 'system', 'company', 'establishment'
    active_context_id BIGINT, -- ID do contexto (company.id ou establishment.id)
    
    -- Personificação (para ROOT/Support)
    impersonated_user_id BIGINT, -- Se está operando como outro usuário
    impersonation_reason TEXT, -- Motivo da personificação
    
    -- Dados da sessão
    session_token VARCHAR(512) NOT NULL UNIQUE,
    refresh_token VARCHAR(512) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    device_fingerprint VARCHAR(128),
    
    -- Controle de expiração
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    refresh_expires_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Flags de segurança
    is_active BOOLEAN DEFAULT true,
    requires_2fa_verification BOOLEAN DEFAULT false,
    two_factor_verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Auditoria
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    terminated_at TIMESTAMP WITH TIME ZONE,
    termination_reason VARCHAR(100),
    
    -- Constraints
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES master.users(id),
    CONSTRAINT fk_user_sessions_role FOREIGN KEY (active_role_id) REFERENCES master.roles(id),
    CONSTRAINT fk_user_sessions_impersonated FOREIGN KEY (impersonated_user_id) REFERENCES master.users(id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON master.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON master.user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON master.user_sessions(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON master.user_sessions(last_activity_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_impersonated ON master.user_sessions(impersonated_user_id);

-- =====================================================
-- 2. TABELA DE MUDANÇAS DE CONTEXTO (AUDITORIA)
-- =====================================================
CREATE TABLE IF NOT EXISTS master.context_switches (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id BIGINT NOT NULL,
    
    -- Contexto anterior
    previous_role_id BIGINT,
    previous_context_type VARCHAR(50),
    previous_context_id BIGINT,
    
    -- Novo contexto
    new_role_id BIGINT,
    new_context_type VARCHAR(50),
    new_context_id BIGINT,
    
    -- Personificação
    previous_impersonated_user_id BIGINT,
    new_impersonated_user_id BIGINT,
    
    -- Metadados
    switch_reason VARCHAR(200),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_context_switches_session FOREIGN KEY (session_id) REFERENCES master.user_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_context_switches_user FOREIGN KEY (user_id) REFERENCES master.users(id)
);

-- Índices para auditoria
CREATE INDEX IF NOT EXISTS idx_context_switches_session ON master.context_switches(session_id);
CREATE INDEX IF NOT EXISTS idx_context_switches_user ON master.context_switches(user_id);
CREATE INDEX IF NOT EXISTS idx_context_switches_created_at ON master.context_switches(created_at);

-- =====================================================
-- 3. FUNÇÃO: OBTER PERFIS DISPONÍVEIS PARA USUÁRIO
-- =====================================================
CREATE OR REPLACE FUNCTION master.get_available_profiles(
    user_id_param BIGINT
) RETURNS TABLE(
    role_id BIGINT,
    role_name VARCHAR,
    role_display_name VARCHAR,
    context_type VARCHAR,
    context_id BIGINT,
    context_name TEXT,
    can_switch BOOLEAN,
    is_impersonation BOOLEAN
) AS $$
DECLARE
    is_root BOOLEAN;
BEGIN
    -- Verificar se é ROOT/System Admin
    SELECT is_system_admin INTO is_root
    FROM master.users 
    WHERE id = user_id_param;
    
    -- Se for ROOT, pode assumir QUALQUER perfil do sistema
    IF is_root THEN
        RETURN QUERY
        SELECT 
            r.id,
            r.name,
            r.display_name,
            ur.context_type,
            ur.context_id,
            CASE 
                WHEN ur.context_type = 'system' THEN 'Sistema Global'
                WHEN ur.context_type = 'company' THEN 
                    (SELECT p.name FROM master.companies c JOIN master.people p ON c.person_id = p.id WHERE c.id = ur.context_id)
                WHEN ur.context_type = 'establishment' THEN 
                    (SELECT p.name FROM master.establishments e JOIN master.people p ON e.person_id = p.id WHERE e.id = ur.context_id)
                ELSE 'Contexto Desconhecido'
            END,
            true, -- ROOT pode sempre trocar
            CASE WHEN ur.user_id != user_id_param THEN true ELSE false END -- É personificação se não for o próprio usuário
        FROM master.user_roles ur
        JOIN master.roles r ON ur.role_id = r.id
        WHERE ur.deleted_at IS NULL
        ORDER BY ur.user_id = user_id_param DESC, r.level DESC; -- Próprios roles primeiro
    END IF;
    
    -- Para usuários não-ROOT, retornar apenas seus próprios perfis
    RETURN QUERY
    SELECT 
        r.id,
        r.name,
        r.display_name,
        ur.context_type,
        ur.context_id,
        CASE 
            WHEN ur.context_type = 'system' THEN 'Sistema Global'
            WHEN ur.context_type = 'company' THEN 
                (SELECT p.name FROM master.companies c JOIN master.people p ON c.person_id = p.id WHERE c.id = ur.context_id)
            WHEN ur.context_type = 'establishment' THEN 
                (SELECT p.name FROM master.establishments e JOIN master.people p ON e.person_id = p.id WHERE e.id = ur.context_id)
            ELSE 'Contexto Desconhecido'
        END,
        true, -- Pode sempre trocar para seus próprios perfis
        false -- Nunca é personificação para próprios perfis
    FROM master.user_roles ur
    JOIN master.roles r ON ur.role_id = r.id
    WHERE ur.user_id = user_id_param 
      AND ur.deleted_at IS NULL
    ORDER BY r.level DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 4. FUNÇÃO: TROCAR PERFIL/CONTEXTO
-- =====================================================
CREATE OR REPLACE FUNCTION master.switch_user_context(
    session_token_param VARCHAR(512),
    new_role_id_param BIGINT DEFAULT NULL,
    new_context_type_param VARCHAR(50) DEFAULT NULL,
    new_context_id_param BIGINT DEFAULT NULL,
    impersonated_user_id_param BIGINT DEFAULT NULL,
    switch_reason_param VARCHAR(200) DEFAULT NULL,
    user_agent_param TEXT DEFAULT NULL,
    ip_address_param INET DEFAULT NULL
) RETURNS TABLE(
    success BOOLEAN,
    message TEXT,
    new_session_data JSONB
) AS $$
DECLARE
    current_session RECORD;
    can_switch BOOLEAN := false;
    context_name TEXT;
    role_name TEXT;
BEGIN
    -- 1. Buscar sessão atual
    SELECT * INTO current_session
    FROM master.user_sessions 
    WHERE session_token = session_token_param 
      AND is_active = true 
      AND expires_at > CURRENT_TIMESTAMP;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'Sessão inválida ou expirada'::TEXT, NULL::JSONB;
        RETURN;
    END IF;
    
    -- 2. Verificar se pode fazer a troca
    SELECT EXISTS(
        SELECT 1 FROM master.get_available_profiles(current_session.user_id)
        WHERE (new_role_id_param IS NULL OR role_id = new_role_id_param)
          AND (new_context_type_param IS NULL OR context_type = new_context_type_param)
          AND (new_context_id_param IS NULL OR context_id = new_context_id_param)
          AND (impersonated_user_id_param IS NULL OR is_impersonation = true)
          AND can_switch = true
    ) INTO can_switch;
    
    IF NOT can_switch THEN
        RETURN QUERY SELECT false, 'Não autorizado para esta troca de contexto'::TEXT, NULL::JSONB;
        RETURN;
    END IF;
    
    -- 3. Obter nomes para auditoria
    IF new_context_type_param = 'company' THEN
        SELECT p.name INTO context_name
        FROM master.companies c JOIN master.people p ON c.person_id = p.id 
        WHERE c.id = new_context_id_param;
    ELSIF new_context_type_param = 'establishment' THEN
        SELECT p.name INTO context_name
        FROM master.establishments e JOIN master.people p ON e.person_id = p.id 
        WHERE e.id = new_context_id_param;
    ELSE
        context_name := 'Sistema Global';
    END IF;
    
    IF new_role_id_param IS NOT NULL THEN
        SELECT display_name INTO role_name
        FROM master.roles WHERE id = new_role_id_param;
    END IF;
    
    -- 4. Registrar mudança de contexto
    INSERT INTO master.context_switches (
        session_id, user_id,
        previous_role_id, previous_context_type, previous_context_id, previous_impersonated_user_id,
        new_role_id, new_context_type, new_context_id, new_impersonated_user_id,
        switch_reason, ip_address, user_agent
    ) VALUES (
        current_session.id, current_session.user_id,
        current_session.active_role_id, current_session.active_context_type, 
        current_session.active_context_id, current_session.impersonated_user_id,
        new_role_id_param, new_context_type_param, new_context_id_param, impersonated_user_id_param,
        switch_reason_param, ip_address_param, user_agent_param
    );
    
    -- 5. Atualizar sessão
    UPDATE master.user_sessions 
    SET 
        active_role_id = COALESCE(new_role_id_param, active_role_id),
        active_context_type = COALESCE(new_context_type_param, active_context_type),
        active_context_id = COALESCE(new_context_id_param, active_context_id),
        impersonated_user_id = COALESCE(impersonated_user_id_param, impersonated_user_id),
        last_activity_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = current_session.id;
    
    -- 6. Retornar dados da nova sessão
    RETURN QUERY 
    SELECT 
        true,
        format('Contexto alterado para: %s (%s)', COALESCE(role_name, 'Mesmo Role'), COALESCE(context_name, 'Mesmo Contexto')),
        jsonb_build_object(
            'role_id', COALESCE(new_role_id_param, current_session.active_role_id),
            'role_name', role_name,
            'context_type', COALESCE(new_context_type_param, current_session.active_context_type),
            'context_id', COALESCE(new_context_id_param, current_session.active_context_id),
            'context_name', context_name,
            'impersonated_user_id', COALESCE(impersonated_user_id_param, current_session.impersonated_user_id),
            'switched_at', CURRENT_TIMESTAMP
        );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 5. FUNÇÃO: VALIDAR SESSÃO E CONTEXTO ATUAL
-- =====================================================
CREATE OR REPLACE FUNCTION master.validate_session_context(
    session_token_param VARCHAR(512)
) RETURNS TABLE(
    is_valid BOOLEAN,
    user_id BIGINT,
    user_email VARCHAR,
    active_role_name VARCHAR,
    active_context_type VARCHAR,
    active_context_id BIGINT,
    active_context_name TEXT,
    impersonated_user_id BIGINT,
    impersonated_user_email VARCHAR,
    permissions JSONB,
    expires_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        true,
        COALESCE(us.impersonated_user_id, us.user_id) as effective_user_id,
        COALESCE(impersonated_u.email_address, u.email_address) as effective_email,
        r.display_name,
        us.active_context_type,
        us.active_context_id,
        CASE 
            WHEN us.active_context_type = 'system' THEN 'Sistema Global'
            WHEN us.active_context_type = 'company' THEN 
                (SELECT p.name FROM master.companies c JOIN master.people p ON c.person_id = p.id WHERE c.id = us.active_context_id)
            WHEN us.active_context_type = 'establishment' THEN 
                (SELECT p.name FROM master.establishments e JOIN master.people p ON e.person_id = p.id WHERE e.id = us.active_context_id)
            ELSE 'Contexto Desconhecido'
        END,
        us.impersonated_user_id,
        impersonated_u.email_address,
        -- Buscar permissões do role no contexto
        COALESCE(
            (SELECT permissions FROM master.user_establishments ue 
             WHERE ue.user_id = COALESCE(us.impersonated_user_id, us.user_id)
               AND ue.establishment_id = us.active_context_id
               AND us.active_context_type = 'establishment'),
            '{}'::jsonb
        ),
        us.expires_at
    FROM master.user_sessions us
    JOIN master.users u ON us.user_id = u.id
    LEFT JOIN master.users impersonated_u ON us.impersonated_user_id = impersonated_u.id
    LEFT JOIN master.roles r ON us.active_role_id = r.id
    WHERE us.session_token = session_token_param
      AND us.is_active = true
      AND us.expires_at > CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 6. VIEW: SESSÕES ATIVAS COM CONTEXTO
-- =====================================================
CREATE OR REPLACE VIEW master.vw_active_sessions AS
SELECT 
    us.id as session_id,
    us.session_token,
    u.email_address as user_email,
    impersonated_u.email_address as impersonated_email,
    r.display_name as active_role,
    us.active_context_type,
    us.active_context_id,
    CASE 
        WHEN us.active_context_type = 'system' THEN 'Sistema Global'
        WHEN us.active_context_type = 'company' THEN 
            (SELECT p.name FROM master.companies c JOIN master.people p ON c.person_id = p.id WHERE c.id = us.active_context_id)
        WHEN us.active_context_type = 'establishment' THEN 
            (SELECT p.name FROM master.establishments e JOIN master.people p ON e.person_id = p.id WHERE e.id = us.active_context_id)
        ELSE 'Contexto Desconhecido'
    END as context_name,
    us.ip_address,
    us.last_activity_at,
    us.expires_at,
    CASE WHEN us.impersonated_user_id IS NOT NULL THEN true ELSE false END as is_impersonating
FROM master.user_sessions us
JOIN master.users u ON us.user_id = u.id
LEFT JOIN master.users impersonated_u ON us.impersonated_user_id = impersonated_u.id
LEFT JOIN master.roles r ON us.active_role_id = r.id
WHERE us.is_active = true 
  AND us.expires_at > CURRENT_TIMESTAMP
ORDER BY us.last_activity_at DESC;

-- =====================================================
-- 7. EXEMPLOS DE USO
-- =====================================================

/*
-- 1. Obter perfis disponíveis para um usuário ROOT
SELECT * FROM master.get_available_profiles(2); -- ID do superadmin

-- 2. Trocar contexto (ROOT assumindo perfil de admin empresa)
SELECT * FROM master.switch_user_context(
    'session_token_here',
    new_role_id_param := 5, -- admin_empresa role
    new_context_type_param := 'company',
    new_context_id_param := 1, -- empresa ID 1
    switch_reason_param := 'Suporte técnico'
);

-- 3. ROOT personificando outro usuário
SELECT * FROM master.switch_user_context(
    'session_token_here',
    impersonated_user_id_param := 3, -- ID do usuário comum
    switch_reason_param := 'Investigação de problema reportado'
);

-- 4. Validar sessão atual
SELECT * FROM master.validate_session_context('session_token_here');

-- 5. Ver sessões ativas
SELECT * FROM master.vw_active_sessions;

-- 6. Auditoria de trocas de contexto
SELECT * FROM master.context_switches 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY created_at DESC;
*/