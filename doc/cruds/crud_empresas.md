# Documento da Estrutura de Arquivos do CRUD de Empresas

## Backend

- **app/domain/entities/company.py**: Define entidades puras do domínio (CompanyEntity, PeopleEntity, PhoneEntity, EmailEntity, AddressEntity) com métodos de lógica de negócio como validação e verificações de status
- **app/application/dto/company_dto.py**: Objetos de Transferência de Dados para operações de empresa (CreateCompanyCommand, UpdateCompanyCommand, CompanyQueryParams) para lidar com comandos de lógica de negócio
- **app/application/use_cases/create_company_use_case.py**: Caso de uso para criar empresas com validação e enriquecimento
- **app/application/use_cases/get_company_use_case.py**: Caso de uso para recuperar detalhes da empresa
- **app/application/use_cases/update_company_use_case.py**: Caso de uso para atualizar dados da empresa com regras de negócio
- **app/application/use_cases/delete_company_use_case.py**: Caso de uso para soft-delete de empresas (mudança de status)
- **app/infrastructure/orm/models.py**: Modelos ORM SQLAlchemy para tabelas Company, People, Phone, Email, Address com relacionamentos e restrições
- **app/infrastructure/repositories/company_repository.py**: Repositório principal implementando operações CRUD com enriquecimento de endereço, validação de contato e gerenciamento de transações
- **app/infrastructure/repositories/company_repository_filtered.py**: Repositório filtrado com capacidades de auto-filtragem para consultas avançadas
- **app/presentation/schemas/company.py**: Esquemas Pydantic para validação de requisição/resposta da API (CompanyCreate, CompanyUpdate, CompanyDetailed, CompanyList)
- **app/presentation/schemas/company_legacy.py**: Esquemas Pydantic legados para compatibilidade retroativa
- **app/presentation/api/v1/companies.py**: Router FastAPI com endpoints CRUD, decoradores de permissão e tratamento de erros
- **app/presentation/decorators/simple_permissions.py**: Decoradores de permissão (require_companies_view, require_companies_create) para controle de acesso

## Frontend

- **frontend/src/types/company.types.ts**: Interfaces TypeScript para entidades Company (Company, CompanyDetailed, CompanyCreate, CompanyUpdate)
- **frontend/src/types/api.ts**: Tipos de resposta da API incluindo interfaces Company e filtros
- **frontend/src/types/enums.ts**: Enum CompanyStatus e rótulos de status
- **frontend/src/types/components.ts**: Tipos de props de componentes para formulários de empresa e tabelas de dados
- **frontend/src/services/companiesService.ts**: Classe de serviço da API para operações CRUD de empresa com cache HTTP e tratamento de erros
- **frontend/src/hooks/useCompanyForm.ts**: Hook React para gerenciar estado de formulário de empresa, validação e submissão
- **frontend/src/hooks/useCompaniesDataTable.ts**: Hook para tabela de dados de empresa com paginação, filtragem e métricas
- **frontend/src/components/forms/CompanyForm.tsx**: Componente principal de formulário de empresa com seções
- **frontend/src/components/forms/CompanyFormSections/CompanyBasicDataSection.tsx**: Seção de formulário para entrada de dados básicos da empresa
- **frontend/src/components/forms/CompanyFormSections/CompanyReceitaFederalSection.tsx**: Seção de formulário para integração CNPJ da Receita Federal
- **frontend/src/components/views/CompanyDetailsNew.tsx**: Componente para exibir informações detalhadas da empresa
- **frontend/src/components/search/CompanySearchInput.jsx**: Componente de entrada de busca para encontrar empresas
- **frontend/src/components/search/CompanySearchModal.jsx**: Modal para busca avançada de empresa
- **frontend/src/components/entities/CompanyBasicInfo.jsx**: Componente para exibir informações básicas da empresa
- **frontend/src/pages/CompaniesPage.tsx**: Componente de página principal roteando entre lista de empresas e visualizações de detalhes
- **frontend/src/config/tables/companies.config.tsx**: Configuração de tabela de dados com colunas, ações e métricas para empresas
- **frontend/src/utils/companyDataMapper.ts**: Funções utilitárias para mapear dados de empresa para formulários de estabelecimento
- **frontend/src/utils/statusUtils.ts**: Funções utilitárias para tratamento e exibição de status de empresa

## Tests

- **tests/test_companies.py**: Testes unitários para lógica de domínio de empresa e operações de repositório
- **tests/test_companies_endpoints.py**: Testes de integração para endpoints da API de empresa (CRUD, validação, permissões)
- **tests/test_companies_integration.py**: Testes de integração end-to-end para fluxos de negócio de empresa

