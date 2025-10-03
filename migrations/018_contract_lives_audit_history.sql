-- =====================================================
-- Migration: 018 - Contract Lives Audit History System
-- Description: Implementa sistema de auditoria automática
--              para rastreamento de mudanças em vidas de contratos
-- Author: Sistema Pro Team Care
-- Date: 2025-10-03
-- =====================================================

BEGIN;

-- =====================================================
-- 1. CRIAR TABELA DE HISTÓRICO DE AUDITORIA
-- =====================================================

CREATE TABLE IF NOT EXISTS master.contract_lives_history (
    id BIGSERIAL PRIMARY KEY,
    contract_life_id BIGINT NOT NULL REFERENCES master.contract_lives(id) ON DELETE CASCADE,

    -- Tipo de ação realizada
    action VARCHAR(20) NOT NULL,

    -- Metadados da mudança
    changed_fields JSONB,           -- Lista de campos alterados
    old_values JSONB,               -- Valores antigos dos campos
    new_values JSONB,               -- Valores novos dos campos

    -- Informações de contexto
    changed_by BIGINT REFERENCES master.users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Dados adicionais (IP, user agent, etc)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Check constraint
    CONSTRAINT clh_action_check CHECK (action IN ('created', 'updated', 'substituted', 'cancelled'))
);

-- Comentários da tabela
COMMENT ON TABLE master.contract_lives_history IS 'Histórico de auditoria de todas as mudanças em vidas de contratos';
COMMENT ON COLUMN master.contract_lives_history.action IS 'Tipo de ação: created, updated, substituted, cancelled';
COMMENT ON COLUMN master.contract_lives_history.changed_fields IS 'Array de nomes dos campos que foram alterados';
COMMENT ON COLUMN master.contract_lives_history.old_values IS 'Objeto JSON com valores antigos dos campos alterados';
COMMENT ON COLUMN master.contract_lives_history.new_values IS 'Objeto JSON com valores novos dos campos alterados';
COMMENT ON COLUMN master.contract_lives_history.changed_by IS 'ID do usuário que realizou a mudança';
COMMENT ON COLUMN master.contract_lives_history.metadata IS 'Metadados adicionais (IP, user agent, etc)';

-- =====================================================
-- 2. CRIAR ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Busca por vida
CREATE INDEX idx_contract_lives_history_life_id
ON master.contract_lives_history(contract_life_id);

-- Busca por usuário que fez a mudança
CREATE INDEX idx_contract_lives_history_changed_by
ON master.contract_lives_history(changed_by);

-- Busca por data (histórico recente)
CREATE INDEX idx_contract_lives_history_changed_at
ON master.contract_lives_history(changed_at DESC);

-- Busca por tipo de ação
CREATE INDEX idx_contract_lives_history_action
ON master.contract_lives_history(action);

-- Índice composto para timeline de uma vida
CREATE INDEX idx_contract_lives_history_timeline
ON master.contract_lives_history(contract_life_id, changed_at DESC);

-- Índice GIN para busca em campos alterados
CREATE INDEX idx_contract_lives_history_changed_fields_gin
ON master.contract_lives_history USING gin(changed_fields);

-- =====================================================
-- 3. CRIAR FUNÇÃO DE AUDITORIA AUTOMÁTICA
-- =====================================================

CREATE OR REPLACE FUNCTION master.fn_audit_contract_lives()
RETURNS TRIGGER AS $$
DECLARE
    v_action VARCHAR(20);
    v_changed_fields JSONB := '[]'::jsonb;
    v_old_values JSONB := '{}'::jsonb;
    v_new_values JSONB := '{}'::jsonb;
    v_field_name TEXT;
    v_old_value TEXT;
    v_new_value TEXT;
