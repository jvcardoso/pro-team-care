-- =====================================================
-- RECOMENDAÇÕES DE ÍNDICES PARA OTIMIZAÇÃO
-- =====================================================
-- Análise baseada na estrutura atual e padrões de uso identificados
-- Foco em consultas de usuários, hierarquia e views implementadas
-- =====================================================

-- =====================================================
-- 1. ÍNDICES EXISTENTES IDENTIFICADOS (SITUAÇÃO ATUAL)
-- =====================================================

/*
ESTRUTURA ATUAL DE ÍNDICES:

📋 USERS (Bem indexada):
  ✅ users_pkey (id)
  ✅ users_email_address_unique 
  ✅ users_person_id_unique
  ✅ users_is_system_admin_index
  ✅ users_deleted_at_index

📋 USER_ROLES (Muito bem indexada):
  ✅ user_roles_pkey (id)
  ✅ user_roles_user_id_index
  ✅ user_roles_role_id_index  
  ✅ user_roles_user_id_context_type_context_id_index
  ✅ user_roles_deleted_at_index
  ✅ idx_user_roles_context_type_id

📋 USER_ESTABLISHMENTS (Bem indexada):
  ✅ user_establishments_pkey (id)
  ✅ idx_user_establishments_user_id
  ✅ idx_user_establishments_establishment_id
  ✅ idx_user_establishments_deleted_at
  ✅ idx_user_establishments_primary

📋 PEOPLE (Adequadamente indexada):
  ✅ people_pkey (id)
  ✅ people_tax_id_unique
  ✅ people_name_index
  ✅ people_person_type_index
  ✅ people_deleted_at_index

📋 ESTABLISHMENTS (Bem indexada):
  ✅ establishments_pkey (id)
  ✅ establishments_company_id_index
  ✅ establishments_person_id_index
  ✅ establishments_deleted_at_index

📋 COMPANIES (Adequadamente indexada):
  ✅ companies_pkey (id)
  ✅ companies_person_id_unique
  ✅ companies_deleted_at_index
*/

-- =====================================================
-- 2. ÍNDICES ADICIONAIS RECOMENDADOS PARA OTIMIZAÇÃO
-- =====================================================

-- 2.1 ÍNDICES PARA VIEWS DE USUÁRIOS COMPLETOS
-- =====================================================

-- Otimizar ORDER BY das views (user_id, is_primary, is_principal, level)
CREATE INDEX IF NOT EXISTS idx_user_establishments_user_primary_order 
ON master.user_establishments (user_id, is_primary DESC, deleted_at) 
WHERE deleted_at IS NULL;

-- Otimizar filtros de estabelecimentos ativos
CREATE INDEX IF NOT EXISTS idx_establishments_active_principal 
ON master.establishments (is_active, is_principal DESC, company_id) 
WHERE deleted_at IS NULL;

-- Otimizar busca por roles ativos com level
CREATE INDEX IF NOT EXISTS idx_roles_active_level 
ON master.roles (is_active, level ASC) 
WHERE is_active = true;

-- 2.2 ÍNDICES PARA HIERARQUIA DE PERMISSÕES
-- =====================================================

-- Otimizar busca por context_type + level (para hierarquia)
CREATE INDEX IF NOT EXISTS idx_user_roles_context_level 
ON master.user_roles (user_id, context_type, deleted_at) 
INCLUDE (context_id, role_id)
WHERE deleted_at IS NULL;

-- Otimizar role levels para verificações hierárquicas
CREATE INDEX IF NOT EXISTS idx_roles_context_level_hierarchy 
ON master.roles (context_type, level DESC, is_active)
WHERE is_active = true;

-- Index para funções de controle de acesso (get_accessible_users_hierarchical)
CREATE INDEX IF NOT EXISTS idx_user_roles_level_context_active 
ON master.user_roles (user_id, deleted_at) 
INCLUDE (context_type, context_id, role_id)
WHERE deleted_at IS NULL;

-- 2.3 ÍNDICES PARA SISTEMA DE SESSÕES E TROCA DE PERFIL
-- =====================================================

-- Índices para tabela user_sessions (já foram criados no script anterior, mas listando aqui)
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active 
ON master.user_sessions (user_id, is_active, expires_at);

CREATE INDEX IF NOT EXISTS idx_user_sessions_token_active 
ON master.user_sessions (session_token, is_active) 
WHERE is_active = true AND expires_at > CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_user_sessions_context_active 
ON master.user_sessions (active_context_type, active_context_id, is_active)
WHERE is_active = true;

-- 2.4 ÍNDICES PARA CONSULTAS DE NEGÓCIO FREQUENTES  
-- =====================================================

-- Buscar usuários por estabelecimento (comum em filtros)
CREATE INDEX IF NOT EXISTS idx_user_establishments_estab_active_users 
ON master.user_establishments (establishment_id, deleted_at) 
INCLUDE (user_id, is_primary, status)
WHERE deleted_at IS NULL;

-- Buscar usuários por empresa (via estabelecimentos)
CREATE INDEX IF NOT EXISTS idx_establishments_company_active 
ON master.establishments (company_id, deleted_at, is_active) 
INCLUDE (id)
WHERE deleted_at IS NULL AND is_active = true;

-- Otimizar join people -> users (comum nas views)
CREATE INDEX IF NOT EXISTS idx_people_users_join 
ON master.people (id, deleted_at) 
INCLUDE (name, person_type, tax_id)
WHERE deleted_at IS NULL;

-- 2.5 ÍNDICES PARA AUDITORIA E LOG
-- =====================================================

-- Otimizar consultas de auditoria por data
CREATE INDEX IF NOT EXISTS idx_user_data_access_log_date_user 
ON master.user_data_access_log (created_at DESC, accessed_by_user_id);

