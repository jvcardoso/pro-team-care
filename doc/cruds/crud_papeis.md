# Documento da Estrutura de Arquivos do CRUD de Papéis

## Backend

- **`app/presentation/api/v1/roles.py`** - Router FastAPI principal com endpoints CRUD completos (criar, listar, obter, atualizar, deletar) e endpoints utilitários para tipos de contexto e níveis de papel. Usa decoradores de permissão e tratamento de erros abrangente.
- **`app/presentation/api/v1/api.py`** - Inclui router de papéis na configuração da API principal.
- **`app/presentation/schemas/role.py`** - Esquemas Pydantic completos para papéis, permissões e entidades relacionadas incluindo validação, enums e modelos de resposta.
- **`app/infrastructure/repositories/role_repository.py`** - Implementação do padrão repositório com classes RoleRepository e PermissionRepository lidando com todas as operações de banco de dados, queries complexas com agregação JSON e gerenciamento de permissões.
- **`app/infrastructure/orm/models.py`** - Modelos SQLAlchemy para entidades Role, Permission, UserRole e RolePermission com relacionamentos, restrições e índices.
- **`app/presentation/decorators/role_permissions.py`** - Decoradores para controle de acesso baseado em papéis com funções `require_role_permission` e `require_role_level_or_permission`.
- **`app/presentation/decorators/simple_permissions.py`** - Decoradores alternativos usando papéis de usuário e permissões de papel.

## Frontend

- **`frontend/src/pages/RolesPage.jsx`** - Página principal de gerenciamento de papéis com listagem, filtragem, paginação, estatísticas de cards e integração de formulário. Design responsivo com tabela desktop, cards tablet e mobile.
- **`frontend/src/components/forms/RoleForm.jsx`** - Formulário abrangente de criação/edição de papel com seleção de permissões, validação e exibição de permissões agrupadas.
- **`frontend/src/components/mobile/RoleMobileCard.jsx`** - Componente otimizado para mobile de card de papel com ícones de contexto, badges de nível e dropdown de ações.
- **`frontend/src/services/rolesService.js`** - Camada de serviço da API com métodos para todas as operações CRUD, gerenciamento de permissões e endpoints utilitários.
- **`frontend/src/hooks/useDataTable.ts`** - Hook genérico para tabelas de dados com métricas específicas de papéis.
- **`frontend/src/hooks/useErrorHandler.ts`** - Hook para tratamento de erros em operações de papel.

## Config/Outros

- **`migrations/007_permission_migration_setup.sql`** - Migração de banco de dados configurando templates de papel e sistema de permissões.
- **`migrations/001_create_hierarchical_functions.sql`** - Funções iniciais de controle de acesso hierárquico de usuário usando papéis.
- **`scripts/add_contract_permissions.py`** - Script para atribuir permissões a papéis admin durante configuração.
- **`scripts/migrate_users_to_granular_permissions.py`** - Script de migração para converter usuários para sistema de permissões granulares usando papéis.
- **`validate_roles_usage.py`** - Script de validação para analisar uso de papéis no sistema.

## Visão Geral Arquitetural

**Implementação de Arquitetura Limpa:**
- **Camada de Apresentação**: Routers FastAPI e esquemas Pydantic lidam com requisições HTTP/respostas
- **Camada de Aplicação**: Repositório implementa lógica de negócio e acesso a dados
- **Camada de Infraestrutura**: Modelos SQLAlchemy e operações de banco de dados
- **Camada de Domínio**: Regras de negócio core e validação de entidades

**Sistema de Contexto Multi-Tenant:**
- Papéis operam dentro de três níveis de contexto: sistema, empresa, estabelecimento
- Modelo de permissão hierárquica com níveis 10-100 e categorias pré-definidas
- Atribuição flexível de usuários com diferentes contextos

**Modelo de Permissão Granular:**
- Níveis hierárquicos + permissões específicas (formato module.action.resource)
- Atribuição flexível permitindo combinação de nível OU permissão específica
- Contexto-aware com verificações de permissão dentro do contexto apropriado

## Modelo de Dados

**Tabelas Core:**

#### `master.roles`
```sql
- id: Chave primária
- name: Nome técnico único (snake_case)
- display_name: Nome legível por humanos
- description: Descrição opcional
- level: Nível hierárquico (10-100)
- context_type: system/company/establishment
- is_active: Flag de status
- is_system_role: Impede modificação
- settings: Configuração JSON
- created_at/updated_at: Timestamps
```