## Config

- **config/settings.py**: Configuração da aplicação incluindo configurações de banco de dados e variáveis de ambiente

## Migrations

- **migrations/005_add_company_id_to_contacts.sql**: Migração SQL para adicionar chaves estrangeiras company_id às tabelas de contato (phones, emails, addresses)
- **alembic/versions/f6c3a4d2e4dc_allow_null_company_person_ids.py**: Migração Alembic para permitir IDs de pessoa da empresa nulos

## Scripts

- **scripts/audit_company_address.py**: Script para auditar e validar dados de endereço de empresa
- **check_company_users.py**: Script para verificar e validar relacionamentos empresa-usuário

## Visão Geral Arquitetural

O CRUD de Empresas segue a arquitetura limpa (Clean Architecture), dividida em camadas:
- **Domínio**: Entidades puras com lógica de negócio (validações, status).
- **Aplicação**: Casos de uso para operações CRUD, DTOs para transferência de dados.
- **Infraestrutura**: Repositórios para acesso a dados, ORM SQLAlchemy com relacionamentos.
- **Apresentação**: APIs FastAPI com esquemas Pydantic, decoradores de permissões.

Fluxo de dados: Requisição → Validação (Pydantic) → Caso de Uso → Repositório → BD. Integra com multi-tenancy via isolamento por empresa.

## Modelo de Dados

Entidades principais:
- **Company**: Dados básicos (nome, CNPJ, status).
- **People**: Responsáveis associados.
- **Address**: Endereços vinculados.
- **Phone/Email**: Contatos.

Relacionamentos: Company 1:N People, Company 1:N Address, etc. Suporte a multi-tenancy com company_id em tabelas relacionadas.

## Segurança e Isolamento

- **Isolamento via Contexto de Tenant**: Configuração de sessão PostgreSQL para isolamento por empresa (possivelmente via RLS).
- **Permissões Granulares**: Decoradores (require_companies_view, require_companies_create) baseados em roles.
- **Autenticação**: JWT com validação de tenant.
- **Validação de Entrada**: Pydantic previne injeções; sanitização de dados.

## Regras de Negócio

- **Criação**: CNPJ único por tenant; enriquecimento automático via Receita Federal.
- **Atualização**: Apenas campos permitidos; validação de status (ativo/inativo).
- **Exclusão**: Soft-delete (status = 'deleted'); preserva integridade referencial.
- **Validações**: CNPJ válido, endereços obrigatórios, contatos únicos.

## Performance e Escalabilidade

- **Cache**: Redis para queries frequentes; HTTP cache no frontend.
- **Indexação**: Índices em company_id, CNPJ, status.
- **Paginação**: Suporte a paginação server-side para listas grandes.
- **Otimização**: Queries N+1 evitadas via joins; async/await para I/O.

## Tratamento de Erros e Validação

- **Exceções Customizadas**: BusinessException, ValidationException, NotFoundException.
- **Logging**: Structlog em JSON para rastreamento.
- **Respostas API**: Códigos HTTP padronizados (400 para validação, 404 para não encontrado).
- **Frontend**: Tratamento de erros em hooks/services com feedback ao usuário.

## Integrações e APIs

- **Princípios RESTful**: Endpoints /companies com métodos GET/POST/PUT/DELETE.
- **Versionamento**: API v1 com compatibilidade legado.
- **Rate Limiting**: Básico no login; expansível.
- **Integrações**: Receita Federal para CNPJ; mapeamento para estabelecimentos/contratos.

## Testes e Qualidade

- **Cobertura**: pytest com --cov; mínimo 80%.
- **Tipos**: Unitários (domínio), integração (endpoints), e2e (fluxos completos).
- **Automação**: CI/CD com pre-commit hooks (black, flake8, mypy).

## Monitoramento e Observabilidade

- **Logs**: Estruturados com níveis (info, error); centralizados via ELK stack.
- **Métricas**: Tempo de resposta, taxa de erro por endpoint.
- **Alertas**: Monitoramento de falhas em criação/atualização.
- **Tracing**: OpenTelemetry para requests distribuídos.

## Decisões de Design

- **Soft-Delete**: Preserva dados históricos vs. hard-delete para simplicidade.
- **DTOs**: Separação entre domínio e apresentação para flexibilidade.
- **Multi-Tenant**: Isolamento via contexto de tenant para segurança, trade-off em performance de queries.
- **Frontend Hooks**: Gerenciamento de estado local vs. global para reusabilidade.

## Análise DBA - Estrutura do Banco de Dados

