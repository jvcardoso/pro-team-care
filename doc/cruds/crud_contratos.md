# Documento da Estrutura de Arquivos do CRUD de Contratos

## Backend

- **app/infrastructure/orm/models.py**: Define os modelos SQLAlchemy para `Contract`, `ContractLife`, `ContractService` com relacionamentos complexos e restrições. Inclui validação de status e soft delete.
- **app/infrastructure/repositories/contract_repository.py**: Repositório abrangente implementando operações CRUD com queries complexas para vidas de contrato, serviços e validações de negócio.
- **app/presentation/schemas/contract.py**: Esquemas Pydantic completos para criação/atualização de contratos, vidas e serviços. Inclui validações de datas, valores e relacionamentos.
- **app/presentation/api/v1/contracts.py**: Router FastAPI com 20+ endpoints para operações CRUD completas, gerenciamento de vidas, serviços e estatísticas. Inclui decoradores de permissão e validação multi-tenant.
- **app/presentation/decorators/simple_permissions.py**: Decoradores para controle de acesso baseado em permissões (`require_contracts_view`, `require_contracts_create`).
- **app/infrastructure/services/contract_dashboard_service.py**: Serviço para métricas de dashboard, agregando dados de contratos para relatórios.
- **app/infrastructure/services/system_optimization_service.py**: Serviço que valida contratos e inclui em verificações de saúde do sistema.

## Frontend

- **frontend/src/pages/ContractsPage.tsx**: Página principal de contratos com listagem, filtros avançados, paginação e design responsivo (tabela desktop, cards tablet/mobile).
- **frontend/src/components/forms/ContractForm.tsx**: Formulário complexo de criação/edição de contratos com seções para dados básicos, vidas e serviços.
- **frontend/src/components/forms/ContractFormSections.tsx**: Seções modulares do formulário para entrada organizada de dados.
- **frontend/src/components/views/ContractDetails.tsx**: Visualização detalhada de contrato com abas para informações, vidas, serviços e histórico.
- **frontend/src/components/search/ContractSearchModal.jsx**: Modal de busca avançada para contratos.
- **frontend/src/config/tables/contracts.config.tsx**: Configuração de tabela de dados com colunas, ações e métricas para contratos.
- **frontend/src/services/contractsService.ts**: Serviço TypeScript para operações CRUD de contratos com cache HTTP e tratamento de erros.
- **frontend/src/hooks/useDataTable.ts**: Hook genérico para tabelas de dados com métricas específicas de contratos (contratos ativos, expirando, receita total).
- **frontend/src/utils/contractCalculations.js**: Utilitários para cálculos de valores, datas e validações de contrato.

## Tests

- **tests/test_contracts_crud.py**: Testes abrangentes de operações CRUD de contratos.
- **tests/test_home_care_business_rules.py**: Testes de regras de negócio para contratos de home care.
- **tests/test_home_care_integration.py**: Testes de integração end-to-end para fluxos de contrato.

## Config/Outros

- **migrations/008_create_contract_tables.py**: Migração criando tabelas de contrato, vidas e serviços com restrições e índices.
- **scripts/create_contract_menus_complete.py**: Script para criar menus completos de contrato.
- **scripts/create_contract_menus_simple.py**: Script simplificado para criação de menus.
- **scripts/create_contract_menus.py**: Script básico para menus de contrato.
- **scripts/create_contract_views.py**: Script para criar views de banco para relatórios de contrato.
- **scripts/add_contract_permissions.py**: Script para adicionar permissões granulares de contrato.

## Visão Geral Arquitetural

**Padrão Arquitetural Limpa:**
- **Camada de Domínio**: Esquemas Pydantic definem entidades e regras de validação
- **Camada de Aplicação**: Repositório implementa lógica de negócio e acesso a dados
- **Camada de Infraestrutura**: Modelos SQLAlchemy e operações de banco de dados
- **Camada de Apresentação**: Routers FastAPI com esquemas Pydantic e decoradores de segurança

**Arquitetura Multi-Tenant:**
- Contratos escopados por empresa através de relacionamentos
- Isolamento via Row Level Security (RLS)
- Validação de acesso a estabelecimento em todas as operações

