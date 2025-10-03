# Documento da Estrutura de Arquivos do CRUD de Clientes

## Backend

- **app/infrastructure/orm/models.py**: Define o modelo SQLAlchemy `Client` com relacionamentos para `People`, `Establishments` e `Contracts`. Inclui restrições para validação de status e índices únicos para códigos de cliente e combinações pessoa-estabelecimento.
- **app/infrastructure/repositories/client_repository.py**: Repositório abrangente implementando todas as operações CRUD com recursos avançados como geração automática de código de cliente, validação de duplicação e filtragem multi-tenant.
- **app/presentation/schemas/client.py**: Conjunto completo de esquemas Pydantic para operações de cliente incluindo modelos base, parâmetros de lista, DTOs de criação/atualização e respostas de validação. Implementa validadores de campo para formatação de ID fiscal e consistência de tipo de pessoa.
- **app/presentation/api/v1/clients.py**: Router FastAPI com 15+ endpoints cobrindo operações CRUD completas, validação, busca e estatísticas. Implementa segurança multi-tenant com validação de acesso a estabelecimentos e autorização baseada em permissões.

## Frontend

- **frontend/src/services/clientsService.ts**: Classe de serviço TypeScript fornecendo chamadas de API tipadas para todas as operações de cliente. Inclui cache HTTP, lógica de retry e métodos utilitários para formatação e validação de dados.
- **frontend/src/types/api.ts**: Interfaces TypeScript para respostas de API relacionadas a cliente e estruturas de dados.
- **frontend/src/components/views/ClientDetails.tsx**: Componente de visualização detalhada de cliente com interface com abas para informações, contratos e vidas.
- **frontend/src/components/forms/ClientForm.tsx**: Formulário principal de criação/edição de cliente com validação e verificação de duplicação.
- **frontend/src/components/forms/ClientFormSections.tsx**: Seções modulares de formulário para entrada de dados de cliente.
- **frontend/src/components/ui/ClientDataCopyModal.tsx**: Modal para copiar dados de cliente entre formulários.
- **frontend/src/pages/ClientsPage.tsx**: Página principal de listagem de clientes com filtragem avançada, paginação e design responsivo (tabela desktop, cards tablet, cards mobile).
- **frontend/src/pages/ClientsPage_new.tsx**: Implementação alternativa/nova da página de clientes.
- **frontend/src/hooks/useClientForm.ts**: Hook React gerenciando estado de formulário de cliente, validação e lógica de submissão.
- **frontend/src/utils/clientDuplicationLogic.js**: Lógica para lidar com cenários de duplicação de cliente (4 casos diferentes baseados em ID fiscal e estabelecimento).
- **frontend/src/utils/clientCodeGenerator.js**: Utilitários para geração automática de código de cliente e validação.
- **frontend/src/config/tables/contracts.config.tsx**: Configuração para exibir nomes de cliente em tabelas de contratos.

## Tests

- **tests/test_clients_endpoints.py**: Conjunto abrangente de testes cobrindo operações CRUD de cliente, validação e tratamento de erros usando pytest-asyncio.

## Config/Outros

- **database/backup_structure.sql**: Estrutura do banco de dados com esquema de tabela de cliente, restrições e índices adequados.
- **Migrations**: Mudanças relacionadas a cliente em arquivos de migração.
- **Scripts**: Scripts de limpeza e reorganização de cliente no diretório de scripts.

## Visão Geral Arquitetural

O CRUD de Clientes segue um padrão de **Arquitetura Limpa** com clara separação de responsabilidades:

- **Domínio**: Regras de negócio mínimas, confiando em entidades compartilhadas
- **Aplicação**: Uso direto do repositório através da camada de apresentação
- **Infraestrutura**: ORM SQLAlchemy com PostgreSQL, padrão de repositório para acesso a dados
- **Apresentação**: API REST FastAPI com validação Pydantic

**Decisões de Design Chave:**
- **Multi-tenant por Empresa**: Todas as operações de cliente são escopadas por empresa através de relacionamentos de estabelecimento
- **Soft Deletes**: Clientes são soft-deletados para manter integridade referencial
- **Geração Automática de Código**: Códigos de cliente são auto-gerados no formato `{establishment_code}-{sequential}`
- **Prevenção de Duplicação**: Lógica de validação complexa previne clientes duplicados dentro de estabelecimentos
- **Relacionamentos Polimórficos**: Contatos de cliente (telefones, emails, endereços) usam associações polimórficas

