-- =====================================================
-- QUERY COMPLETA: USUÁRIOS COM TODAS AS RELAÇÕES
-- =====================================================
-- Esta query lista todos os usuários com:
-- - Dados pessoais (tabela people)
-- - Empresas relacionadas (companies via establishments)
-- - Estabelecimentos vinculados (establishments)
-- - Perfis/Roles atribuídos (roles via user_roles)
-- - Todos os campos de todas as tabelas
-- =====================================================

SELECT 
    -- DADOS DO USUÁRIO (USERS)
    u.id AS usuario_id,
    u.person_id AS usuario_person_id,
    u.email_address AS usuario_email,
    u.email_verified_at AS usuario_email_verificado_em,
    u.is_active AS usuario_ativo,
    u.is_system_admin AS usuario_admin_sistema,
    u.preferences AS usuario_preferencias,
    u.notification_settings AS usuario_config_notificacoes,
    u.two_factor_secret AS usuario_2fa_secret,
    u.two_factor_recovery_codes AS usuario_2fa_recovery,
    u.last_login_at AS usuario_ultimo_login,
    u.password_changed_at AS usuario_senha_alterada_em,
    u.created_at AS usuario_criado_em,
    u.updated_at AS usuario_atualizado_em,
    u.deleted_at AS usuario_deletado_em,

    -- DADOS PESSOAIS (PEOPLE)
    p.id AS pessoa_id,
    p.person_type AS pessoa_tipo,
    p.name AS pessoa_nome,
    p.trade_name AS pessoa_nome_fantasia,
    p.tax_id AS pessoa_cpf_cnpj,
    p.secondary_tax_id AS pessoa_doc_secundario,
    p.birth_date AS pessoa_nascimento,
    p.gender AS pessoa_genero,
    p.marital_status AS pessoa_estado_civil,
    p.occupation AS pessoa_profissao,
    p.incorporation_date AS pessoa_data_fundacao,
    p.tax_regime AS pessoa_regime_tributario,
    p.legal_nature AS pessoa_natureza_juridica,
    p.municipal_registration AS pessoa_inscricao_municipal,
    p.status AS pessoa_status,
    p.is_active AS pessoa_ativa,
    p.metadata AS pessoa_metadata,
    p.website AS pessoa_website,
    p.description AS pessoa_descricao,
    p.lgpd_consent_version AS pessoa_lgpd_versao,
    p.lgpd_consent_given_at AS pessoa_lgpd_consentimento_em,
    p.lgpd_data_retention_expires_at AS pessoa_lgpd_expira_em,
    p.created_at AS pessoa_criada_em,
    p.updated_at AS pessoa_atualizada_em,
    p.deleted_at AS pessoa_deletada_em,

    -- DADOS DA EMPRESA (COMPANIES)
    c.id AS empresa_id,
    c.person_id AS empresa_person_id,
    c.settings AS empresa_configuracoes,
    c.metadata AS empresa_metadata,
    c.display_order AS empresa_ordem_exibicao,
    c.created_at AS empresa_criada_em,
    c.updated_at AS empresa_atualizada_em,
    c.deleted_at AS empresa_deletada_em,

    -- DADOS DO ESTABELECIMENTO (ESTABLISHMENTS)
    e.id AS estabelecimento_id,
    e.person_id AS estabelecimento_person_id,
    e.company_id AS estabelecimento_empresa_id,
    e.code AS estabelecimento_codigo,
    e.type AS estabelecimento_tipo,
    e.category AS estabelecimento_categoria,
    e.is_active AS estabelecimento_ativo,
    e.is_principal AS estabelecimento_principal,
    e.settings AS estabelecimento_configuracoes,
    e.operating_hours AS estabelecimento_horarios,
    e.service_areas AS estabelecimento_areas_atendimento,
    e.created_at AS estabelecimento_criado_em,
    e.updated_at AS estabelecimento_atualizado_em,
    e.deleted_at AS estabelecimento_deletado_em,

    -- RELAÇÃO USUÁRIO-ESTABELECIMENTO (USER_ESTABLISHMENTS)
    ue.id AS user_establishment_id,
    ue.role_id AS user_establishment_role_id,
    ue.is_primary AS user_establishment_primario,
    ue.status AS user_establishment_status,
    ue.assigned_by_user_id AS user_establishment_atribuido_por,
    ue.assigned_at AS user_establishment_atribuido_em,
    ue.expires_at AS user_establishment_expira_em,
    ue.permissions AS user_establishment_permissoes,
    ue.created_at AS user_establishment_criado_em,
    ue.updated_at AS user_establishment_atualizado_em,
    ue.deleted_at AS user_establishment_deletado_em,

    -- DADOS DO PERFIL/ROLE (ROLES)
    r.id AS role_id,
    r.name AS role_nome,
    r.display_name AS role_nome_exibicao,
    r.description AS role_descricao,
    r.level AS role_nivel,
    r.context_type AS role_contexto_tipo,
    r.is_active AS role_ativa,
    r.is_system_role AS role_sistema,
    r.settings AS role_configuracoes,
    r.created_at AS role_criada_em,
    r.updated_at AS role_atualizada_em,

    -- RELAÇÃO USUÁRIO-ROLE (USER_ROLES)
    ur.id AS user_role_id,
    ur.context_type AS user_role_contexto_tipo,
    ur.context_id AS user_role_contexto_id,
    ur.status AS user_role_status,
    ur.assigned_by_user_id AS user_role_atribuido_por,
    ur.assigned_at AS user_role_atribuido_em,
    ur.expires_at AS user_role_expira_em,
    ur.created_at AS user_role_criado_em,
    ur.updated_at AS user_role_atualizado_em,
    ur.deleted_at AS user_role_deletado_em

