-- =====================================================
-- Migration: 018_company_activation_fields.sql
-- Descrição: Adiciona campos para processo de ativação de empresas
-- Data: 2025-10-02
-- Autor: Sistema ProTeamCare
-- =====================================================

-- Contexto:
-- Este migration implementa o novo fluxo de ativação de empresas que inclui:
-- 1. Envio de email de aceite de contrato
-- 2. Registro de aceite de contrato pelo cliente
-- 3. Criação de usuário gestor
-- 4. Ativação completa do acesso da empresa

BEGIN;

-- =====================================================
-- 1. ADICIONAR NOVOS CAMPOS À TABELA COMPANIES
-- =====================================================

ALTER TABLE master.companies
    ADD COLUMN IF NOT EXISTS access_status VARCHAR(20) DEFAULT 'pending_contract',
    ADD COLUMN IF NOT EXISTS contract_terms_version VARCHAR(10),
    ADD COLUMN IF NOT EXISTS contract_accepted_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS contract_accepted_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS contract_ip_address VARCHAR(45),
    ADD COLUMN IF NOT EXISTS activation_sent_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS activation_sent_to VARCHAR(255),
    ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS activated_by_user_id BIGINT;

-- =====================================================
-- 2. ADICIONAR COMENTÁRIOS NOS CAMPOS
-- =====================================================

COMMENT ON COLUMN master.companies.access_status IS
    'Status de ativação: pending_contract, contract_signed, pending_user, active, suspended';

COMMENT ON COLUMN master.companies.contract_terms_version IS
    'Versão dos termos de uso aceitos (ex: 1.0, 1.1)';

COMMENT ON COLUMN master.companies.contract_accepted_at IS
    'Data e hora em que o contrato foi aceito';

COMMENT ON COLUMN master.companies.contract_accepted_by IS
    'Email ou nome de quem aceitou o contrato';

COMMENT ON COLUMN master.companies.contract_ip_address IS
    'Endereço IP de onde o contrato foi aceito (compliance/auditoria)';

COMMENT ON COLUMN master.companies.activation_sent_at IS
    'Data e hora do último envio de email de ativação';

COMMENT ON COLUMN master.companies.activation_sent_to IS
    'Email para quem foi enviado o convite de ativação';

COMMENT ON COLUMN master.companies.activated_at IS
    'Data e hora em que a empresa foi totalmente ativada';

COMMENT ON COLUMN master.companies.activated_by_user_id IS
    'ID do usuário gestor que completou a ativação';

-- =====================================================
-- 3. CRIAR ÍNDICES PARA PERFORMANCE
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_companies_access_status
    ON master.companies(access_status);

CREATE INDEX IF NOT EXISTS idx_companies_contract_accepted_at
    ON master.companies(contract_accepted_at);

CREATE INDEX IF NOT EXISTS idx_companies_activated_at
    ON master.companies(activated_at);

CREATE INDEX IF NOT EXISTS idx_companies_activation_sent_at
    ON master.companies(activation_sent_at);

-- =====================================================
-- 4. ADICIONAR CONSTRAINT DE STATUS
-- =====================================================

ALTER TABLE master.companies
    DROP CONSTRAINT IF EXISTS companies_access_status_check;

ALTER TABLE master.companies
    ADD CONSTRAINT companies_access_status_check
    CHECK (access_status IN (
        'pending_contract',    -- Aguardando envio/aceite de contrato
        'contract_signed',     -- Contrato aceito, aguardando usuário
        'pending_user',        -- Email de criação de usuário enviado
        'active',              -- Empresa ativa e funcional
        'suspended'            -- Empresa suspensa (sem acesso)
    ));

-- =====================================================
-- 5. ADICIONAR FOREIGN KEY
-- =====================================================

ALTER TABLE master.companies
    DROP CONSTRAINT IF EXISTS fk_companies_activated_by_user;

ALTER TABLE master.companies
    ADD CONSTRAINT fk_companies_activated_by_user
    FOREIGN KEY (activated_by_user_id)
    REFERENCES master.users(id)
    ON DELETE SET NULL;

-- =====================================================
-- 6. ATUALIZAR EMPRESAS EXISTENTES
-- =====================================================

-- Empresas que já têm usuários ativos são consideradas ativas
UPDATE master.companies c
SET
    access_status = 'active',
    activated_at = c.created_at,
    contract_accepted_at = c.created_at,
    contract_terms_version = '1.0'
WHERE EXISTS (
    SELECT 1
    FROM master.users u
    WHERE u.company_id = c.id
    AND u.status = 'active'
    AND u.context_type = 'company'
    LIMIT 1
);

-- Empresas sem usuários ficam aguardando contrato
UPDATE master.companies c
SET
    access_status = 'pending_contract'
WHERE NOT EXISTS (
    SELECT 1
    FROM master.users u
    WHERE u.company_id = c.id
    AND u.status = 'active'
    AND u.context_type = 'company'
);

-- =====================================================
-- 7. CRIAR FUNÇÃO HELPER PARA VERIFICAR STATUS
-- =====================================================