## Modelo de Dados

**Entidades Core:**
- `Client`: Liga `People` a `Establishments` com status e código de cliente opcional
- `People`: Armazena dados de pessoa (PF/PJ) com validação de ID fiscal
- `Establishments`: Filiais da empresa onde clientes são registrados
- `Contracts`: Contratos de negócio associados a clientes

**Relacionamentos Chave:**
- Client → Person (many-to-one)
- Client → Establishment (many-to-one) 
- Client → Contracts (one-to-many)
- Restrições únicas: (establishment_id, client_code), (establishment_id, person_id)

## Segurança

**Autenticação & Autorização:**
- Autenticação baseada em JWT necessária para todas as operações
- Controle de acesso baseado em permissões (`clients_view`, `clients_create`, `clients_update`, `clients_delete`)
- Permissões de tipo de contexto escopadas para estabelecimentos

**Isolamento Multi-Tenant:**
- Políticas de Row Level Security (RLS) garantem que usuários acessem apenas clientes de estabelecimentos de sua empresa
- Validação de acesso a estabelecimento em todas as operações
- Queries escopadas por empresa previnem vazamento de dados

**Validação de Entrada:**
- Validação de formato de ID fiscal (CPF/CNPJ)
- Unicidade de código de cliente dentro de estabelecimentos
- Consistência de tipo de pessoa com comprimento de ID fiscal
- Validação de campos obrigatórios com mensagens de erro descritivas

## Regras de Negócio

**Criação de Cliente:**
1. Validação de unicidade de ID fiscal dentro de estabelecimento
2. Geração automática de código de cliente se não fornecido
3. Criação ou reutilização de pessoa baseada em lógica de duplicação
4. Validação de acesso a estabelecimento

**Cenários de Duplicação:**
1. **Mesmo estabelecimento, mesmo ID fiscal**: Bloquear criação
2. **Estabelecimento diferente, mesmo ID fiscal**: Permitir com opção de reutilização de pessoa
3. **Pessoa existe globalmente, nenhum cliente no estabelecimento**: Oferecer reutilização de pessoa
4. **Pessoa existe globalmente, cliente existe em outro lugar**: Mostrar estabelecimentos existentes

**Gerenciamento de Status:**
- Quatro tipos de status: active, inactive, on_hold, archived
- Soft delete define timestamp deleted_at
- Mudanças de status logadas com contexto de usuário

## Performance

**Otimizações de Banco de Dados:**
- Índices compostos em (establishment_id, person_id), (establishment_id, client_code)
- Índices de status e deleted_at para filtragem eficiente
- Queries unidas com selectinload para dados relacionados

**Estratégia de Cache:**
- Cache de resposta HTTP para listas e detalhes de cliente
- Invalidação de cache em operações de criar/atualizar/deletar
- Limpeza de cache baseada em padrão para endpoints relacionados

**Otimização de Query:**
- Queries paginadas com tamanhos de página configuráveis (máx 100)
- Queries filtradas com suporte a múltiplos critérios
- Queries de contagem eficientes para metadados de paginação
- Lazy loading de entidades relacionadas quando apropriado

## Tratamento de Erros

**Respostas de Erro da API:**
- 400: Erros de validação com mensagens detalhadas de campo
- 403: Permissão negada ou violações de acesso a estabelecimento
- 404: Cliente não encontrado
- 422: Erros de validação Pydantic
- 500: Erros internos do servidor com logging estruturado

**Tratamento de Erros no Frontend:**
- Blocos try-catch em torno de todas as chamadas de API
- Notificações de erro amigáveis ao usuário
- Fallbacks graciosos para erros de rede
- Validação de formulário com feedback em tempo real

**Logging:**
- Logging estruturado com contexto (user_id, client_id, operation)
- Rastreamento de erros com stack traces
- Monitoramento de performance para queries lentas

## Integrações

**Sistemas Internos:**
- **Contratos**: Clientes são ligados a contratos de home care
- **Estabelecimentos**: Escopo multi-tenant através de relacionamentos de estabelecimento
- **Pessoas**: Entidade pessoa compartilhada para gerenciamento de contato
- **Usuários**: Controle de acesso baseado em permissões