#### `master.permissions`
```sql
- id: Chave primária
- name: Nome único de permissão
- display_name: Nome legível por humanos
- module: Módulo funcional (admin, clinical, etc.)
- action: Operação CRUD (view, create, edit, delete)
- resource: Recurso alvo (users, companies, etc.)
- context_level: Contexto aplicável
- is_active: Flag de status
```

#### `master.role_permissions`
```sql
- role_id: Chave estrangeira para roles
- permission_id: Chave estrangeira para permissions
- granted_at: Timestamp
- UNIQUE(role_id, permission_id)
```

#### `master.user_roles`
```sql
- user_id: Chave estrangeira para users
- role_id: Chave estrangeira para roles
- context_type: Contexto de aplicação
- context_id: Instância de contexto específica
- status: active/inactive/suspended/expired
- assigned_at/expires_at: Controle temporal
- UNIQUE(user_id, role_id, context_type, context_id)
```

## Segurança

**Mecanismos de Controle de Acesso:**

1. **Acesso Baseado em Permissões**: Decoradores verificam permissões específicas via papéis do usuário
2. **Acesso Baseado em Nível**: Requisitos de nível mínimo de papel
3. **Lógica OR**: Nível OU permissão específica permite acesso flexível
4. **Contexto-Aware**: Permissões verificadas dentro do contexto apropriado (system/company/establishment)

**Recursos de Segurança:**

- **Proteção de Papel do Sistema**: `is_system_role` impede modificação/exclusão
- **Soft Delete**: Papéis em uso são desativados em vez de deletados
- **Restrições de Unicidade**: Previne atribuições duplicadas
- **Auditoria Trail**: Timestamps e rastreamento de usuário para atribuições de papel
- **Validação de Entrada**: Validação Pydantic abrangente com validadores customizados

## Regras de Negócio

**Gerenciamento de Papel:**

1. **Convenção de Nomenclatura**: Nomes técnicos devem ser minúsculos com underscores
2. **Hierarquia de Níveis**: Escala 10-100 com significado semântico
3. **Restrições de Contexto**: Papéis aplicam apenas dentro do contexto definido
4. **Imutabilidade de Papel do Sistema**: Papéis do sistema não podem ser modificados ou deletados
5. **Herança de Permissões**: Usuários herdam todas as permissões de seus papéis atribuídos

**Atribuição de Permissões:**

1. **Apenas Permissões Ativas**: Apenas permissões ativas podem ser atribuídas
2. **Verificação de Permissões Válidas**: Repositório valida existência de permissão antes da atribuição
3. **Operações em Massa**: Permissões podem ser atualizadas em massa durante modificação de papel
4. **Resolução de Conflitos**: ON CONFLICT DO NOTHING previne atribuições duplicadas

**Atribuição de Usuário:**

1. **Específica de Contexto**: Atribuições usuário-papel são context-aware
2. **Combinações Únicas**: Sem combinações duplicadas usuário-papel-contexto
3. **Gerenciamento de Status**: Papéis podem ser ativos, inativos, suspensos ou expirados
4. **Controle Temporal**: Datas de expiração opcionais para atribuições de papel

## Performance

**Índices de Banco de Dados:**
```sql
- roles_name_idx: Lookups de nome único
- roles_level_idx: Filtragem baseada em nível
- roles_context_idx: Queries baseadas em contexto
- user_roles_user_idx: Lookups de papel de usuário
- user_roles_role_idx: Contagens de usuário de papel
- user_roles_context_idx: Queries context-aware
- role_permissions_role_idx: Joins de permissão de papel
- role_permissions_permission_idx: Joins de papel de permissão
```

**Otimizações de Query:**

1. **Agregação JSON**: Query única retorna papéis com detalhes completos de permissão
2. **Paginação**: LIMIT/OFFSET eficiente com queries de contagem total
3. **Operações em Massa**: Atribuições de permissões em massa usando cláusulas VALUES
4. **Lookups Indexados**: Relacionamentos de chave estrangeira otimizados

**Estratégia de Cache:**
- Verificações de permissão cacheadas por sessão de usuário
- Dados de papel cacheados para lookups frequentes
- Cache específico de contexto para reduzir hits de banco

