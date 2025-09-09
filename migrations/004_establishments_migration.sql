-- =====================================================
-- MIGRAÇÃO URGENTE - ESTABLISHMENTS DEPENDENCY FIX
-- Arquivo: migrations/004_establishments_migration.sql
-- Data: 2025-09-08
-- =====================================================

-- 1. Adicionar campos faltantes
ALTER TABLE master.establishments 
    ADD COLUMN IF NOT EXISTS display_order INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS metadata JSONB NULL;

-- 2. Popular display_order para registros existentes
UPDATE master.establishments 
SET display_order = ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY id)
WHERE deleted_at IS NULL;

-- 3. Criar índices necessários
CREATE INDEX IF NOT EXISTS idx_establishments_display_order 
ON master.establishments (company_id, display_order) 
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_establishments_metadata_gin 
ON master.establishments USING GIN (metadata) 
WHERE deleted_at IS NULL AND metadata IS NOT NULL;

-- 4. Constraint única display_order por company
CREATE UNIQUE INDEX IF NOT EXISTS idx_establishments_company_display_unique 
ON master.establishments (company_id, display_order) 
WHERE deleted_at IS NULL;

-- 5. Constraint business rule: apenas 1 principal por company
CREATE UNIQUE INDEX IF NOT EXISTS idx_establishments_company_principal_unique 
ON master.establishments (company_id) 
WHERE deleted_at IS NULL AND is_principal = true;

-- 6. Função de Validação Company->Establishment
CREATE OR REPLACE FUNCTION master.validate_establishment_creation(
    company_id_param BIGINT,
    code_param VARCHAR,
    is_principal_param BOOLEAN DEFAULT false
) RETURNS TABLE(
    is_valid BOOLEAN,
    error_message TEXT,
    suggested_display_order INTEGER
) AS $$
DECLARE
    company_exists BOOLEAN;
    code_exists BOOLEAN;
    principal_exists BOOLEAN;
    next_order INTEGER;
BEGIN
    -- Verificar se company existe e está ativa
    SELECT EXISTS(
        SELECT 1 FROM master.companies 
        WHERE id = company_id_param AND deleted_at IS NULL
    ) INTO company_exists;
    
    -- Verificar code único na company
    SELECT EXISTS(
        SELECT 1 FROM master.establishments 
        WHERE company_id = company_id_param 
          AND code = code_param 
          AND deleted_at IS NULL
    ) INTO code_exists;
    
    -- Verificar se já existe principal
    IF is_principal_param THEN
        SELECT EXISTS(
            SELECT 1 FROM master.establishments 
            WHERE company_id = company_id_param 
              AND is_principal = true 
              AND deleted_at IS NULL
        ) INTO principal_exists;
    ELSE
        principal_exists := false;
    END IF;
    
    -- Calcular próximo display_order
    SELECT COALESCE(MAX(display_order), 0) + 1 INTO next_order
    FROM master.establishments 
    WHERE company_id = company_id_param AND deleted_at IS NULL;
    
    -- Retornar validação
    RETURN QUERY
    SELECT 
        company_exists AND NOT code_exists AND NOT principal_exists,
        CASE 
            WHEN NOT company_exists THEN 'Company não encontrada ou inativa'
            WHEN code_exists THEN 'Code já existe nesta company'
            WHEN principal_exists THEN 'Já existe establishment principal nesta company'
            ELSE 'OK'
        END,
        next_order;
END;
$$ LANGUAGE plpgsql;

-- 7. Função de Reordenação
CREATE OR REPLACE FUNCTION master.reorder_establishments(
    company_id_param BIGINT,
    establishment_orders JSONB -- [{"id": 1, "order": 1}, {"id": 2, "order": 2}]
) RETURNS BOOLEAN AS $$
DECLARE
    order_item JSONB;
BEGIN
    -- Atualizar display_order de cada establishment
    FOR order_item IN SELECT * FROM jsonb_array_elements(establishment_orders)
    LOOP
        UPDATE master.establishments 
        SET display_order = (order_item->>'order')::INTEGER,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = (order_item->>'id')::BIGINT 
          AND company_id = company_id_param
          AND deleted_at IS NULL;
    END LOOP;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- 8. View Pública
CREATE OR REPLACE VIEW master.vw_establishments_public AS
SELECT 
    e.id AS establishment_id,
    e.code AS establishment_code,
    e.type AS establishment_type,
    e.category AS establishment_category,
    e.is_active AS establishment_is_active,
    e.is_principal AS establishment_is_principal,
    e.display_order AS establishment_order,
    -- Mascaramento de dados sensíveis
    CONCAT('COMP_', e.company_id) AS company_reference,
    -- Status dos campos JSONB
    CASE WHEN e.settings IS NOT NULL THEN 'CONFIGURED' ELSE 'DEFAULT' END AS settings_status,
    CASE WHEN e.metadata IS NOT NULL THEN 'HAS_METADATA' ELSE 'NO_METADATA' END AS metadata_status,
    CASE WHEN e.operating_hours IS NOT NULL THEN 'HAS_HOURS' ELSE 'DEFAULT_HOURS' END AS hours_status,
    e.created_at
FROM master.establishments e
WHERE e.deleted_at IS NULL 
  AND e.is_active = true
ORDER BY e.company_id, e.display_order;

-- 9. View Admin Completa
CREATE OR REPLACE VIEW master.vw_establishments_admin AS
SELECT 
    e.*,
    c.person_id AS company_person_id,
    p.name AS company_name,
    p.tax_id AS company_tax_id,
    -- Contadores de relacionamentos
    (SELECT COUNT(*) FROM master.user_establishments ue 
     WHERE ue.establishment_id = e.id AND ue.deleted_at IS NULL) AS user_count,
    (SELECT COUNT(*) FROM master.professionals pr 
     WHERE pr.establishment_id = e.id AND pr.deleted_at IS NULL) AS professional_count,
    (SELECT COUNT(*) FROM master.clients cl 
     WHERE cl.establishment_id = e.id AND cl.deleted_at IS NULL) AS client_count,
    (SELECT COUNT(*) FROM master.establishment_settings es 
     WHERE es.establishment_id = e.id AND es.deleted_at IS NULL) AS setting_count
FROM master.establishments e
JOIN master.companies c ON e.company_id = c.id
JOIN master.people p ON c.person_id = p.id
WHERE e.deleted_at IS NULL
  AND c.deleted_at IS NULL
ORDER BY c.id, e.display_order;

-- 10. View Hierárquica Company->Establishment
CREATE OR REPLACE VIEW master.vw_company_establishments AS
SELECT 
    c.id AS company_id,
    c.person_id AS company_person_id,
    c.display_order AS company_order,
    pc.name AS company_name,
    e.id AS establishment_id,
    e.person_id AS establishment_person_id,
    e.code AS establishment_code,
    e.type AS establishment_type,
    e.category AS establishment_category,
    e.is_principal AS establishment_is_principal,
    e.display_order AS establishment_order,
    pe.name AS establishment_name,
    -- Indicadores de relacionamento
    CASE WHEN e.person_id = c.person_id THEN 'SAME_ENTITY' ELSE 'DIFFERENT_ENTITY' END AS entity_relationship
FROM master.companies c
JOIN master.people pc ON c.person_id = pc.id
LEFT JOIN master.establishments e ON c.id = e.company_id AND e.deleted_at IS NULL
LEFT JOIN master.people pe ON e.person_id = pe.id
WHERE c.deleted_at IS NULL
ORDER BY c.display_order, e.display_order;