### Tabelas Principais e Relacionamentos

#### 1. **COMPANIES** (Tabela Central)
```sql
CREATE TABLE master.companies (
    id                        BIGINT PRIMARY KEY DEFAULT nextval('companies_id_seq'),
    person_id                 BIGINT UNIQUE REFERENCES people(id),
    settings                  JSONB,
    metadata                  JSONB,
    created_at                TIMESTAMP DEFAULT now(),
    updated_at                TIMESTAMP,
    deleted_at                TIMESTAMP,
    display_order             INTEGER NOT NULL DEFAULT 0
);
```

**Características:**
- Relacionamento 1:1 com `people` via `person_id` (UNIQUE)
- Soft-delete via `deleted_at`
- Configurações flexíveis em `settings` (JSONB)
- Metadados extensíveis em `metadata` (JSONB)
- Índices full-text search em JSONB fields

#### 2. **PEOPLE** (Dados Pessoais/Empresariais)
```sql
CREATE TABLE master.people (
    id                        BIGINT PRIMARY KEY,
    person_type               VARCHAR(255) NOT NULL,     -- 'PF' ou 'PJ'
    name                      VARCHAR(200) NOT NULL,      -- Razão Social
    trade_name                VARCHAR(200),               -- Nome Fantasia
    tax_id                    VARCHAR(14) NOT NULL,       -- CNPJ/CPF
    secondary_tax_id          VARCHAR(20),                -- IE/RG
    birth_date                DATE,
    incorporation_date        DATE,                       -- Data de Fundação
    tax_regime                VARCHAR(50),                -- Regime Tributário
    legal_nature              VARCHAR(100),               -- Natureza Jurídica
    municipal_registration    VARCHAR(20),                -- Inscrição Municipal
    status                    VARCHAR(255) DEFAULT 'active',
    company_id                INTEGER,                    -- Multi-tenancy
    -- Campos LGPD
    lgpd_consent_version      VARCHAR(10),
    lgpd_consent_given_at     TIMESTAMP,
    lgpd_data_retention_expires_at TIMESTAMP,
    -- Auditoria
    created_at                TIMESTAMP DEFAULT now(),
    updated_at                TIMESTAMP,
    deleted_at                TIMESTAMP
);
```

**Características:**
- Suporte tanto PF quanto PJ
- CNPJ único por tenant (`company_tax_id_unique`)
- Compliance LGPD built-in
- Multi-tenancy via `company_id`

#### 3. **ESTABLISHMENTS** (Filiais/Unidades)
```sql
CREATE TABLE master.establishments (
    id                        BIGINT PRIMARY KEY,
    person_id                 BIGINT UNIQUE REFERENCES people(id),
    company_id                BIGINT NOT NULL,
    code                      VARCHAR(50) NOT NULL,       -- Código único por empresa
    type                      VARCHAR(255) DEFAULT 'filial',
    category                  VARCHAR(100),
    is_active                 BOOLEAN DEFAULT true,
    is_principal              BOOLEAN DEFAULT false,      -- Matriz/Filial
    settings                  JSONB,
    operating_hours           JSONB,                      -- Horários de funcionamento
    service_areas             JSONB,                      -- Áreas de atendimento
    display_order             INTEGER DEFAULT 0,
    metadata                  JSONB
);
```

**Características:**
- Código único por company (`company_id_code_unique`)
- Hierarquia matriz/filial via `is_principal`
- Configurações operacionais em JSONB
- Índices otimizados para consultas ativas

#### 4. **ADDRESSES** (Endereços Polimórficos)
```sql
CREATE TABLE master.addresses (
    id                        BIGINT PRIMARY KEY,
    addressable_type          VARCHAR(255) NOT NULL,     -- 'App\Models\People'
    addressable_id            BIGINT NOT NULL,           -- ID da entidade
    type                      VARCHAR(255) DEFAULT 'residential',
    -- Dados básicos
    street                    VARCHAR(255) NOT NULL,
    number                    VARCHAR(20),
    details                   VARCHAR(255),              -- Complemento
    neighborhood              VARCHAR(255) NOT NULL,
    city                      VARCHAR(255) NOT NULL,
    state                     VARCHAR(2) NOT NULL,
    zip_code                  VARCHAR(10) NOT NULL,
    country                   VARCHAR(2) DEFAULT 'BR',
    -- Geolocalização
    latitude                  NUMERIC(10,8),
    longitude                 NUMERIC(11,8),
    geocoding_accuracy        VARCHAR(255),
    geocoding_source          VARCHAR(255),
    google_place_id           VARCHAR(255),
    formatted_address         TEXT,
    -- Dados IBGE
    ibge_city_code            INTEGER,
    ibge_state_code           INTEGER,
    region                    VARCHAR(255),
    microregion               VARCHAR(255),
    mesoregion                VARCHAR(255),
    -- Dados auxiliares
    area_code                 VARCHAR(255),
    gia_code                  VARCHAR(255),
    siafi_code                VARCHAR(255),
    -- Validação e qualidade
    quality_score             INTEGER,
    is_validated              BOOLEAN DEFAULT false,
    last_validated_at         TIMESTAMP,
    validation_source         VARCHAR(255),
    api_data                  JSONB,                     -- Dados da API externa
    -- Contexto home care
    within_coverage           BOOLEAN,
    distance_to_establishment INTEGER,                    -- Metros
    estimated_travel_time     INTEGER,                    -- Minutos
    access_difficulty         VARCHAR(255),
    access_notes              TEXT,
    -- Multi-tenancy
    company_id                BIGINT REFERENCES companies(id)
);
```

