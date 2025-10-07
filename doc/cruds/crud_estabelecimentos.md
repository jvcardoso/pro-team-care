# Documento da Estrutura de Arquivos do CRUD de Estabelecimentos

## Backend

- **app/infrastructure/orm/models.py**: Define o modelo SQLAlchemy `Establishment` com relacionamentos, restrições e índices para performance. Inclui validação de status e suporte a soft delete.
- **app/infrastructure/repositories/establishment_repository.py**: Repositório implementando operações CRUD, validação e lógica de negócio. Inclui queries complexas e gerenciamento de transações.
- **app/presentation/schemas/establishment.py**: Esquemas Pydantic para validação de requisição/resposta e serialização. Inclui modelos base, parâmetros de lista, DTOs de criação/atualização e respostas de validação.
- **app/presentation/api/v1/establishments.py**: Router FastAPI com endpoints para todas as operações CRUD. Inclui decoradores de permissão, validação e tratamento de erros estruturado.

## Frontend

- **frontend/src/pages/EstablishmentsPage.jsx**: Página principal de gerenciamento de estabelecimentos com listagem, filtragem, paginação, estatísticas e integração de formulário. Design responsivo com tabela desktop, cards tablet e mobile.
- **frontend/src/components/views/EstablishmentDetails.jsx**: Componente para exibir detalhes de estabelecimento.
- **frontend/src/components/forms/EstablishmentForm.tsx**: Formulário de criação/edição de estabelecimento com validação.
- **frontend/src/components/forms/EstablishmentFormSections.tsx**: Seções modulares do formulário para entrada de dados.
- **frontend/src/components/search/EstablishmentSearchModal.jsx**: Modal de busca para estabelecimentos.
- **frontend/src/config/tables/establishments.config.tsx**: Configuração de tabela de dados com colunas, ações e métricas.
- **frontend/src/services/api.js**: Camada de serviço da API com endpoints de estabelecimentos.
- **frontend/src/services/establishmentsService.ts**: Serviço dedicado para operações de estabelecimento.
- **frontend/src/utils/establishmentCodeGenerator.js**: Utilitário para geração de códigos de estabelecimento.
- **frontend/src/hooks/useDataTable.ts**: Hook com métricas específicas de estabelecimento.

## Tests

- **tests/test_establishments.py**: Testes abrangentes de API backend.
- **frontend/src/__tests__/services/establishmentsService.test.js**: Testes de serviço frontend.
- **frontend/src/__tests__/integration/establishments-integration.test.js**: Testes de integração.
- **frontend/src/__tests__/pages/EstablishmentsPage.test.jsx**: Testes de página.
- **frontend/src/__tests__/components/EstablishmentsPage.test.jsx**: Testes de componente.

## Config/Outros

- **migrations/004_establishments_migration.sql**: Migração de esquema de banco de dados, restrições e funções.
- **migrations/001_create_hierarchical_functions.sql**: Funções de controle de acesso hierárquico para estabelecimentos.
- **migrations/007_permission_migration_setup.sql**: Configuração de permissões e papéis.
- **config/settings.py**: Configuração da aplicação.

## Visão Geral Arquitetural

**Padrão Arquitetural Limpa:**
- **Camada de Apresentação**: Routers FastAPI e esquemas Pydantic lidam com requisições HTTP/respostas
- **Camada de Aplicação**: Repositório implementa lógica de negócio e acesso a dados
- **Camada de Infraestrutura**: Modelos SQLAlchemy e operações de banco de dados
- **Camada de Domínio**: Regras de negócio e validação de entidades

**Segurança Multi-Tenant:**
- Operações escopadas por empresa com filtragem automática
- Bypass de admin do sistema para acesso cross-company
- Controle de acesso baseado em permissões com níveis hierárquicos

**Fluxo de Dados:**
1. Componentes frontend disparam chamadas de API via camada de serviço
2. Routers FastAPI validam requisições e aplicam permissões
3. Camada de repositório executa lógica de negócio e operações de banco
4. Respostas são serializadas através de esquemas Pydantic