## Tratamento de Erros

**Erros de Validação:**
- **Unicidade de Nome**: 400 erro para nomes de papel duplicados
- **Proteção de Papel do Sistema**: 400 erro para tentar modificar papéis do sistema
- **Tipo de Contexto Inválido**: 400 erro para tipos de contexto não suportados
- **Faixa de Nível**: 400 erro para níveis fora de 10-100

**Erros de Permissões:**
- **403 Proibido**: Permissões faltando ou nível insuficiente
- **Incompatibilidade de Contexto**: Verificações de permissão falham para contexto errado
- **Recursos Inativos**: Operações bloqueadas em papéis/permissões inativos

**Erros de Banco de Dados:**
- **Falhas de Conexão**: 500 erro com mecanismos de retry
- **Rollback de Transação**: Rollback automático em falhas de operação
- **Violações de Restrição**: Mensagens de erro adequadas para restrições de banco

## Integrações

**Sistema de Gerenciamento de Usuário:**
- Papéis integram com autenticação de usuário e gerenciamento de sessão
- Perfis de usuário exibem papéis atribuídos e permissões efetivas
- Mudanças de papel disparam invalidação de cache de permissão

**Sistema de Menu:**
- Menus dinâmicos baseados em papéis e permissões do usuário
- Visibilidade de menu context-aware
- Controle de acesso hierárquico de menu

**Sistema de Auditoria:**
- Atribuições de papel logadas com timestamps
- Mudanças de permissão rastreadas
- Atividade do usuário monitorada baseada em papéis

## Testes

**Testes Unitários:**
- Métodos de repositório testados com mock de banco
- Validação de esquema testada com várias entradas
- Lógica de verificação de permissão validada

**Testes de Integração:**
- Endpoint da API completo testado com autenticação
- Transação de banco testada
- Validação de permissão cross-contexto

**Testes End-to-End:**
- Ciclo de vida completo de papel testado
- Atribuição de usuário e herança de permissão
- Integração frontend-backend validada

## Monitoramento

**Logging:**
- Logging estruturado com IDs de usuário, permissões e contexto
- Eventos de concessão/negação de permissão logados
- Criação/modificação de papel rastreada
- Métricas de performance para queries lentas

**Métricas:**
- Estatísticas de uso de papel
- Taxas de sucesso/falha de verificação de permissão
- Performance de query de banco
- Padrões de uso de endpoint da API

## Decisões de Design

**Sistema de Permissões Granulares:**
**Decisão**: Implementar permissões granulares além de papéis apenas baseados em nível
**Racional**: Fornece controle fino enquanto mantém simplicidade baseada em papel
**Impacto**: Configuração mais complexa mas maior flexibilidade de segurança

**Papéis Context-Aware:**
**Decisão**: Sistema multi-tenant de contexto (system/company/establishment)
**Racional**: Suporta hierarquias organizacionais complexas
**Impacto**: Complexidade aumentada mas habilita sofisticado controle de acesso

**Hierárquicos Níveis + Permissões:**
**Decisão**: Combinar níveis hierárquicos com permissões específicas
**Racional**: Permite acesso simples baseado em nível e complexo baseado em permissão
**Impacto**: Modelo de autorização flexível suportando vários casos de uso

**Soft Delete para Papéis:**
**Decisão**: Desativar papéis em vez de hard delete quando em uso
**Racional**: Impede perda acidental de permissão para usuários ativos
**Impacto**: Integridade de dados mantida, limpeza requer intervenção manual

## Análise DBA

**Relacionamentos de Tabela:**
```
users (1) ──── (N) user_roles (N) ──── (1) roles
                              │
                              └── (1) role_permissions (N) ──── (1) permissions
```

**Considerações de Performance:**
- **Particionamento**: Considerar particionamento de user_roles por context_type para datasets grandes
- **Arquivamento**: Implementar estratégia de arquivamento para atribuições de papel expiradas
- **Replicação**: Dados de papel devem ser replicados para alta disponibilidade

**Scripts de Manutenção:**
- **Jobs de Limpeza**: Remover atribuições de papel expiradas periodicamente
- **Jobs de Validação**: Verificar permissões órfãs e atribuições de papel inválidas
- **Analytics de Uso**: Gerar relatórios sobre utilização de papel e padrões de permissão