**Características:**
- Polimórfico (`addressable_type` + `addressable_id`)
- Enriquecimento automático com APIs externas
- Suporte completo a geolocalização
- Dados IBGE integrados
- Métricas para home care (distância, tempo)
- Controle de qualidade e validação

#### 5. **PHONES** (Telefones com WhatsApp)
```sql
CREATE TABLE master.phones (
    id                        BIGINT PRIMARY KEY,
    phoneable_type            VARCHAR(255) NOT NULL,
    phoneable_id              BIGINT NOT NULL,
    type                      VARCHAR(255) DEFAULT 'mobile',
    country_code              VARCHAR(3) DEFAULT '55',
    number                    VARCHAR(11) NOT NULL,
    extension                 VARCHAR(10),
    -- WhatsApp features
    is_whatsapp               BOOLEAN DEFAULT false,
    whatsapp_formatted        VARCHAR(15),
    whatsapp_verified         BOOLEAN DEFAULT false,
    whatsapp_verified_at      TIMESTAMP,
    whatsapp_business         BOOLEAN DEFAULT false,
    whatsapp_name             VARCHAR(100),
    accepts_whatsapp_marketing BOOLEAN DEFAULT false,
    accepts_whatsapp_notifications BOOLEAN DEFAULT true,
    whatsapp_preferred_time_start TIME DEFAULT '08:00:00',
    whatsapp_preferred_time_end TIME DEFAULT '18:00:00',
    -- Dados da operadora
    carrier                   VARCHAR(30),
    line_type                 VARCHAR(255),
    -- Controle de contato
    contact_priority          INTEGER DEFAULT 1,
    last_contact_attempt      TIMESTAMP,
    last_contact_success      TIMESTAMP,
    contact_attempts_count    INTEGER DEFAULT 0,
    -- Multi-tenancy
    company_id                BIGINT REFERENCES companies(id)
);
```

**Características:**
- Suporte completo ao WhatsApp Business
- Controle de preferências de contato
- Tracking de tentativas de contato
- Validação de operadora

#### 6. **EMAILS** (E-mails)
```sql
CREATE TABLE master.emails (
    id                        BIGINT PRIMARY KEY,
    emailable_type            VARCHAR(255) NOT NULL,
    emailable_id              BIGINT NOT NULL,
    type                      VARCHAR(255) DEFAULT 'work',
    email_address             VARCHAR(255) NOT NULL,
    is_principal              BOOLEAN DEFAULT false,
    is_active                 BOOLEAN DEFAULT true,
    verified_at               TIMESTAMP,
    company_id                BIGINT REFERENCES companies(id)
);
```

#### 7. **COMPANY_SETTINGS** (Configurações por Empresa)
```sql
CREATE TABLE master.company_settings (
    id                        BIGINT NOT NULL,
    company_id                BIGINT NOT NULL REFERENCES companies(id),
    setting_key               VARCHAR(100) NOT NULL,
    setting_category          VARCHAR(50) NOT NULL,
    setting_value             JSONB,
    updated_by_user_id        BIGINT REFERENCES users(id),
    UNIQUE(company_id, setting_key)
);
```

### Índices e Performance

#### Índices Estratégicos:
- **Full-text search**: JSONB fields com GIN indexes
- **Geolocalização**: Coordenadas com índices espaciais
- **Multi-tenancy**: `company_id` indexes em todas as tabelas
- **Soft-delete**: `deleted_at` indexes para filtros
- **Polimórficos**: Composite indexes (`type`, `id`)