## Modelo de Dados

**Estrutura da Tabela `establishments`:**
```sql
CREATE TABLE master.establishments (
    id BIGINT PRIMARY KEY,
    person_id BIGINT REFERENCES master.people(id),
    company_id BIGINT REFERENCES master.companies(id),
    code VARCHAR(50) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('matriz', 'filial', 'unidade', 'posto')),
    category VARCHAR(30) CHECK (category IN ('clinica', 'hospital', 'laboratorio', ...)),
    is_active BOOLEAN DEFAULT TRUE,
    is_principal BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    settings JSONB,
    metadata JSONB,
    operating_hours JSONB,
    service_areas JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

**Restrições Chave:**
- Código único por empresa
- Ordem de exibição única por empresa
- Apenas um estabelecimento principal por empresa
- Soft delete com deleted_at

**Relacionamentos:**
- Pertence a Company (many-to-one)
- Pertence a Person (many-to-one)
- Tem muitos Users (via user_establishments)
- Tem muitos Professionals
- Tem muitos Clients

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

**Criação de Estabelecimento:**
- Código deve ser único dentro da empresa
- Apenas um estabelecimento principal por empresa
- Atribuição automática de ordem de exibição
- Validação de criação ou reutilização de pessoa
- Unicidade de CNPJ (a menos que reutilizando pessoa existente)

**Gerenciamento de Estabelecimento:**
- Soft delete apenas se não houver dependências (usuários, profissionais, clientes)
- Toggle de status afeta disponibilidade
- Reordenação dentro do escopo da empresa
- Validação de atualização previne conflitos

**Regras Multi-Tenant:**
- Usuários veem apenas estabelecimentos de sua empresa
- Admins do sistema podem acessar todos os estabelecimentos
- Operações cross-company bloqueadas para usuários regulares

## Performance

**Otimização de Banco de Dados:**
- Índices compostos em (company_id, code), (company_id, display_order)
- Índices parciais excluindo registros deletados
- Índices GIN em campos JSONB (metadata, settings)
- Queries eficientes com joinedload para relacionamentos

**Otimização de Query:**
- Listagem paginada com tamanho de página configurável
- Queries filtradas com múltiplos critérios
- Queries de contagem para metadados de paginação
- Lazy loading para relacionamentos opcionais

**Estratégia de Cache:**
- Invalidação de cache HTTP em mutações
- Gerenciamento de estado frontend com React Query
- Pooling de conexões de banco

## Tratamento de Erros

**Respostas de Erro da API:**
- 400: Erros de validação (códigos duplicados, dados inválidos)
- 401: Autenticação necessária
- 403: Permissão negada (acesso cross-company)
- 404: Estabelecimento não encontrado
- 500: Erros internos do servidor

**Erros de Lógica de Negócio:**
- ValueError para falhas de validação
- Mensagens de erro customizadas para regras de negócio
- Logging estruturado com contexto

**Tratamento de Erros no Frontend:**
- Blocos try-catch em chamadas de serviço
- Mensagens de erro amigáveis ao usuário
- Estados de loading e boundaries de erro

## Integrações

**Dependências Internas:**
- **Companies**: Relacionamento pai e validação
- **People**: Dados pessoais para detalhes de estabelecimento
- **Users**: Atribuições usuário-estabelecimento
- **Professionals**: Atribuições de profissionais
- **Clients**: Registros de clientes

**Sistemas Externos:**
- Nenhum identificado na implementação atual
- Potencial para integração com sistemas de saúde ou registros governamentais

## Testes

**Testes Backend:**
- Testes unitários para métodos de repositório
- Testes de endpoint da API com dependências mockadas
- Testes de validação e tratamento de erros
- Testes de permissão e segurança

**Testes Frontend:**
- Testes unitários de serviço
- Testes de integração de componente
- Testes de funcionalidade de página
- Testes de validação de formulário

**Cobertura de Testes:**
- Operações CRUD totalmente testadas
- Casos extremos e cenários de erro
- Limites de permissão
- Regras de validação de dados

## Monitoramento

**Logging:**
- Logging estruturado com contexto (user_id, establishment_id, company_id)
- Rastreamento de operações para trilhas de auditoria
- Logging de erro com stack traces

**Métricas:**
- Tempos de resposta da API
- Taxas de erro por endpoint
- Padrões de uso do usuário
- Performance de query de banco

**Verificações de Saúde:**
- Conectividade de banco de dados
- Integridade de dados de estabelecimento
- Funcionamento do sistema de permissões

## Decisões de Design

**Estratégia de Soft Delete:**
- Preserva integridade de dados e trilhas de auditoria
- Permite recuperação de registros acidentalmente deletados
- Mantém integridade referencial

**Campos JSONB:**
- Armazenamento flexível de configurações (settings, metadata)
- Horários de funcionamento e áreas de serviço como dados estruturados
- Query eficiente com índices GIN

**Sistema de Ordem de Exibição:**
- Reordenação manual dentro de empresas
- Restrições únicas previnem conflitos
- Ordenação eficiente e apresentação

**Padrão de Reutilização de Pessoa:**
- Permite que múltiplos estabelecimentos compartilhem dados pessoais
- Reduz duplicação para estabelecimentos da mesma entidade
- Validação previne conflitos de CNPJ

## Análise DBA

**Estratégia de Índices:**
- Chave primária em id
- Índices de chave estrangeira em person_id, company_id
- Índices compostos únicos para regras de negócio
- Índices parciais para filtragem ativa/deletada
- Índices GIN para campos JSONB

**Considerações de Performance:**
- Particionamento potencial por company_id para datasets grandes
- Arquivamento para registros antigos de estabelecimento
- Manutenção regular de índices e atualizações de estatísticas

**Backup & Recuperação:**
- Procedimentos padrão de backup PostgreSQL
- Capacidade de recuperação point-in-time
- Funcionalidade de exportação de dados do usuário
- Planejamento de recuperação de desastre

Esta implementação abrangente fornece um sistema CRUD robusto, escalável para estabelecimentos com segurança adequada, validação e otimizações de performance. A arquitetura limpa garante manutenibilidade enquanto o design multi-tenant suporta requisitos de negócio complexos.

## Estrutura em Formato de Árvore

```
.
├── Backend
│   ├── app/infrastructure/orm/models.py
│   ├── app/infrastructure/repositories/establishment_repository.py
│   ├── app/presentation/schemas/establishment.py
│   └── app/presentation/api/v1/establishments.py
├── Frontend
│   ├── frontend/src/pages/EstablishmentsPage.jsx
│   ├── frontend/src/components/views/EstablishmentDetails.jsx
│   ├── frontend/src/components/forms/EstablishmentForm.tsx
│   ├── frontend/src/components/forms/EstablishmentFormSections.tsx
│   ├── frontend/src/components/search/EstablishmentSearchModal.jsx
│   ├── frontend/src/config/tables/establishments.config.tsx
│   ├── frontend/src/services/api.js
│   ├── frontend/src/services/establishmentsService.ts
│   ├── frontend/src/utils/establishmentCodeGenerator.js
│   └── frontend/src/hooks/useDataTable.ts
├── Tests
│   ├── tests/test_establishments.py
│   ├── frontend/src/__tests__/services/establishmentsService.test.js
│   ├── frontend/src/__tests__/integration/establishments-integration.test.js
│   ├── frontend/src/__tests__/pages/EstablishmentsPage.test.jsx
│   └── frontend/src/__tests__/components/EstablishmentsPage.test.jsx
├── Config/Outros
│   ├── migrations/004_establishments_migration.sql
│   ├── migrations/001_create_hierarchical_functions.sql
│   ├── migrations/007_permission_migration_setup.sql
│   └── config/settings.py
```