**Fluxo de Dados:**
1. Componentes frontend disparam chamadas de API via camada de serviço
2. Routers FastAPI validam requisições e aplicam permissões
3. Repositório executa lógica de negócio e operações de banco
4. Respostas são serializadas através de esquemas Pydantic

## Modelo de Dados

**Entidades Core:**
- `Contract`: Contrato principal com dados básicos (cliente, estabelecimento, valores, datas)
- `ContractLife`: Vidas do contrato com períodos de cobertura e limites
- `ContractService`: Serviços associados ao contrato com preços e autorizações

**Relacionamentos Complexos:**
- Contract → Client (many-to-one)
- Contract → Establishment (many-to-one)
- Contract → ContractLife (one-to-many)
- Contract → ContractService (one-to-many)
- ContractLife → ContractService (many-to-many através de autorizações)

**Estrutura da Tabela `contracts`:**
```sql
CREATE TABLE master.contracts (
    id BIGINT PRIMARY KEY,
    client_id BIGINT REFERENCES master.clients(id),
    establishment_id BIGINT REFERENCES master.establishments(id),
    contract_number VARCHAR(50) UNIQUE,
    status VARCHAR(255) CHECK (status IN ('draft', 'active', 'suspended', 'cancelled', 'expired')),
    contract_type VARCHAR(50),
    start_date DATE NOT NULL,
    end_date DATE,
    total_value DECIMAL(15,2),
    monthly_value DECIMAL(15,2),
    settings JSONB,
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

## Segurança

**Sistema de Permissões:**
- Permissões baseadas em contexto: system/company/establishment
- Controle de acesso baseado em nível com papéis hierárquicos
- Isolamento multi-tenant impedindo acesso cross-company

**Autenticação & Autorização:**
- Autenticação JWT necessária para todas as operações
- Decoradores de permissão nos endpoints da API
- Filtragem automática de empresa para usuários não-admin

**Validação de Entrada:**
- Esquemas Pydantic com validação rigorosa de campo
- Restrições de banco de dados e verificações
- Validação de regras de negócio na camada de repositório

## Regras de Negócio

**Criação de Contrato:**
- Número de contrato único por estabelecimento
- Validação de datas (start_date ≤ end_date)
- Cálculo automático de valores mensais
- Verificação de cliente ativo e estabelecimento válido

**Gerenciamento de Vidas:**
- Vidas sequenciais sem sobreposição de datas
- Limites de cobertura por vida
- Status independente por vida
- Renovação automática opcional

**Gerenciamento de Serviços:**
- Serviços associados a vidas específicas
- Controle de autorizações por serviço
- Preços específicos por contrato/serviço
- Validação de compatibilidade de serviços

**Regras Multi-Tenant:**
- Contratos visíveis apenas para usuários da empresa
- Validação de estabelecimento no escopo da empresa
- Isolamento completo entre empresas

## Performance

**Otimização de Banco de Dados:**
- Índices compostos em (establishment_id, status), (client_id, status)
- Índices parciais excluindo registros deletados
- GIN indexes em campos JSONB (metadata, settings)
- Queries eficientes com joinedload para relacionamentos

**Otimização de Query:**
- Listagem paginada com tamanho de página configurável
- Queries filtradas com múltiplos critérios
- Queries de contagem para metadados de paginação
- Lazy loading para relacionamentos opcionais

**Estratégia de Cache:**
- Cache HTTP para listas e detalhes de contrato
- Invalidação de cache em operações de mutação
- Cache de dados relacionados (clientes, estabelecimentos)

## Tratamento de Erros

**Respostas de Erro da API:**
- 400: Erros de validação (datas inválidas, valores incorretos)
- 401: Autenticação necessária
- 403: Permissão negada (acesso cross-company)
- 404: Contrato não encontrado
- 409: Conflitos de negócio (datas sobrepostas, números duplicados)
- 500: Erros internos do servidor

**Erros de Lógica de Negócio:**
- Datas de contrato inválidas
- Valores inconsistentes
- Sobreposição de vidas
- Serviços incompatíveis

**Tratamento de Erros no Frontend:**
- Blocos try-catch em chamadas de serviço
- Mensagens de erro amigáveis ao usuário
- Estados de loading e boundaries de erro

## Integrações

**Dependências Internas:**
- **Clientes**: Relacionamento principal e validação
- **Estabelecimentos**: Escopo multi-tenant e acesso
- **Profissionais**: Atribuições de serviço
- **Autorizações Médicas**: Controle de uso de serviços
- **Dashboard**: Métricas e relatórios de contrato

**Sistemas Externos:**
- **PostgreSQL**: Armazenamento primário com recursos avançados
- **Redis**: Cache e armazenamento de sessão
- **Sistema de Cobrança**: Potencial integração futura

## Testes

**Cobertura de Testes:**
- Testes unitários para métodos de repositório
- Testes de integração para endpoints da API
- Testes end-to-end para fluxos críticos de contrato
- Testes de validação de regras de negócio

**Cenários de Teste:**
- CRUD completo de contratos
- Gerenciamento de vidas e serviços
- Validação de permissões e isolamento
- Cenários de erro e casos extremos

## Monitoramento

**Logging:**
- Logging estruturado com contexto (user_id, contract_id, company_id)
- Rastreamento de operações para trilhas de auditoria
- Logging de erro com stack traces

**Métricas:**
- Tempos de resposta da API
- Taxas de erro por endpoint
- Padrões de uso do usuário
- Performance de query de banco

**Verificações de Saúde:**
- Conectividade de banco de dados
- Integridade de dados de contrato
- Funcionamento do sistema de permissões

## Decisões de Design

**Estrutura Complexa de Relacionamentos:**
- Separação em entidades distintas (contrato, vidas, serviços)
- Flexibilidade para diferentes tipos de contrato
- Suporte a mudanças incrementais

**Campos JSONB para Flexibilidade:**
- Configurações específicas por contrato
- Metadados extensíveis
- Suporte a customizações futuras

**Sistema de Vidas Sequenciais:**
- Modelo de cobertura por períodos
- Renovação e extensão flexível
- Controle granular de limites

**Validação de Regras de Negócio:**
- Validações no nível de aplicação
- Restrições de banco de dados
- Mensagens de erro específicas

## Análise DBA

**Estratégia de Índices:**
- Chave primária em id
- Índices de chave estrangeira em client_id, establishment_id
- Índices compostos únicos para regras de negócio
- Índices parciais para filtragem ativa/deletada
- GIN indexes para campos JSONB

**Considerações de Performance:**
- Particionamento potencial por establishment_id para datasets grandes
- Arquivamento para contratos expirados
- Manutenção regular de índices e atualizações de estatísticas

**Backup & Recuperação:**
- Backups completos incluindo tabelas relacionadas
- Capacidade de recuperação point-in-time
- Funcionalidade de exportação de dados de contrato
- Planejamento de recuperação de desastre

## Análise DBA - Estrutura do Banco de Dados

### Tabelas Principais do Módulo de Contratos

#### 1. **CONTRACTS** (Contratos Principais)
```sql
CREATE TABLE master.contracts (
    id                    BIGINT PRIMARY KEY,
    client_id             BIGINT NOT NULL REFERENCES clients(id),
    contract_number       VARCHAR NOT NULL UNIQUE,
    contract_type         VARCHAR NOT NULL,
    lives_contracted      INTEGER NOT NULL,
    lives_minimum         INTEGER,
    lives_maximum         INTEGER,
    allows_substitution   BOOLEAN DEFAULT false,
    control_period        VARCHAR,
    plan_name             VARCHAR NOT NULL,
    -- Campos financeiros e datas via outras colunas
    created_at            TIMESTAMP DEFAULT now(),
    updated_at            TIMESTAMP
);
```

#### 2. **CONTRACT_LIVES** (Vidas do Contrato)
```sql
CREATE TABLE master.contract_lives (
    id                    BIGINT PRIMARY KEY,
    contract_id           BIGINT NOT NULL REFERENCES contracts(id),
    person_id             BIGINT NOT NULL REFERENCES people(id),
    life_sequence         INTEGER NOT NULL,
    start_date            DATE NOT NULL,
    end_date              DATE,
    status                VARCHAR DEFAULT 'active',
    is_principal          BOOLEAN DEFAULT false,
    coverage_limits       JSONB,
    created_at            TIMESTAMP DEFAULT now()
);
```

#### 3. **CONTRACT_SERVICES** (Serviços por Contrato)
```sql
CREATE TABLE master.contract_services (
    id                         BIGINT PRIMARY KEY,
    contract_id                BIGINT NOT NULL REFERENCES contracts(id),
    service_id                 BIGINT NOT NULL REFERENCES services_catalog(id),
    monthly_limit              INTEGER,
    daily_limit                INTEGER,
    annual_limit               INTEGER,
    unit_value                 NUMERIC(10,2),
    requires_pre_authorization BOOLEAN DEFAULT false,
    start_date                 DATE NOT NULL,
    end_date                   DATE,
    status                     VARCHAR DEFAULT 'active'
);
```

### Índices Estratégicos
```sql
-- Índices para performance
CREATE INDEX idx_contracts_client ON contracts(client_id);
CREATE INDEX idx_contracts_number ON contracts(contract_number);
CREATE INDEX idx_contract_lives_contract ON contract_lives(contract_id);
CREATE INDEX idx_contract_services_contract ON contract_services(contract_id);