#### Views Especializadas:
- `vw_addresses_with_geolocation`: Endereços enriquecidos com dados geográficos

### Estratégias de Isolamento (Multi-tenancy)

1. **Nível de Linha**: `company_id` em tabelas de contato
2. **Contexto de Sessão**: PostgreSQL search_path configurável
3. **Índices Parciais**: `WHERE company_id = ? AND deleted_at IS NULL`

### Compliance e Auditoria

- **LGPD**: Campos específicos para consentimento e retenção
- **Soft-delete**: Preservação de dados históricos
- **Timestamps**: Criação/atualização em todas as tabelas
- **User tracking**: `created_by_user_id`, `updated_by_user_id`

### Integrações Externas

- **ViaCEP**: Enriquecimento de endereços
- **ReceitaWS**: Validação de CNPJ
- **Google Places**: Geolocalização precisa
- **IBGE**: Dados demográficos e administrativos

### Exemplo de Consulta Otimizada

```sql
-- Buscar empresa com todos os dados relacionados
SELECT
    c.id,
    p.name,
    p.trade_name,
    p.tax_id,
    COUNT(e.id) as establishments_count,
    COUNT(DISTINCT a.id) as addresses_count,
    COUNT(DISTINCT ph.id) as phones_count,
    COUNT(DISTINCT em.id) as emails_count
FROM companies c
JOIN people p ON c.person_id = p.id
LEFT JOIN establishments e ON e.company_id = c.id AND e.deleted_at IS NULL
LEFT JOIN addresses a ON a.addressable_type = 'App\\Models\\People' AND a.addressable_id = p.id AND a.deleted_at IS NULL
LEFT JOIN phones ph ON ph.phoneable_type = 'App\\Models\\People' AND ph.phoneable_id = p.id AND ph.deleted_at IS NULL
LEFT JOIN emails em ON em.emailable_type = 'App\\Models\\People' AND em.emailable_id = p.id AND em.deleted_at IS NULL
WHERE c.deleted_at IS NULL
  AND p.company_id = ?
GROUP BY c.id, p.name, p.trade_name, p.tax_id
ORDER BY p.name;
```

## Estrutura em Formato de Árvore

```
.
├── Backend
│   ├── app/domain/entities/company.py
│   ├── app/application/dto/company_dto.py
│   ├── app/application/use_cases/create_company_use_case.py
│   ├── app/application/use_cases/get_company_use_case.py
│   ├── app/application/use_cases/update_company_use_case.py
│   ├── app/application/use_cases/delete_company_use_case.py
│   ├── app/infrastructure/orm/models.py
│   ├── app/infrastructure/repositories/company_repository.py
│   ├── app/infrastructure/repositories/company_repository_filtered.py
│   ├── app/presentation/schemas/company.py
│   ├── app/presentation/schemas/company_legacy.py
│   ├── app/presentation/api/v1/companies.py
│   └── app/presentation/decorators/simple_permissions.py
├── Frontend
│   ├── frontend/src/types/company.types.ts
│   ├── frontend/src/types/api.ts
│   ├── frontend/src/types/enums.ts
│   ├── frontend/src/types/components.ts
│   ├── frontend/src/services/companiesService.ts
│   ├── frontend/src/hooks/useCompanyForm.ts
│   ├── frontend/src/hooks/useCompaniesDataTable.ts
│   ├── frontend/src/components/forms/CompanyForm.tsx
│   ├── frontend/src/components/forms/CompanyFormSections/CompanyBasicDataSection.tsx
│   ├── frontend/src/components/forms/CompanyFormSections/CompanyReceitaFederalSection.tsx
│   ├── frontend/src/components/views/CompanyDetailsNew.tsx
│   ├── frontend/src/components/search/CompanySearchInput.jsx
│   ├── frontend/src/components/search/CompanySearchModal.jsx
│   ├── frontend/src/components/entities/CompanyBasicInfo.jsx
│   ├── frontend/src/pages/CompaniesPage.tsx
│   ├── frontend/src/config/tables/companies.config.tsx
│   ├── frontend/src/utils/companyDataMapper.ts
│   └── frontend/src/utils/statusUtils.ts
├── Tests
│   ├── tests/test_companies.py
│   ├── tests/test_companies_endpoints.py
│   └── tests/test_companies_integration.py
├── Config
│   └── config/settings.py
├── Migrations
│   ├── migrations/005_add_company_id_to_contacts.sql
│   └── alembic/versions/f6c3a4d2e4dc_allow_null_company_person_ids.py
└── Scripts
    ├── scripts/audit_company_address.py
    └── scripts/check_company_users.py
```