BEGIN
    -- Determinar tipo de ação
    IF (TG_OP = 'INSERT') THEN
        v_action := 'created';

        -- Para INSERT, todos os campos são "novos"
        v_new_values := to_jsonb(NEW);

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Detectar tipo de update
        IF (NEW.status = 'substituted' AND OLD.status != 'substituted') THEN
            v_action := 'substituted';
        ELSIF (NEW.status = 'cancelled' AND OLD.status != 'cancelled') THEN
            v_action := 'cancelled';
        ELSE
            v_action := 'updated';
        END IF;

        -- Comparar cada campo relevante para detectar mudanças
        IF (OLD.start_date IS DISTINCT FROM NEW.start_date) THEN
            v_changed_fields := v_changed_fields || '"start_date"'::jsonb;
            v_old_values := jsonb_set(v_old_values, '{start_date}', to_jsonb(OLD.start_date::text));
            v_new_values := jsonb_set(v_new_values, '{start_date}', to_jsonb(NEW.start_date::text));
        END IF;

        IF (OLD.end_date IS DISTINCT FROM NEW.end_date) THEN
            v_changed_fields := v_changed_fields || '"end_date"'::jsonb;
            v_old_values := jsonb_set(v_old_values, '{end_date}', to_jsonb(OLD.end_date::text));
            v_new_values := jsonb_set(v_new_values, '{end_date}', to_jsonb(NEW.end_date::text));
        END IF;

        IF (OLD.relationship_type IS DISTINCT FROM NEW.relationship_type) THEN
            v_changed_fields := v_changed_fields || '"relationship_type"'::jsonb;
            v_old_values := jsonb_set(v_old_values, '{relationship_type}', to_jsonb(OLD.relationship_type));
            v_new_values := jsonb_set(v_new_values, '{relationship_type}', to_jsonb(NEW.relationship_type));
        END IF;

        IF (OLD.status IS DISTINCT FROM NEW.status) THEN
            v_changed_fields := v_changed_fields || '"status"'::jsonb;
            v_old_values := jsonb_set(v_old_values, '{status}', to_jsonb(OLD.status));
            v_new_values := jsonb_set(v_new_values, '{status}', to_jsonb(NEW.status));
        END IF;

        IF (OLD.substitution_reason IS DISTINCT FROM NEW.substitution_reason) THEN
            v_changed_fields := v_changed_fields || '"substitution_reason"'::jsonb;
            v_old_values := jsonb_set(v_old_values, '{substitution_reason}', to_jsonb(OLD.substitution_reason));
            v_new_values := jsonb_set(v_new_values, '{substitution_reason}', to_jsonb(NEW.substitution_reason));
        END IF;

        IF (OLD.primary_service_address IS DISTINCT FROM NEW.primary_service_address) THEN
            v_changed_fields := v_changed_fields || '"primary_service_address"'::jsonb;
            v_old_values := jsonb_set(v_old_values, '{primary_service_address}', COALESCE(OLD.primary_service_address, 'null'::jsonb));
            v_new_values := jsonb_set(v_new_values, '{primary_service_address}', COALESCE(NEW.primary_service_address, 'null'::jsonb));
        END IF;

    ELSIF (TG_OP = 'DELETE') THEN
        v_action := 'deleted';
        v_old_values := to_jsonb(OLD);
    END IF;

    -- Inserir registro de auditoria
    INSERT INTO master.contract_lives_history (
        contract_life_id,
        action,
        changed_fields,
        old_values,
        new_values,
        changed_by,
        changed_at,
        metadata
    ) VALUES (
        COALESCE(NEW.id, OLD.id),
        v_action,
        CASE WHEN jsonb_array_length(v_changed_fields) > 0 THEN v_changed_fields ELSE NULL END,
        CASE WHEN v_old_values != '{}'::jsonb THEN v_old_values ELSE NULL END,
        CASE WHEN v_new_values != '{}'::jsonb THEN v_new_values ELSE NULL END,
        COALESCE(NEW.created_by, OLD.created_by),
        NOW(),
        jsonb_build_object(
            'table', TG_TABLE_NAME,
            'operation', TG_OP,
            'schema', TG_TABLE_SCHEMA
        )
    );

    -- Retornar registro apropriado
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Comentário da função
COMMENT ON FUNCTION master.fn_audit_contract_lives() IS
'Função de trigger que registra automaticamente todas as mudanças em contract_lives';