-- Índices compostos para queries complexas
CREATE INDEX idx_contract_lives_active ON contract_lives(contract_id, status) WHERE status = 'active';
CREATE INDEX idx_contract_services_active ON contract_services(contract_id, status) WHERE status = 'active';
```

### Views Especializadas
```sql
-- View para contratos ativos com resumo
CREATE VIEW vw_active_contracts_summary AS
SELECT
    c.id,
    c.contract_number,
    c.plan_name,
    p.name AS client_name,
    COUNT(cl.id) AS total_lives,
    COUNT(cs.id) AS total_services
FROM contracts c
JOIN clients cli ON c.client_id = cli.id
JOIN people p ON cli.person_id = p.id
LEFT JOIN contract_lives cl ON c.id = cl.contract_id AND cl.status = 'active'
LEFT JOIN contract_services cs ON c.id = cs.contract_id AND cs.status = 'active'
GROUP BY c.id, c.contract_number, c.plan_name, p.name;
```

Esta implementação abrangente fornece um sistema CRUD robusto, escalável para contratos com estrutura complexa de relacionamentos, segurança adequada, validação rigorosa e otimizações de performance adequadas para requisitos de negócio complexos.

## Estrutura em Formato de Árvore

```
.
├── Backend
│   ├── app/infrastructure/orm/models.py
│   ├── app/infrastructure/repositories/contract_repository.py
│   ├── app/presentation/schemas/contract.py
│   ├── app/presentation/api/v1/contracts.py
│   ├── app/presentation/decorators/simple_permissions.py
│   ├── app/infrastructure/services/contract_dashboard_service.py
│   └── app/infrastructure/services/system_optimization_service.py
├── Frontend
│   ├── frontend/src/pages/ContractsPage.tsx
│   ├── frontend/src/components/forms/ContractForm.tsx
│   ├── frontend/src/components/forms/ContractFormSections.tsx
│   ├── frontend/src/components/views/ContractDetails.tsx
│   ├── frontend/src/components/search/ContractSearchModal.jsx
│   ├── frontend/src/config/tables/contracts.config.tsx
│   ├── frontend/src/services/contractsService.ts
│   ├── frontend/src/hooks/useDataTable.ts
│   └── frontend/src/utils/contractCalculations.js
├── Tests
│   ├── tests/test_contracts_crud.py
│   ├── tests/test_home_care_business_rules.py
│   └── tests/test_home_care_integration.py
├── Config/Outros
│   ├── migrations/008_create_contract_tables.py
│   ├── scripts/create_contract_menus_complete.py
│   ├── scripts/create_contract_menus_simple.py
│   ├── scripts/create_contract_menus.py
│   ├── scripts/create_contract_views.py
│   └── scripts/add_contract_permissions.py
```