**Estratégia de Backup:**
- **Dados Críticos**: Tabelas de papel e permissão requerem recuperação point-in-time
- **Consistência**: Garantir backup de user_roles e role_permissions juntos
- **Teste**: Testes regulares de restore para recuperação de atribuição de papel

## Análise DBA - Estrutura do Banco de Dados

### Sistema de Papéis e Permissões

#### 1. **ROLES** (Papéis/Funções)
```sql
CREATE TABLE master.roles (
    id                BIGINT PRIMARY KEY,
    name              VARCHAR NOT NULL UNIQUE,
    display_name      VARCHAR NOT NULL,
    description       TEXT,
    level             INTEGER NOT NULL CHECK (level BETWEEN 10 AND 100),
    context_type      VARCHAR NOT NULL CHECK (context_type IN ('system','company','establishment')),
    is_active         BOOLEAN DEFAULT true,
    is_system_role    BOOLEAN DEFAULT false,
    settings          JSONB,
    created_at        TIMESTAMP DEFAULT now(),
    updated_at        TIMESTAMP DEFAULT now()
);
```

#### 2. **PERMISSIONS** (Permissões Granulares)
```sql
CREATE TABLE master.permissions (
    id                BIGINT PRIMARY KEY,
    name              VARCHAR NOT NULL UNIQUE,
    display_name      VARCHAR NOT NULL,
    module            VARCHAR NOT NULL,
    action            VARCHAR NOT NULL,
    resource          VARCHAR NOT NULL,
    context_level     VARCHAR NOT NULL,
    is_active         BOOLEAN DEFAULT true
);
```

#### 3. **USER_ROLES** (Atribuições Usuário-Papel)
```sql
CREATE TABLE master.user_roles (
    user_id           BIGINT NOT NULL REFERENCES users(id),
    role_id           BIGINT NOT NULL REFERENCES roles(id),
    context_type      VARCHAR NOT NULL,
    context_id        BIGINT,
    status            VARCHAR DEFAULT 'active',
    assigned_at       TIMESTAMP DEFAULT now(),
    expires_at        TIMESTAMP,
    PRIMARY KEY (user_id, role_id, context_type, COALESCE(context_id, 0))
);
```

### Índices de Performance
```sql
-- Índices críticos para verificação de permissões
CREATE INDEX idx_user_roles_user ON user_roles(user_id, status);
CREATE INDEX idx_user_roles_context ON user_roles(context_type, context_id);
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_permissions_module_action ON permissions(module, action);
```

### Views de Sistema
```sql
-- View para hierarquia completa de papéis
CREATE VIEW vw_roles_hierarchy AS
SELECT
    r.id,
    r.name,
    r.display_name,
    r.level,
    r.context_type,
    COUNT(rp.permission_id) AS permissions_count,
    COUNT(ur.user_id) AS users_count
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN user_roles ur ON r.id = ur.role_id AND ur.status = 'active'
WHERE r.is_active = true
GROUP BY r.id, r.name, r.display_name, r.level, r.context_type;
```

Esta implementação abrangente de CRUD de Papéis fornece controle de acesso enterprise-grade com flexibilidade, segurança e otimizações de performance adequadas para aplicações complexas multi-tenant de saúde.

## Estrutura em Formato de Árvore

```
.
├── Backend
│   ├── app/presentation/api/v1/roles.py
│   ├── app/presentation/api/v1/api.py
│   ├── app/presentation/schemas/role.py
│   ├── app/infrastructure/repositories/role_repository.py
│   ├── app/infrastructure/orm/models.py
│   ├── app/presentation/decorators/role_permissions.py
│   └── app/presentation/decorators/simple_permissions.py
├── Frontend
│   ├── frontend/src/pages/RolesPage.jsx
│   ├── frontend/src/components/forms/RoleForm.jsx
│   ├── frontend/src/components/mobile/RoleMobileCard.jsx
│   └── frontend/src/services/rolesService.js
├── Config/Outros
│   ├── migrations/007_permission_migration_setup.sql
│   ├── migrations/001_create_hierarchical_functions.sql
│   ├── scripts/add_contract_permissions.py
│   ├── scripts/migrate_users_to_granular_permissions.py
│   └── validate_roles_usage.py
```