FROM master.users u

    -- RELAÇÃO OBRIGATÓRIA: USUÁRIO -> PESSOA
    INNER JOIN master.people p ON u.person_id = p.id

    -- RELAÇÃO OPCIONAL: USUÁRIO -> ESTABELECIMENTOS
    LEFT JOIN master.user_establishments ue ON u.id = ue.user_id AND ue.deleted_at IS NULL

    -- RELAÇÃO OPCIONAL: ESTABELECIMENTO -> DADOS DO ESTABELECIMENTO
    LEFT JOIN master.establishments e ON ue.establishment_id = e.id AND e.deleted_at IS NULL

    -- RELAÇÃO OPCIONAL: ESTABELECIMENTO -> EMPRESA
    LEFT JOIN master.companies c ON e.company_id = c.id AND c.deleted_at IS NULL

    -- RELAÇÃO OPCIONAL: USUÁRIO -> ROLES
    LEFT JOIN master.user_roles ur ON u.id = ur.user_id AND ur.deleted_at IS NULL

    -- RELAÇÃO OPCIONAL: ROLE -> DADOS DO ROLE
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
-- VERSÃO RESUMIDA (CAMPOS PRINCIPAIS)
-- =====================================================
/*
SELECT 
    -- USUÁRIO
    u.id AS usuario_id,
    u.email_address AS email,
    u.is_active AS ativo,
    u.is_system_admin AS admin_sistema,
    u.last_login_at AS ultimo_login,
    
    -- PESSOA
    p.name AS nome,
    p.person_type AS tipo_pessoa,
    p.tax_id AS cpf_cnpj,
    p.birth_date AS nascimento,
    
    -- EMPRESA/ESTABELECIMENTO
    c.id AS empresa_id,
    e.code AS estabelecimento_codigo,
    e.type AS estabelecimento_tipo,
    e.is_principal AS estabelecimento_principal,
    ue.is_primary AS vinculo_primario,
    
    -- PERFIL
    r.name AS role_nome,
    r.display_name AS role_titulo,
    r.level AS role_nivel,
    ur.status AS role_status
    
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
ORDER BY 
    u.id, 
    ue.is_primary DESC NULLS LAST,
    r.level ASC;
*/