-- MIGRAÇÃO: Adicionar company_id às tabelas de contatos
-- Data: 2025-09-14
-- Descrição: Durante a migração multi-tenant, adicionamos company_id aos modelos Python
--           mas não criamos a migração SQL correspondente. Isso está causando erro 500
--           no endpoint /api/v1/companies/56 porque o SQLAlchemy tenta buscar colunas
--           que não existem no banco.

-- ====================================================================
-- PASSO 1: Adicionar colunas company_id
-- ====================================================================

-- Adicionar company_id na tabela phones
ALTER TABLE master.phones
ADD COLUMN company_id BIGINT REFERENCES master.companies(id);

-- Adicionar company_id na tabela emails
ALTER TABLE master.emails
ADD COLUMN company_id BIGINT REFERENCES master.companies(id);

-- Adicionar company_id na tabela addresses
ALTER TABLE master.addresses
ADD COLUMN company_id BIGINT REFERENCES master.companies(id);

-- ====================================================================
-- PASSO 2: Popular company_id com base nos relacionamentos existentes
-- ====================================================================

-- Popular phones.company_id
-- Phones são ligados a people via phoneable_id, e people são ligados a companies
UPDATE master.phones
SET company_id = (
    SELECT c.id
    FROM master.companies c
    WHERE c.person_id = phones.phoneable_id
    AND phones.phoneable_type = 'People'
)
WHERE phones.phoneable_type = 'People'
AND phones.phoneable_id IN (SELECT person_id FROM master.companies);

-- Popular emails.company_id
UPDATE master.emails
SET company_id = (
    SELECT c.id
    FROM master.companies c
    WHERE c.person_id = emails.emailable_id
    AND emails.emailable_type = 'People'
)
WHERE emails.emailable_type = 'People'
AND emails.emailable_id IN (SELECT person_id FROM master.companies);

-- Popular addresses.company_id
UPDATE master.addresses
SET company_id = (
    SELECT c.id
    FROM master.companies c
    WHERE c.person_id = addresses.addressable_id
    AND addresses.addressable_type = 'People'
)
WHERE addresses.addressable_type = 'People'
AND addresses.addressable_id IN (SELECT person_id FROM master.companies);

-- ====================================================================
-- PASSO 3: Criar índices para performance
-- ====================================================================

-- Índices company_id para performance multi-tenant
CREATE INDEX phones_company_id_idx ON master.phones(company_id) WHERE company_id IS NOT NULL;
CREATE INDEX emails_company_id_idx ON master.emails(company_id) WHERE company_id IS NOT NULL;
CREATE INDEX addresses_company_id_idx ON master.addresses(company_id) WHERE company_id IS NOT NULL;

-- ====================================================================
-- PASSO 4: Verificação dos resultados
-- ====================================================================

-- Verificar quantos registros foram atualizados
DO $$
BEGIN
    RAISE NOTICE 'RESULTADOS DA MIGRAÇÃO:';
    RAISE NOTICE 'Phones com company_id: %', (SELECT COUNT(*) FROM master.phones WHERE company_id IS NOT NULL);
    RAISE NOTICE 'Emails com company_id: %', (SELECT COUNT(*) FROM master.emails WHERE company_id IS NOT NULL);
    RAISE NOTICE 'Addresses com company_id: %', (SELECT COUNT(*) FROM master.addresses WHERE company_id IS NOT NULL);

    RAISE NOTICE 'Phones sem company_id: %', (SELECT COUNT(*) FROM master.phones WHERE company_id IS NULL);
    RAISE NOTICE 'Emails sem company_id: %', (SELECT COUNT(*) FROM master.emails WHERE company_id IS NULL);
    RAISE NOTICE 'Addresses sem company_id: %', (SELECT COUNT(*) FROM master.addresses WHERE company_id IS NULL);
END $$;