CREATE OR REPLACE FUNCTION master.fn_get_company_activation_status(p_company_id BIGINT)
RETURNS TABLE (
    company_id BIGINT,
    company_name VARCHAR,
    access_status VARCHAR,
    has_contract BOOLEAN,
    has_active_user BOOLEAN,
    has_subscription BOOLEAN,
    activation_days_pending INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        p.name,
        c.access_status,
        (c.contract_accepted_at IS NOT NULL) as has_contract,
        EXISTS(
            SELECT 1 FROM master.users u
            WHERE u.company_id = c.id
            AND u.status = 'active'
            AND u.context_type = 'company'
        ) as has_active_user,
        EXISTS(
            SELECT 1 FROM master.company_subscriptions s
            WHERE s.company_id = c.id
            AND s.status = 'active'
        ) as has_subscription,
        CASE
            WHEN c.activation_sent_at IS NOT NULL
            THEN EXTRACT(DAY FROM (NOW() - c.activation_sent_at))::INTEGER
            ELSE NULL
        END as activation_days_pending
    FROM master.companies c
    LEFT JOIN master.people p ON p.id = c.person_id
    WHERE c.id = p_company_id;
END;
$$;

COMMENT ON FUNCTION master.fn_get_company_activation_status IS
    'Retorna status detalhado de ativação de uma empresa';

-- =====================================================
-- 8. CRIAR VIEW PARA EMPRESAS PENDENTES
-- =====================================================

CREATE OR REPLACE VIEW master.vw_companies_pending_activation AS
SELECT
    c.id,
    c.access_status,
    p.name as company_name,
    p.tax_id as cnpj,
    p.status as people_status,
    c.activation_sent_at,
    c.activation_sent_to,
    c.contract_accepted_at,
    c.contract_accepted_by,
    c.created_at,
    EXTRACT(DAY FROM (NOW() - c.created_at))::INTEGER as days_since_creation,
    CASE
        WHEN c.activation_sent_at IS NOT NULL
        THEN EXTRACT(DAY FROM (NOW() - c.activation_sent_at))::INTEGER
        ELSE NULL
    END as days_since_activation_sent,
    (SELECT COUNT(*) FROM master.users u WHERE u.company_id = c.id) as users_count
FROM master.companies c
LEFT JOIN master.people p ON p.id = c.person_id
WHERE c.access_status IN ('pending_contract', 'contract_signed', 'pending_user')
AND c.deleted_at IS NULL
ORDER BY c.created_at DESC;

COMMENT ON VIEW master.vw_companies_pending_activation IS
    'View com empresas que estão pendentes de ativação completa';

-- =====================================================
-- 9. GRANT PERMISSIONS
-- =====================================================

GRANT SELECT ON master.vw_companies_pending_activation TO postgres;
GRANT EXECUTE ON FUNCTION master.fn_get_company_activation_status TO postgres;

-- =====================================================
-- 10. LOG DE EXECUÇÃO
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 018 executada com sucesso!';
    RAISE NOTICE '   - Campos de ativação adicionados à tabela companies';
    RAISE NOTICE '   - Índices criados para performance';
    RAISE NOTICE '   - Constraints de status aplicados';
    RAISE NOTICE '   - % empresas atualizadas para status active',
        (SELECT COUNT(*) FROM master.companies WHERE access_status = 'active');
    RAISE NOTICE '   - % empresas marcadas como pending_contract',
        (SELECT COUNT(*) FROM master.companies WHERE access_status = 'pending_contract');
    RAISE NOTICE '   - View vw_companies_pending_activation criada';
    RAISE NOTICE '   - Função fn_get_company_activation_status criada';
END $$;

COMMIT;

-- =====================================================
-- ROLLBACK (caso necessário)
-- =====================================================
-- Para reverter esta migration, execute:
/*
BEGIN;

-- Remover view
DROP VIEW IF EXISTS master.vw_companies_pending_activation;

-- Remover função
DROP FUNCTION IF EXISTS master.fn_get_company_activation_status;

-- Remover constraint
ALTER TABLE master.companies DROP CONSTRAINT IF EXISTS companies_access_status_check;
ALTER TABLE master.companies DROP CONSTRAINT IF EXISTS fk_companies_activated_by_user;

-- Remover índices
DROP INDEX IF EXISTS master.idx_companies_access_status;
DROP INDEX IF EXISTS master.idx_companies_contract_accepted_at;
DROP INDEX IF EXISTS master.idx_companies_activated_at;
DROP INDEX IF EXISTS master.idx_companies_activation_sent_at;

-- Remover colunas
ALTER TABLE master.companies
    DROP COLUMN IF EXISTS access_status,
    DROP COLUMN IF EXISTS contract_terms_version,
    DROP COLUMN IF EXISTS contract_accepted_at,
    DROP COLUMN IF EXISTS contract_accepted_by,
    DROP COLUMN IF EXISTS contract_ip_address,
    DROP COLUMN IF EXISTS activation_sent_at,
    DROP COLUMN IF EXISTS activation_sent_to,
    DROP COLUMN IF EXISTS activated_at,
    DROP COLUMN IF EXISTS activated_by_user_id;

COMMIT;
*/