**Dependências Externas:**
- **PostgreSQL**: Armazenamento primário de dados com recursos avançados
- **Redis**: Camada de cache para otimização de performance
- **JWT**: Gerenciamento de token de autenticação

## Testes

**Cobertura de Testes:**
- Testes unitários para métodos de repositório
- Testes de integração para endpoints de API
- Testes end-to-end para fluxos críticos de usuário
- Suporte a testes assíncronos com pytest-asyncio

**Cenários de Teste:**
- Operações CRUD com dados válidos/inválidos
- Controle de acesso baseado em permissões
- Isolamento de dados multi-tenant
- Tratamento de erros e casos extremos
- Validação de performance

## Monitoramento

**Métricas Rastreadas:**
- Tempos de resposta da API para operações de cliente
- Taxas de erro por endpoint
- Taxas de acerto/erro de cache
- Performance de query de banco de dados

**Eventos de Logging:**
- Criação/atualização/exclusão de cliente com contexto de usuário
- Violações de permissão
- Falhas de validação
- Gargalos de performance

## Análise DBA

**Estrutura da Tabela:**
```sql
CREATE TABLE master.clients (
    id BIGINT PRIMARY KEY,
    person_id BIGINT REFERENCES master.people(id),
    establishment_id BIGINT REFERENCES master.establishments(id),
    client_code VARCHAR(50),
    status VARCHAR(255) CHECK (status IN ('active', 'inactive', 'on_hold', 'archived')),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

**Índices:**
- `clients_establishment_id_index` em establishment_id
- `clients_person_id_index` em person_id
- `clients_status_index` em status
- `clients_deleted_at_index` em deleted_at
- Único: `clients_establishment_id_client_code_unique`
- Único: `clients_establishment_id_person_id_unique`

**Restrições:**
- Restrições de chave estrangeira para people e establishments
- Restrição de verificação de status
- Restrições únicas previnem duplicatas

**Considerações de Performance:**
- Estratégia de particionamento poderia ser implementada para datasets grandes
- Estratégia de arquivamento para clientes inativos antigos
- Manutenção regular de índices e atualizações de estatísticas

**Backup & Recuperação:**
- Clientes incluídos em backups completos do banco de dados
- Capacidade de recuperação point-in-time
- Soft delete permite reconstrução de dados se necessário

## Análise DBA - Estrutura do Banco de Dados

### Tabela Principal: CLIENTS

```sql
CREATE TABLE master.clients (
    id                        BIGINT PRIMARY KEY DEFAULT nextval('clients_id_seq'),
    person_id                 BIGINT NOT NULL REFERENCES people(id),
    establishment_id          BIGINT NOT NULL REFERENCES establishments(id),
    client_code               VARCHAR(50),
    status                    VARCHAR(255) NOT NULL DEFAULT 'active'
                              CHECK (status IN ('active', 'inactive', 'on_hold', 'archived')),
    created_at                TIMESTAMP DEFAULT now(),
    updated_at                TIMESTAMP,
    deleted_at                TIMESTAMP
);
```

### Índices Estratégicos

```sql
-- Índices únicos para regras de negócio
CREATE UNIQUE INDEX clients_establishment_id_person_id_unique
ON clients(establishment_id, person_id) WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX clients_establishment_id_client_code_unique
ON clients(establishment_id, client_code) WHERE deleted_at IS NULL AND client_code IS NOT NULL;

-- Índices de performance
CREATE INDEX clients_establishment_id_index ON clients(establishment_id);
CREATE INDEX clients_person_id_index ON clients(person_id);
CREATE INDEX clients_status_index ON clients(status);
CREATE INDEX clients_deleted_at_index ON clients(deleted_at);
```

### Relacionamentos e Integridade

**Dependências:**
- `person_id` → `people.id` (dados pessoais do cliente)
- `establishment_id` → `establishments.id` (escopo multi-tenant)

**Regras de Unicidade:**
- Uma pessoa pode ser cliente em múltiplos estabelecimentos
- Mas apenas uma vez por estabelecimento
- Códigos de cliente únicos por estabelecimento

### Queries Otimizadas

```sql
-- Query para listagem de clientes com dados completos
SELECT
    c.id,
    c.client_code,
    c.status,
    p.name AS client_name,
    p.trade_name,
    p.tax_id,
    p.person_type,
    e.code AS establishment_code,
    COUNT(contracts.id) AS contracts_count
