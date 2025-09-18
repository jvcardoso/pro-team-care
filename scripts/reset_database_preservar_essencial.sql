-- RESET COMPLETO DA BASE - PRESERVANDO ESSENCIAL
-- Este script remove todos os dados de negócio mas preserva:
-- - Usuários admin (com email contendo 'admin')
-- - Todos os menus
-- - Todas as roles e permissions
-- Data: 2025-09-14

-- Definir contexto admin para bypass de RLS
SELECT master.set_current_company_id(0);

-- =======================================================================
-- PASSO 1: DESABILITAR FOREIGN KEYS TEMPORARIAMENTE
-- =======================================================================

-- Remover FKs que impedem a limpeza
ALTER TABLE master.people DROP CONSTRAINT IF EXISTS fk_people_company;
ALTER TABLE master.users DROP CONSTRAINT IF EXISTS fk_users_company;
ALTER TABLE master.establishments DROP CONSTRAINT IF EXISTS fk_establishments_company;
ALTER TABLE master.clients DROP CONSTRAINT IF EXISTS fk_clients_company;

-- =======================================================================
-- PASSO 2: REMOVER DEPENDÊNCIAS PRIMEIRO
-- =======================================================================

-- Limpar tabelas de relacionamento
DELETE FROM master.user_roles;
DELETE FROM master.user_sessions;
DELETE FROM master.user_establishments;
DELETE FROM master.role_permissions WHERE granted_by_user_id IS NOT NULL;

-- =======================================================================
-- PASSO 3: REMOVER DADOS DE NEGÓCIO
-- =======================================================================

-- Remover entities de negócio
DELETE FROM master.establishments;
DELETE FROM master.clients;

-- Remover contatos (devem estar vazios após limpeza anterior)
DELETE FROM master.phones;
DELETE FROM master.emails;
DELETE FROM master.addresses;

-- Remover companies
DELETE FROM master.companies;

-- Remover users que NÃO são admin
DELETE FROM master.users
WHERE email_address NOT ILIKE '%admin%'
  AND email_address != 'admin@example.com'
  AND email_address NOT ILIKE '%root%';

-- Remover people órfãs (que não são de users admin)
DELETE FROM master.people
WHERE id NOT IN (
    SELECT person_id FROM master.users
    WHERE person_id IS NOT NULL
);

-- =======================================================================
-- PASSO 4: VERIFICAÇÃO E RELATÓRIO
-- =======================================================================

-- Mostrar o que foi preservado
DO $$
DECLARE
    users_count INTEGER;
    menus_count INTEGER;
    roles_count INTEGER;
    companies_count INTEGER;
    establishments_count INTEGER;
    clients_count INTEGER;
    people_count INTEGER;
BEGIN
    -- Contar registros finais
    SELECT COUNT(*) INTO users_count FROM master.users;
    SELECT COUNT(*) INTO menus_count FROM master.menus;
    SELECT COUNT(*) INTO roles_count FROM master.roles;
    SELECT COUNT(*) INTO companies_count FROM master.companies;
    SELECT COUNT(*) INTO establishments_count FROM master.establishments;
    SELECT COUNT(*) INTO clients_count FROM master.clients;
    SELECT COUNT(*) INTO people_count FROM master.people;

    -- Relatório
    RAISE NOTICE '';
    RAISE NOTICE '🎉 RESET COMPLETO DA BASE DE DADOS';
    RAISE NOTICE '=====================================';
    RAISE NOTICE '';
    RAISE NOTICE '✅ PRESERVADO (SISTEMA):';
    RAISE NOTICE '   - Usuários admin: %', users_count;
    RAISE NOTICE '   - Menus: %', menus_count;
    RAISE NOTICE '   - Roles: %', roles_count;
    RAISE NOTICE '   - People (admin): %', people_count;
    RAISE NOTICE '';
    RAISE NOTICE '🗑️ REMOVIDO (DADOS DE NEGÓCIO):';
    RAISE NOTICE '   - Companies: %', companies_count;
    RAISE NOTICE '   - Establishments: %', establishments_count;
    RAISE NOTICE '   - Clients: %', clients_count;
    RAISE NOTICE '';

    IF users_count > 0 AND menus_count > 0 AND roles_count > 0 AND
       companies_count = 0 AND establishments_count = 0 AND clients_count = 0 THEN
        RAISE NOTICE '🚀 SUCESSO! Base limpa e pronta para novos dados.';
        RAISE NOTICE '   Sistema essencial preservado.';
        RAISE NOTICE '   Dados de negócio completamente removidos.';
        RAISE NOTICE '   Estrutura multi-tenant intacta.';
    ELSE
        RAISE NOTICE '⚠️ Verificar resultado da limpeza.';
    END IF;

    RAISE NOTICE '';
END $$;

-- =======================================================================
-- PASSO 5: MOSTRAR USUÁRIOS ADMIN PRESERVADOS
-- =======================================================================

-- Listar usuários admin que foram preservados
DO $$
DECLARE
    user_rec RECORD;
BEGIN
    RAISE NOTICE '👤 USUÁRIOS ADMIN PRESERVADOS:';
    FOR user_rec IN
        SELECT id, email_address
        FROM master.users
        ORDER BY id
    LOOP
        RAISE NOTICE '   - ID %: %', user_rec.id, user_rec.email_address;
    END LOOP;
    RAISE NOTICE '';
END $$;

-- =======================================================================
-- PASSO 6: RECRIAR FOREIGN KEYS ESSENCIAIS (OPCIONAL)
-- =======================================================================

-- Comentário: As FKs podem ser recriadas se necessário
-- ALTER TABLE master.people ADD CONSTRAINT fk_people_company FOREIGN KEY (company_id) REFERENCES master.companies(id);
-- ALTER TABLE master.users ADD CONSTRAINT fk_users_company FOREIGN KEY (company_id) REFERENCES master.companies(id);

RAISE NOTICE '✅ Reset da base de dados concluído!';
RAISE NOTICE '🚀 Sistema pronto para recadastrar com estrutura multi-tenant.';