-- =====================================================
-- 4. CRIAR TRIGGER PARA AUDITORIA AUTOMÁTICA
-- =====================================================

-- Remover trigger se já existir
DROP TRIGGER IF EXISTS tr_contract_lives_audit ON master.contract_lives;

-- Criar trigger
CREATE TRIGGER tr_contract_lives_audit
    AFTER INSERT OR UPDATE OR DELETE
    ON master.contract_lives
    FOR EACH ROW
    EXECUTE FUNCTION master.fn_audit_contract_lives();

COMMENT ON TRIGGER tr_contract_lives_audit ON master.contract_lives IS
'Trigger que captura todas as operações (INSERT, UPDATE, DELETE) em contract_lives para auditoria';

-- =====================================================
-- 5. CRIAR VIEW PARA HISTÓRICO ENRIQUECIDO
-- =====================================================

CREATE OR REPLACE VIEW master.v_contract_lives_history_enriched AS
SELECT
    clh.id,
    clh.contract_life_id,
    clh.action,
    clh.changed_fields,
    clh.old_values,
    clh.new_values,
    clh.changed_by,
    clh.changed_at,
    clh.metadata,

    -- Informações da vida
    cl.person_id,
    p.name AS person_name,
    cl.contract_id,
    c.contract_number,

    -- Informações do usuário que fez a mudança
    u.email_address AS changed_by_email,
    pu.name AS changed_by_name

FROM master.contract_lives_history clh
LEFT JOIN master.contract_lives cl ON clh.contract_life_id = cl.id
LEFT JOIN master.people p ON cl.person_id = p.id
LEFT JOIN master.contracts c ON cl.contract_id = c.id
LEFT JOIN master.users u ON clh.changed_by = u.id
LEFT JOIN master.people pu ON u.person_id = pu.id
ORDER BY clh.changed_at DESC;

COMMENT ON VIEW master.v_contract_lives_history_enriched IS
'View enriquecida do histórico de auditoria com joins de informações relacionadas';

-- =====================================================
-- 6. GRANT PERMISSIONS
-- =====================================================

-- Permissões na tabela de histórico (read-only para usuários normais)
GRANT SELECT ON master.contract_lives_history TO PUBLIC;
GRANT INSERT ON master.contract_lives_history TO postgres; -- Apenas trigger pode inserir

-- Permissões na view enriquecida
GRANT SELECT ON master.v_contract_lives_history_enriched TO PUBLIC;

-- =====================================================
-- 7. INSERIR REGISTROS HISTÓRICOS PARA VIDAS EXISTENTES
-- =====================================================

-- Criar histórico "created" para todas as vidas já existentes
INSERT INTO master.contract_lives_history (
    contract_life_id,
    action,
    changed_fields,
    old_values,
    new_values,
    changed_by,
    changed_at,
    metadata
)
SELECT
    id,
    'created',
    NULL,
    NULL,
    to_jsonb(cl.*),
    created_by,
    created_at,
    jsonb_build_object('migration', '018_backfill', 'source', 'existing_records')
FROM master.contract_lives cl
WHERE NOT EXISTS (
    SELECT 1
    FROM master.contract_lives_history clh
    WHERE clh.contract_life_id = cl.id
    AND clh.action = 'created'
);

-- =====================================================
-- FIM DA MIGRATION
-- =====================================================

COMMIT;

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 018 executada com sucesso!';
    RAISE NOTICE '📊 Tabela contract_lives_history criada';
    RAISE NOTICE '🔧 Trigger de auditoria automática configurado';
    RAISE NOTICE '👁️ View enriquecida disponível: v_contract_lives_history_enriched';
    RAISE NOTICE '📝 Histórico backfill para registros existentes completado';
END $$;