FROM clients c
JOIN people p ON c.person_id = p.id
JOIN establishments e ON c.establishment_id = e.id
LEFT JOIN contracts ON contracts.client_id = c.id AND contracts.deleted_at IS NULL
WHERE c.deleted_at IS NULL
  AND c.establishment_id = ?
GROUP BY c.id, c.client_code, c.status, p.name, p.trade_name, p.tax_id, p.person_type, e.code
ORDER BY c.created_at DESC;

-- Query para verificação de duplicação
SELECT
    c.id,
    c.establishment_id,
    e.code AS establishment_code,
    p.name,
    p.tax_id
FROM clients c
JOIN people p ON c.person_id = p.id
JOIN establishments e ON c.establishment_id = e.id
WHERE p.tax_id = ?
  AND c.deleted_at IS NULL;
```

### Triggers e Automatizações

```sql
-- Trigger para geração automática de client_code
CREATE OR REPLACE FUNCTION generate_client_code()
RETURNS TRIGGER AS $$
DECLARE
    establishment_code VARCHAR(10);
    next_sequence INTEGER;
    new_code VARCHAR(50);
BEGIN
    IF NEW.client_code IS NULL THEN
        -- Buscar código do estabelecimento
        SELECT code INTO establishment_code
        FROM establishments
        WHERE id = NEW.establishment_id;

        -- Buscar próximo número sequencial
        SELECT COALESCE(MAX(CAST(REGEXP_REPLACE(client_code, '^[A-Z]+-', '') AS INTEGER)), 0) + 1
        INTO next_sequence
        FROM clients
        WHERE establishment_id = NEW.establishment_id
          AND client_code ~ ('^' || establishment_code || '-[0-9]+$');

        -- Gerar novo código
        NEW.client_code := establishment_code || '-' || LPAD(next_sequence::TEXT, 3, '0');
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generate_client_code
    BEFORE INSERT ON clients
    FOR EACH ROW
    EXECUTE FUNCTION generate_client_code();
```

### Estratégias de Performance

#### Particionamento (Para datasets grandes)
```sql
-- Particionamento por establishment_id para isolamento
CREATE TABLE clients_partitioned (
    LIKE clients INCLUDING ALL
) PARTITION BY HASH (establishment_id);

CREATE TABLE clients_part_0 PARTITION OF clients_partitioned
FOR VALUES WITH (modulus 4, remainder 0);

CREATE TABLE clients_part_1 PARTITION OF clients_partitioned
FOR VALUES WITH (modulus 4, remainder 1);
```

#### Arquivamento de Dados
```sql
-- Função para arquivar clientes inativos antigos
CREATE OR REPLACE FUNCTION archive_inactive_clients()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    WITH moved_rows AS (
        DELETE FROM clients
        WHERE status = 'archived'
          AND updated_at < CURRENT_DATE - INTERVAL '5 years'
          AND deleted_at IS NOT NULL
        RETURNING *
    )
    INSERT INTO clients_archive
    SELECT * FROM moved_rows;

    GET DIAGNOSTICS archived_count = ROW_COUNT;
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;
```

### Views Especializadas

```sql
-- View para clientes ativos com informações agregadas
CREATE VIEW vw_active_clients_summary AS
SELECT
    c.id,
    c.client_code,
    p.name AS client_name,
    p.tax_id,
    p.person_type,
    e.code AS establishment_code,
    COUNT(contracts.id) AS active_contracts,
    MAX(contracts.start_date) AS latest_contract_date,
    SUM(contracts.total_value) AS total_contract_value
FROM clients c
JOIN people p ON c.person_id = p.id
JOIN establishments e ON c.establishment_id = e.id
LEFT JOIN contracts ON contracts.client_id = c.id
    AND contracts.status = 'active'
    AND contracts.deleted_at IS NULL
WHERE c.status = 'active'
  AND c.deleted_at IS NULL
GROUP BY c.id, c.client_code, p.name, p.tax_id, p.person_type, e.code;