CREATE INDEX IF NOT EXISTS idx_context_switches_date_user 
ON master.context_switches (created_at DESC, user_id);

-- Buscar logs por usuário específico
CREATE INDEX IF NOT EXISTS idx_context_switches_session_date 
ON master.context_switches (session_id, created_at DESC);

-- 2.6 ÍNDICES PARCIAIS PARA CASOS ESPECÍFICOS
-- =====================================================

-- Apenas usuários ativos (filtra 90%+ das consultas)
CREATE INDEX IF NOT EXISTS idx_users_active_only 
ON master.users (id, person_id, email_address, is_system_admin) 
WHERE deleted_at IS NULL AND is_active = true;

-- Apenas roles de sistema (super_admin, etc)
CREATE INDEX IF NOT EXISTS idx_user_roles_system_context 
ON master.user_roles (user_id, role_id, context_id) 
WHERE context_type = 'system' AND deleted_at IS NULL;

-- Apenas admins de empresa (level >= 80)
CREATE INDEX IF NOT EXISTS idx_user_roles_company_admins 
ON master.user_roles ur 
USING btree (user_id, context_id, deleted_at)
WHERE context_type = 'company' AND deleted_at IS NULL
  AND EXISTS (SELECT 1 FROM master.roles r WHERE r.id = ur.role_id AND r.level >= 80);

-- =====================================================
-- 3. ÍNDICES COMPOSTOS PARA QUERIES ESPECÍFICAS DAS VIEWS
-- =====================================================

-- Para vw_users_complete (join otimizado)
CREATE INDEX IF NOT EXISTS idx_users_complete_view_optimization 
ON master.users (id, person_id, deleted_at, is_active, is_system_admin)
WHERE deleted_at IS NULL;

-- Para função get_accessible_users_hierarchical
CREATE INDEX IF NOT EXISTS idx_hierarchy_access_optimization 
ON master.user_establishments (user_id, establishment_id, deleted_at, is_primary)
INCLUDE (status, permissions)
WHERE deleted_at IS NULL;

-- Para filtros por contexto hierarchical
CREATE INDEX IF NOT EXISTS idx_context_hierarchy_lookup 
ON master.user_roles (context_type, context_id, deleted_at)
INCLUDE (user_id, role_id)
WHERE deleted_at IS NULL;

-- =====================================================
-- 4. ÍNDICES DE PERFORMANCE PARA TEXT SEARCH
-- =====================================================

-- Busca por nome de pessoas (autocomplete)
CREATE INDEX IF NOT EXISTS idx_people_name_text_search 
ON master.people USING gin(to_tsvector('portuguese', name))
WHERE deleted_at IS NULL;

-- Busca por email (autocomplete para admins)
CREATE INDEX IF NOT EXISTS idx_users_email_text_search 
ON master.users USING gin(to_tsvector('portuguese', email_address))
WHERE deleted_at IS NULL AND is_active = true;

-- =====================================================
-- 5. ÍNDICES PARA MANUTENÇÃO E CLEANUP
-- =====================================================

-- Otimizar limpeza de sessões expiradas
CREATE INDEX IF NOT EXISTS idx_user_sessions_cleanup 
ON master.user_sessions (expires_at, is_active)
WHERE is_active = false OR expires_at < CURRENT_TIMESTAMP;

-- Otimizar limpeza de logs antigos
CREATE INDEX IF NOT EXISTS idx_audit_logs_cleanup 
ON master.user_data_access_log (created_at)
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- =====================================================
-- 6. ESTATÍSTICAS E MONITORAMENTO RECOMENDADO
-- =====================================================

-- Script para monitorar uso dos índices
/*
-- Verificar uso dos índices
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE schemaname = 'master' 
    AND tablename IN ('users', 'user_roles', 'user_establishments')
ORDER BY idx_scan DESC;

-- Verificar índices não utilizados (candidatos para remoção)
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes 
WHERE schemaname = 'master' 
    AND idx_scan = 0
    AND NOT indexname LIKE '%pkey';
*/

-- =====================================================
-- 7. ANÁLISE DE IMPACTO E PRIORIDADE
-- =====================================================

/*
PRIORIDADE ALTA (implementar primeiro):
✅ idx_user_establishments_user_primary_order - Para views principais
✅ idx_user_roles_context_level - Para hierarquia
✅ idx_users_active_only - Filtra maioria das consultas
✅ idx_establishments_company_active - Para joins empresa-estabelecimento

PRIORIDADE MÉDIA:
✅ idx_roles_context_level_hierarchy - Para validações hierárquicas  
✅ idx_user_establishments_estab_active_users - Para filtros por estabelecimento
✅ idx_people_name_text_search - Para autocomplete

PRIORIDADE BAIXA (monitorar necessidade):
✅ idx_context_switches_date_user - Apenas se auditoria for muito consultada
✅ idx_user_sessions_cleanup - Para manutenção automatizada
✅ Índices de texto - Se busca textual for implementada

OBSERVAÇÕES:
- A estrutura atual JÁ é muito bem indexada
- Muitos índices já cobrem os casos de uso principais  
- Implementar gradualmente e monitorar impacto
- Alguns índices podem ser desnecessários dependendo do volume
*/

-- =====================================================
-- 8. COMANDOS DE IMPLEMENTAÇÃO SEGURA
-- =====================================================

-- Implementar durante baixa utilização:
-- CREATE INDEX CONCURRENTLY quando possível
-- Monitorar espaço em disco antes da criação
-- Verificar planos de execução antes/depois

-- Exemplo de implementação segura:
-- CREATE INDEX CONCURRENTLY idx_user_establishments_user_primary_order 
-- ON master.user_establishments (user_id, is_primary DESC, deleted_at) 
-- WHERE deleted_at IS NULL;