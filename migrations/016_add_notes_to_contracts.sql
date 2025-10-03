-- Migration: Adicionar campo notes à tabela contracts
-- Data: 2024-09-24
-- Objetivo: Resolver inconsistência entre frontend e banco de dados

-- Adicionar campo notes para observações do contrato
ALTER TABLE master.contracts
ADD COLUMN notes TEXT;

-- Adicionar comentário para documentação
COMMENT ON COLUMN master.contracts.notes IS 'Observações adicionais sobre o contrato';

-- Índice para busca por texto (opcional, para performance futura)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contracts_notes_text
ON master.contracts USING gin(to_tsvector('portuguese', notes))
WHERE notes IS NOT NULL;

-- Migration executada com sucesso em 2024-09-24
-- Campo notes adicionado à tabela contracts