-- Migration: Add User Management Fields for Company/Establishment Context
-- Adicionando campos para gestão de usuários com contexto empresa/estabelecimento

BEGIN;

-- 1. Adicionar campos na tabela users
ALTER TABLE master.users
ADD COLUMN IF NOT EXISTS establishment_id BIGINT REFERENCES master.establishments (
    id
),
ADD COLUMN IF NOT EXISTS context_type VARCHAR(
    20
) DEFAULT 'establishment' CHECK (
    context_type IN ('company', 'establishment', 'client')
),
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active' CHECK (
    status IN ('active', 'inactive', 'pending', 'suspended', 'blocked')
),
ADD COLUMN IF NOT EXISTS activation_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS activation_expires_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS password_reset_expires_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS invited_by_user_id BIGINT REFERENCES master.users (id),
ADD COLUMN IF NOT EXISTS invited_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP;

-- 2. Adicionar índices para performance
CREATE INDEX IF NOT EXISTS users_establishment_id_idx ON master.users (
    establishment_id
);
CREATE INDEX IF NOT EXISTS users_context_type_idx ON master.users (
    context_type
);
CREATE INDEX IF NOT EXISTS users_status_idx ON master.users (status);
CREATE INDEX IF NOT EXISTS users_activation_token_idx ON master.users (
    activation_token
);
CREATE INDEX IF NOT EXISTS users_password_reset_token_idx ON master.users (
    password_reset_token
);
CREATE INDEX IF NOT EXISTS users_invited_by_idx ON master.users (
    invited_by_user_id
);

-- 3. Comentários para documentação
COMMENT ON COLUMN master.users.establishment_id IS 'ID do estabelecimento para usuários com contexto establishment';
COMMENT ON COLUMN master.users.context_type IS 'Tipo de contexto do usuário: company, establishment, client';
COMMENT ON COLUMN master.users.status IS 'Status do usuário: active, inactive, pending, suspended, blocked';
COMMENT ON COLUMN master.users.activation_token IS 'Token para ativação da conta';
COMMENT ON COLUMN master.users.activation_expires_at IS 'Data de expiração do token de ativação';
COMMENT ON COLUMN master.users.password_reset_token IS 'Token para reset de senha';
COMMENT ON COLUMN master.users.password_reset_expires_at IS 'Data de expiração do token de reset';
COMMENT ON COLUMN master.users.invited_by_user_id IS 'ID do usuário que fez o convite';
COMMENT ON COLUMN master.users.invited_at IS 'Data do convite';
COMMENT ON COLUMN master.users.activated_at IS 'Data de ativação da conta';

-- 4. Atualizar dados existentes
-- Todos os usuários existentes ficam como 'active' e contexto 'establishment'
UPDATE master.users
SET
    status = 'active',
    context_type = 'establishment',
    activated_at = created_at
WHERE status IS NULL OR activated_at IS NULL;

-- 5. Adicionar constraint para garantir consistência
ALTER TABLE master.users
ADD CONSTRAINT users_context_consistency CHECK (
    (context_type = 'company' AND establishment_id IS NULL)
    OR (context_type = 'establishment' AND establishment_id IS NOT NULL)
    OR (context_type = 'client')
);

COMMIT;