-- View para detecção de duplicatas potenciais
CREATE VIEW vw_potential_duplicate_clients AS
SELECT
    p.tax_id,
    p.name,
    COUNT(*) AS occurrences,
    STRING_AGG(e.code || ':' || c.client_code, ', ') AS locations
FROM clients c
JOIN people p ON c.person_id = p.id
JOIN establishments e ON c.establishment_id = e.id
WHERE c.deleted_at IS NULL
GROUP BY p.tax_id, p.name
HAVING COUNT(*) > 1;
```

### Monitoramento e Métricas

```sql
-- Função para estatísticas de clientes
CREATE OR REPLACE FUNCTION get_client_statistics(establishment_id_param BIGINT DEFAULT NULL)
RETURNS TABLE(
    total_clients INTEGER,
    active_clients INTEGER,
    clients_with_contracts INTEGER,
    avg_contracts_per_client NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER AS total_clients,
        COUNT(CASE WHEN c.status = 'active' THEN 1 END)::INTEGER AS active_clients,
        COUNT(CASE WHEN contracts_count > 0 THEN 1 END)::INTEGER AS clients_with_contracts,
        ROUND(AVG(contracts_count), 2) AS avg_contracts_per_client
    FROM (
        SELECT
            c.id,
            c.status,
            COUNT(contracts.id) AS contracts_count
        FROM clients c
        LEFT JOIN contracts ON contracts.client_id = c.id AND contracts.deleted_at IS NULL
        WHERE c.deleted_at IS NULL
          AND (establishment_id_param IS NULL OR c.establishment_id = establishment_id_param)
        GROUP BY c.id, c.status
    ) client_data;
END;
$$ LANGUAGE plpgsql;
```

### Compliance LGPD

```sql
-- Função para anonização de dados de cliente
CREATE OR REPLACE FUNCTION anonymize_client_data(client_id_param BIGINT)
RETURNS VOID AS $$
BEGIN
    -- Anonizar dados na tabela people
    UPDATE people
    SET
        name = 'Cliente Anonimizado #' || client_id_param,
        tax_id = REGEXP_REPLACE(tax_id, '.', '*'),
        birth_date = NULL,
        occupation = '[ANONIMIZADO]'
    WHERE id = (SELECT person_id FROM clients WHERE id = client_id_param);

    -- Anonizar endereços
    UPDATE addresses
    SET
        street = '[ANONIMIZADO]',
        number = '***',
        details = '[ANONIMIZADO]'
    WHERE addressable_type = 'App\\Models\\People'
      AND addressable_id = (SELECT person_id FROM clients WHERE id = client_id_param);

    -- Log da anonização
    INSERT INTO audit_log (table_name, record_id, action, performed_at)
    VALUES ('clients', client_id_param, 'ANONYMIZE', now());
END;
$$ LANGUAGE plpgsql;
```

Esta implementação abrangente fornece uma base robusta, escalável e segura para gerenciamento de cliente dentro do sistema Pro Team Care.

## Estrutura em Formato de Árvore

```
.
├── Backend
│   ├── app/infrastructure/orm/models.py
│   ├── app/infrastructure/repositories/client_repository.py
│   ├── app/presentation/schemas/client.py
│   └── app/presentation/api/v1/clients.py
├── Frontend
│   ├── frontend/src/services/clientsService.ts
│   ├── frontend/src/types/api.ts
│   ├── frontend/src/components/views/ClientDetails.tsx
│   ├── frontend/src/components/forms/ClientForm.tsx
│   ├── frontend/src/components/forms/ClientFormSections.tsx
│   ├── frontend/src/components/ui/ClientDataCopyModal.tsx
│   ├── frontend/src/pages/ClientsPage.tsx
│   ├── frontend/src/pages/ClientsPage_new.tsx
│   ├── frontend/src/hooks/useClientForm.ts
│   ├── frontend/src/utils/clientDuplicationLogic.js
│   ├── frontend/src/utils/clientCodeGenerator.js
│   └── frontend/src/config/tables/contracts.config.tsx
├── Tests
│   └── tests/test_clients_endpoints.py
├── Config/Outros
│   ├── database/backup_structure.sql
│   ├── migrations/
│   └── scripts/
```