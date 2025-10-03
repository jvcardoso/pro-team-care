-- Migração para setup do sistema de permissões granulares
-- Fase 1: Estrutura de dados e mapeamento

-- 1. Criar tabela de mapeamento temporária para migração
CREATE TABLE IF NOT EXISTS master.level_permission_mapping (
    id BIGSERIAL PRIMARY KEY,
    level_min INTEGER NOT NULL,
    level_max INTEGER NOT NULL,
    permission_name VARCHAR(100) NOT NULL,
    context_type VARCHAR(50) NOT NULL DEFAULT 'establishment',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS level_permission_mapping_level_idx ON master.level_permission_mapping (
    level_min, level_max
);
CREATE INDEX IF NOT EXISTS level_permission_mapping_permission_idx ON master.level_permission_mapping (
    permission_name
);

-- 2. Popular mapeamento baseado na análise do código atual
INSERT INTO master.level_permission_mapping (
    level_min, level_max, permission_name, context_type, description
) VALUES
-- Sistema (90-100)
(90, 100, 'system.admin', 'system', 'Administração completa do sistema'),
(90, 100, 'system.settings', 'system', 'Configurações globais do sistema'),
(90, 100, 'system.logs', 'system', 'Acesso aos logs do sistema'),
(90, 100, 'system.backup', 'system', 'Backup e restore do sistema'),

-- Admin Empresa (80-100)
(80, 100, 'companies.create', 'company', 'Criar empresas'),
(80, 100, 'companies.delete', 'company', 'Excluir empresas'),
(80, 100, 'companies.settings', 'company', 'Configurações da empresa'),
(80, 100, 'users.create', 'establishment', 'Criar usuários'),
(80, 100, 'users.delete', 'establishment', 'Excluir usuários'),
(
    80,
    100,
    'users.permissions',
    'establishment',
    'Gerenciar permissões de usuários'
),
(80, 100, 'establishments.create', 'company', 'Criar estabelecimentos'),
(80, 100, 'establishments.delete', 'establishment', 'Excluir estabelecimentos'),

-- Admin Estabelecimento (60-100)
(60, 100, 'companies.edit', 'company', 'Editar empresas'),
(60, 100, 'companies.view', 'company', 'Visualizar empresas'),
(60, 100, 'establishments.edit', 'establishment', 'Editar estabelecimentos'),
(
    60,
    100,
    'establishments.settings',
    'establishment',
    'Configurações do estabelecimento'
),
(60, 100, 'users.edit', 'establishment', 'Editar usuários'),
(60, 100, 'users.list', 'establishment', 'Listar usuários'),
(60, 100, 'roles.assign', 'establishment', 'Atribuir perfis'),

-- Operacional (40-100)
(40, 100, 'users.view', 'establishment', 'Visualizar usuários'),
(
    40,
    100,
    'establishments.view',
    'establishment',
    'Visualizar estabelecimentos'
),
(40, 100, 'companies.list', 'company', 'Listar empresas'),

-- Perfis e Permissões (níveis variados)
(70, 100, 'roles.create', 'establishment', 'Criar perfis'),
(70, 100, 'roles.edit', 'establishment', 'Editar perfis'),
(70, 100, 'roles.delete', 'establishment', 'Excluir perfis'),
(40, 100, 'roles.view', 'establishment', 'Visualizar perfis'),
(40, 100, 'roles.list', 'establishment', 'Listar perfis')

ON CONFLICT DO NOTHING;

-- 3. Criar tabela de templates de perfis para migração
CREATE TABLE IF NOT EXISTS master.role_templates (
    id BIGSERIAL PRIMARY KEY,
    template_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(125) NOT NULL,
    description TEXT,
    equivalent_level_min INTEGER,
    equivalent_level_max INTEGER,
    context_type VARCHAR(50) NOT NULL DEFAULT 'establishment',
    permissions TEXT [], -- Array de permissões
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para templates
CREATE INDEX IF NOT EXISTS role_templates_key_idx ON master.role_templates (
    template_key
);
CREATE INDEX IF NOT EXISTS role_templates_level_idx ON master.role_templates (
    equivalent_level_min, equivalent_level_max
);

-- 4. Popular templates baseados na análise
INSERT INTO master.role_templates (
    template_key,
    name,
    description,
    equivalent_level_min,
    equivalent_level_max,
    context_type,
    permissions
) VALUES

(
    'super_admin',
    'Super Administrador',
    'Acesso total ao sistema',
    90,
    100,
    'system',
    ARRAY[
        'system.admin', 'system.settings', 'system.logs', 'system.backup',
        'companies.create',
        'companies.edit',
        'companies.delete',
        'companies.settings',
        'users.create', 'users.edit', 'users.delete', 'users.permissions',
        'roles.create', 'roles.edit', 'roles.delete', 'roles.assign'
    ]
),

(
    'admin_empresa',
    'Administrador da Empresa',
    'Gestão completa da empresa',
    80,
    89,
    'company',
    ARRAY[
        'companies.edit', 'companies.settings', 'companies.view',
        'establishments.create', 'establishments.edit', 'establishments.delete',
        'users.create',
        'users.edit',
        'users.delete',
        'users.list',
        'users.view',
        'roles.create', 'roles.edit', 'roles.assign'
    ]
),

(
    'admin_estabelecimento',
    'Administrador do Estabelecimento',
    'Gestão do estabelecimento',
    60,
    79,
    'establishment',
    ARRAY[
        'establishments.edit', 'establishments.settings', 'establishments.view',
        'users.edit', 'users.list', 'users.view',
        'companies.view', 'companies.list',
        'roles.view', 'roles.assign'
    ]
),

(
    'gerente_operacional',
    'Gerente Operacional',
    'Operações diárias',
    50,
    69,
    'establishment',
    ARRAY[
        'users.view', 'users.list',
        'establishments.view',
        'companies.view', 'companies.list',
        'roles.view'
    ]
),

(
    'operador',
    'Operador',
    'Acesso básico para operações',
    40,
    59,
    'establishment',
    ARRAY['users.view', 'establishments.view', 'companies.view']
),

(
    'consultor',
    'Consultor Externo',
    'Acesso limitado para consultoria',
    30,
    49,
    'establishment',
    ARRAY['companies.view', 'establishments.view']
)

ON CONFLICT (template_key) DO UPDATE SET
name = excluded.name,
description = excluded.description,
equivalent_level_min = excluded.equivalent_level_min,
equivalent_level_max = excluded.equivalent_level_max,
permissions = excluded.permissions,
updated_at = NOW();

-- 5. Criar tabela de auditoria para mudanças de permissões
CREATE TABLE IF NOT EXISTS master.permission_audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES master.users (id),
    -- 'granted', 'revoked', 'role_assigned', 'role_removed'
    action VARCHAR(50) NOT NULL,
    permission VARCHAR(100),
    role_id BIGINT REFERENCES master.roles (id),
    context_type VARCHAR(50) NOT NULL,
    context_id BIGINT,
    changed_by BIGINT REFERENCES master.users (id),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para auditoria
CREATE INDEX IF NOT EXISTS permission_audit_user_idx ON master.permission_audit_log (
    user_id
);
CREATE INDEX IF NOT EXISTS permission_audit_permission_idx ON master.permission_audit_log (
    permission
);
CREATE INDEX IF NOT EXISTS permission_audit_date_idx ON master.permission_audit_log (
    created_at
);

-- 6. Criar função para mapear nível para permissões
CREATE OR REPLACE FUNCTION master.get_permissions_for_level(
    user_level INTEGER,
    ctx_type VARCHAR(50) DEFAULT 'establishment'
) RETURNS TEXT [] AS $$
DECLARE
    permissions_array TEXT[];
BEGIN
    SELECT array_agg(DISTINCT permission_name)
    INTO permissions_array
    FROM master.level_permission_mapping
    WHERE user_level >= level_min
      AND user_level <= level_max
      AND context_type = ctx_type;

    RETURN COALESCE(permissions_array, ARRAY[]::TEXT[]);
END;
$$ LANGUAGE plpgsql;

-- 7. Criar função para sugerir template baseado no nível
CREATE OR REPLACE FUNCTION master.suggest_role_template_for_level(
    user_level INTEGER,
    ctx_type VARCHAR(50) DEFAULT 'establishment'
) RETURNS VARCHAR(50) AS $$
DECLARE
    template_key VARCHAR(50);
BEGIN
    SELECT rt.template_key
    INTO template_key
    FROM master.role_templates rt
    WHERE user_level >= rt.equivalent_level_min
      AND user_level <= rt.equivalent_level_max
      AND rt.context_type = ctx_type
      AND rt.is_active = true
    ORDER BY (rt.equivalent_level_max - rt.equivalent_level_min) ASC -- Mais específico primeiro
    LIMIT 1;

    RETURN COALESCE(template_key, 'operador'); -- Fallback para operador
END;
$$ LANGUAGE plpgsql;

-- 8. Criar view para análise de usuários e seus níveis atuais
CREATE OR REPLACE VIEW master.user_levels_analysis AS
SELECT
    u.id AS user_id,
    u.name AS user_name,
    u.email,
    ur.context_type,
    ur.context_id,
    r.name AS role_name,
    r.level AS current_level,
    ur.status AS role_status,
    ur.created_at AS role_assigned_at,
    master.suggest_role_template_for_level(
        r.level, ur.context_type
    ) AS suggested_template,
    master.get_permissions_for_level(
        r.level, ur.context_type
    ) AS equivalent_permissions
FROM master.users AS u
INNER JOIN master.user_roles AS ur ON u.id = ur.user_id
INNER JOIN master.roles AS r ON ur.role_id = r.id
WHERE
    ur.status = 'active'
    AND ur.deleted_at IS null
    AND r.is_active = true
ORDER BY u.name ASC, ur.context_type ASC, r.level DESC;

-- 9. Comentários da migração
COMMENT ON TABLE master.level_permission_mapping IS 'Mapeamento temporário para migração de níveis para permissões';
COMMENT ON TABLE master.role_templates IS 'Templates de perfis pré-configurados para facilitar migração';
COMMENT ON TABLE master.permission_audit_log IS 'Log de auditoria para mudanças de permissões';
COMMENT ON VIEW master.user_levels_analysis IS 'Análise de usuários atuais para planejamento da migração';
