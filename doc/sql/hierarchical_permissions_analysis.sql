-- =====================================================
-- ANÁLISE: SUPORTE À HIERARQUIA DE PERMISSÕES
-- =====================================================
-- Análise da estrutura atual para suportar o cenário hierárquico:
-- ROOT > ADMIN EMPRESA > ADMIN ESTABELECIMENTO > USUÁRIO COMUM
-- =====================================================

-- =====================================================
-- 1. CENÁRIO HIERÁRQUICO PROPOSTO
-- =====================================================

/*
🔴 ROOT/SYSTEM ADMIN (Level 100):
   - Acesso TOTAL ao sistema
   - Todos usuários, todas empresas, todos estabelecimentos
   - Gerenciamento de system roles e configurações globais

🔵 ADMIN EMPRESA (Level 80):
   - Acesso a TODAS as informações da(s) empresa(s) que administra
   - Todos usuários e estabelecimentos das empresas sob sua responsabilidade
   - Pode criar/editar usuários dentro de suas empresas
   - Pode gerenciar estabelecimentos de suas empresas

🟢 ADMIN ESTABELECIMENTO (Level 60-70):
   - Acesso apenas aos estabelecimentos que administra
   - Usuários vinculados aos estabelecimentos sob sua responsabilidade
   - Pode gerenciar usuários de seus estabelecimentos
   - NÃO vê dados de outros estabelecimentos da mesma empresa

🟡 USUÁRIO COMUM (Level 10-50):
   - Acesso apenas aos próprios dados
   - Pode ver colegas do mesmo estabelecimento (conforme permissão)
   - Operações limitadas conforme role específico
*/

-- =====================================================
-- 2. COMPATIBILIDADE COM ESTRUTURA ATUAL
-- =====================================================

-- ✅ ESTRUTURA ATUAL SUPORTA COMPLETAMENTE O CENÁRIO!

-- 2.1 ROOT/SYSTEM ADMIN
-- Campo: users.is_system_admin = true
-- Role: super_admin (level 100, context: system)
-- Identificação: Direto via campo booleano

-- 2.2 ADMIN EMPRESA  
-- Role: admin_empresa/Company Administrator (level 80, context: company)
-- Vinculação: user_roles.context_type = 'company', context_id = company.id
-- Acesso: Todos usuários/estabelecimentos da empresa via company_id

-- 2.3 ADMIN ESTABELECIMENTO
-- Role: admin_estabelecimento/Establishment Administrator (level 60-70, context: establishment)  
-- Vinculação: user_roles.context_type = 'establishment', context_id = establishment.id
-- Acesso: Apenas usuários do estabelecimento via establishment_id

-- 2.4 USUÁRIO COMUM
-- Roles: Viewer, operador, consultor, etc (level 10-50, context: establishment)
-- Vinculação: user_establishments para definir estabelecimentos acessíveis
-- Acesso: Próprios dados + colegas do estabelecimento conforme role

-- =====================================================
-- 3. FUNÇÃO DE CONTROLE HIERÁRQUICO PROPOSTA
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
-- 4. VIEW HIERÁRQUICA SEGURA
-- =====================================================

CREATE OR REPLACE VIEW master.vw_users_hierarchical AS
SELECT 
    u.user_id,
    u.user_email,
    u.person_name,
    u.company_id,
    u.establishment_code,
    u.role_name,
    u.role_display_name,
    -- Campos adicionais para controle
    CASE 
        WHEN u.user_is_system_admin THEN 'ROOT'
        WHEN EXISTS(
            SELECT 1 FROM master.user_roles ur2 
            JOIN master.roles r2 ON ur2.role_id = r2.id 
            WHERE ur2.user_id = u.user_id 
              AND r2.context_type = 'company' 
              AND r2.level >= 80
        ) THEN 'ADMIN_EMPRESA'
        WHEN EXISTS(
            SELECT 1 FROM master.user_roles ur3 
            JOIN master.roles r3 ON ur3.role_id = r3.id 
            WHERE ur3.user_id = u.user_id 
              AND r3.context_type = 'establishment' 
              AND r3.level >= 60
        ) THEN 'ADMIN_ESTABELECIMENTO'
        ELSE 'USUARIO_COMUM'
    END as hierarchy_level,
    
    -- Contextos de acesso
    (SELECT ARRAY_AGG(DISTINCT ur4.context_id::text) 
     FROM master.user_roles ur4 
     JOIN master.roles r4 ON ur4.role_id = r4.id
     WHERE ur4.user_id = u.user_id 
       AND r4.context_type = 'company'
       AND ur4.deleted_at IS NULL
    ) as accessible_companies,
    
    (SELECT ARRAY_AGG(DISTINCT ur5.context_id::text) 
     FROM master.user_roles ur5 
     JOIN master.roles r5 ON ur5.role_id = r5.id
     WHERE ur5.user_id = u.user_id 
       AND r5.context_type = 'establishment'
       AND ur5.deleted_at IS NULL
    ) as accessible_establishments

FROM master.vw_users_public u
ORDER BY 
    CASE 
        WHEN u.user_is_system_admin THEN 1
        WHEN EXISTS(SELECT 1 FROM master.user_roles ur JOIN master.roles r ON ur.role_id = r.id WHERE ur.user_id = u.user_id AND r.level >= 80) THEN 2
        WHEN EXISTS(SELECT 1 FROM master.user_roles ur JOIN master.roles r ON ur.role_id = r.id WHERE ur.user_id = u.user_id AND r.level >= 60) THEN 3
        ELSE 4
    END,
    u.person_name;

-- =====================================================
-- 5. EXEMPLOS DE USO DA HIERARQUIA
-- =====================================================

/*
-- Verificar usuários acessíveis para um admin de empresa
SELECT * FROM master.get_accessible_users_hierarchical(2); -- ID do admin empresa

-- Ver usuários com classificação hierárquica
SELECT user_id, user_email, person_name, hierarchy_level, 
       accessible_companies, accessible_establishments
FROM master.vw_users_hierarchical;

-- Filtrar usuários por nível hierárquico
SELECT * FROM master.vw_users_hierarchical 
WHERE hierarchy_level IN ('ROOT', 'ADMIN_EMPRESA');

-- Verificar quais empresas/estabelecimentos um usuário pode acessar
SELECT user_email, hierarchy_level, accessible_companies, accessible_establishments
FROM master.vw_users_hierarchical 
WHERE user_id = 1;
*/

-- =====================================================
-- 6. VALIDAÇÃO DA IMPLEMENTAÇÃO
-- =====================================================

-- Verificar se todos os níveis hierárquicos estão representados
SELECT 
    hierarchy_level,
    COUNT(*) as user_count,
    STRING_AGG(user_email, ', ') as users
FROM master.vw_users_hierarchical
GROUP BY hierarchy_level
ORDER BY 
    CASE hierarchy_level
        WHEN 'ROOT' THEN 1
        WHEN 'ADMIN_EMPRESA' THEN 2  
        WHEN 'ADMIN_ESTABELECIMENTO' THEN 3
        WHEN 'USUARIO_COMUM' THEN 4
    END;