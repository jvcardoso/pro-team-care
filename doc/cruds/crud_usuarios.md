# Documento da Estrutura de Arquivos do CRUD de Usuários

## Backend

### Camada de Domínio
- **app/domain/entities/user.py**: Entidade pura do domínio com métodos de lógica de negócio (is_verified, is_admin, can_login, etc.)
- **app/application/dto/user_dto.py**: Comandos e esquemas para operações de usuário (CreateUserCommand, UserResponse, UserActivation, etc.)

### Camada de Aplicação
- **app/application/use_cases/user_management_use_case.py**: Gerencia fluxos de trabalho de convite, ativação e gerenciamento de usuários
- **app/application/use_cases/auth_use_case.py**: Casos de uso de autenticação (login, registro, criação de token)

### Camada de Infraestrutura
- **app/infrastructure/repositories/user_repository.py**: Repositório CRUD completo com criação de pessoa/contato
- **app/infrastructure/repositories/user_repository_enhanced.py**: Repositório aprimorado com views de segurança e logging de auditoria
- **app/infrastructure/repositories/hierarchical_user_repository.py**: Repositório de controle de acesso hierárquico
- **app/infrastructure/services/auth_service.py**: Hashing de senha, gerenciamento de tokens JWT
- **app/infrastructure/services/email_service.py**: Envio de email para ativação/convite
- **app/infrastructure/orm/models.py**: Modelo ORM de usuário com relacionamentos e restrições

### Camada de Apresentação
- **app/presentation/api/v1/users.py**: Endpoints CRUD principais com filtragem multi-tenant
- **app/presentation/api/v1/user_activation.py**: Endpoints de convite e ativação de usuário
- **app/presentation/api/v1/users_hierarchical.py**: Gerenciamento hierárquico de usuários com controle de acesso

## Frontend

### Páginas
- **frontend/src/pages/UsersPage.jsx**: Página principal de listagem de usuários com tabela de dados
- **frontend/src/pages/ActivationPage.jsx**: Página de ativação de conta de usuário

### Componentes
- **frontend/src/components/forms/UserForm.jsx**: Formulário de criação/edição de usuário com validação
- **frontend/src/components/mobile/RoleMobileCard.jsx**: Componente de cartão de função otimizado para mobile com ícones de contexto, badges de nível e dropdown de ações

### Hooks
- **frontend/src/hooks/useDataTable.ts**: Hook genérico para tabelas de dados com métricas de usuários
- **frontend/src/hooks/useErrorHandler.ts**: Hook para tratamento de erros com mensagens amigáveis ao usuário

### Serviços
- **frontend/src/services/userActivationService.js**: Serviço frontend para operações de ativação

## Configuração

### Banco de Dados
- **Estrutura da tabela User**: Multi-tenant com contexto empresa/estabelecimento, tokens de ativação, suporte 2FA
- **Views**: vw_users_complete, vw_users_hierarchical, vw_users_admin para diferentes níveis de acesso
- **Funções**: get_accessible_users_hierarchical, check_user_permission para controle de acesso

## Testes

### Testes de Backend
- **tests/test_auth.py**: Testes de autenticação (login, registro, validação de token)

## Scripts

### Scripts de Administração
- **scripts/admin/create_admin_user.py**: Cria usuário admin inicial para desenvolvimento
- **scripts/migrate_users_to_granular_permissions.py**: Migra usuários para sistema de permissões granulares

## Visão Geral Arquitetural

### Implementação da Clean Architecture
- **Domínio**: Entidades puras de negócio com lógica de validação
- **Aplicação**: Casos de uso orquestram fluxos de trabalho de negócio
- **Infraestrutura**: Preocupações externas (BD, auth, email)
- **Apresentação**: Endpoints da API com decoradores de segurança

### Arquitetura Multi-Tenant
- Usuários pertencem a empresas com contexto opcional de estabelecimento
- Sistema de permissões hierárquico (ROOT → Admin Empresa → Admin Estabelecimento → Usuário)
- Segurança a nível de linha com middleware de contexto de tenant

### Recursos de Segurança
- Autenticação JWT com tokens de refresh
- Hashing de senha com bcrypt
- Suporte 2FA (segredo + códigos de recuperação)
- Verificação de email e tokens de ativação
- Controle de acesso hierárquico com níveis de permissão
- Logging de auditoria para operações sensíveis

## Modelo de Dados

### Campos da Entidade User
- Básicos: id, person_id, company_id, establishment_id, email_address
- Segurança: password, two_factor_secret, two_factor_recovery_codes
- Status: is_active, is_system_admin, status (active/pending/suspended)
- Contexto: context_type (company/establishment/client)
- Ativação: activation_token, activation_expires_at, activated_at
- Auditoria: created_at, updated_at, deleted_at, last_login_at
- Preferências: preferences (JSON), notification_settings (JSON)

### Relacionamentos
- Person (1:1): Dados pessoais (name, tax_id, birth_date, etc.)
- Company (N:1): Isolamento multi-tenant
- Establishment (N:1, opcional): Contexto sub-tenant
- UserRole (1:N): Permissões granulares
- UserEstablishment (1:N): Acesso a múltiplos estabelecimentos

## Segurança

### Autenticação
- Tokens JWT com expiração configurável
- Requisitos de complexidade de senha (8+ caracteres)
- Bloqueio de conta após tentativas falhadas
- Funcionalidade "lembrar-me"

### Autorização
- Controle de acesso baseado em função (RBAC) com níveis hierárquicos
- Acesso baseado em permissão (users.view, users.create, etc.)
- Permissões cientes de contexto (empresa vs estabelecimento)
- Bypass de admin do sistema para todas as operações

### Proteção de Dados
- Soft deletes para trilha de auditoria
- Campos sensíveis criptografados (segredos 2FA)
- Conformidade LGPD com rastreamento de consentimento
- Logs de auditoria para todas as operações de usuário

## Regras de Negócio

### Criação de Usuário
- Unicidade de email por empresa
- Criação de registro de pessoa com validação de tax_id
- Envio de email de ativação para novos usuários
- Atribuição de função baseada no contexto do convite

### Ativação de Usuário
- Ativação baseada em token com expiração de 24h
- Definição de senha durante ativação
- Transição de status de 'pending' para 'active'
- Requisito de verificação de email

### Gerenciamento de Usuário
- Controle de acesso hierárquico (usuários só podem ver/gerenciar subordinados)
- Isolamento de empresa (usuários não podem acessar outras empresas)
- Preservação de soft delete para auditoria
- Rastreamento de mudança de senha

### Sistema de Permissões
- Permissões granulares (users.view, users.edit, etc.)
- Permissões específicas de contexto (empresa/estabelecimento)
- Herança de função para simplicidade
- Verificação dinâmica de permissões

## Performance

### Otimização de Banco de Dados
- Campos indexados: email, company_id, person_id, status
- Índices compostos para consultas comuns
- Views para consultas hierárquicas complexas
- Pooling de conexões com asyncpg

### Estratégia de Cache
- Permissões de usuário em cache por sessão de usuário
- Dados de sessão em cache no Redis
- Cache de resultados de consulta para operações frequentes
- Invalidação de cache nas atualizações de usuário

### Otimização de Consultas
- Eager loading para entidades relacionadas
- Carregamento seletivo de campos para reduzir uso de memória
- Consultas paginadas com limites configuráveis
- Consultas filtradas para limitar transferência de dados

## Tratamento de Erros

### Erros de Validação
- Validação de formato de email
- Requisitos de força de senha
- Validação de formato de tax ID
- Violações de restrição única

### Erros de Lógica de Negócio
- Usuário não encontrado (404)
- Permissão negada (403)
- Token de ativação inválido
- Email duplicado por empresa

### Erros de Sistema
- Falhas de conexão com banco de dados
- Falhas de serviço de email
- Erros de geração de token
- Falhas de cache (degradação graciosa)

## Integrações

### Serviço de Email
- Integração SMTP para notificações
- Emails baseados em template (ativação, redefinição de senha)
- Envio assíncrono de email com lógica de retry
- Verificação de email e tratamento de bounce

### Serviços Externos
- Enriquecimento de endereço (opcional)
- Serviços de geolocalização (opcional)
- SMS para 2FA (futuro)

## Testes

### Testes Unitários
- Lógica de negócio da entidade de domínio
- Operações CRUD do repositório
- Funcionalidade da camada de serviço
- Validação de DTO

### Testes de Integração
- Teste de endpoints da API com autenticação
- Teste de transações de banco de dados
- Integração com serviço de email
- Teste de fluxo de autenticação

### Testes E2E
- Fluxo de registro de usuário
- Ciclo de login/logout
- Operações de gerenciamento de usuário
- Aplicação de permissões

## Monitoramento

### Logging
- Logging estruturado com contexto
- Trilha de auditoria para operações sensíveis
- Rastreamento de erros com stack traces
- Monitoramento de performance

### Métricas
- Taxa de registro de usuário
- Taxas de sucesso/falha de login
- Performance de verificação de permissões
- Performance de consulta de banco de dados

### Alertas
- Tentativas de login falhadas
- Violações de permissão
- Uso de recursos do sistema
- Problemas de conexão com banco de dados

## Decisões de Design

### Design Multi-Tenant
- Isolamento baseado em empresa para escalabilidade
- Sub-tenancy de estabelecimento para flexibilidade
- Schema compartilhado com RLS para segurança

### Permissões Hierárquicas
- Controle de acesso baseado em nível (faixa 40-90)
- Permissões cientes de contexto
- Herança de função para simplicidade

### Fluxo de Ativação
- Verificação baseada em email para segurança
- Expiração de token para segurança
- Definição de senha durante ativação

### Soft Deletes
- Requisitos de conformidade de auditoria
- Capacidades de recuperação de dados
- Necessidades de relatórios históricos

## Análise DBA

### Relacionamentos de Tabela
```
users (1) ──── (N) user_roles (N) ──── (1) roles
                              │
                              └── (1) role_permissions (N) ──── (1) permissions
```

### Considerações de Performance
- Potencial de particionamento para grandes conjuntos de dados
- Estratégia de arquivamento para atribuições de função expiradas
- Configuração de pooling de conexões
- Otimização de consultas para acesso hierárquico

### Scripts de Manutenção
- Jobs de limpeza: Remover atribuições de função expiradas periodicamente
- Jobs de validação: Verificar permissões órfãs e atribuições de função inválidas
- Analytics de uso: Gerar relatórios sobre utilização de função e padrões de permissão

### Estratégia de Backup
- Dados críticos: Tabelas de função e permissão requerem recuperação point-in-time
- Consistência: Garantir backup conjunto de user_roles e role_permissions
- Testes: Testes regulares de restauração para recuperação de atribuição de função

## Análise DBA - Estrutura do Banco de Dados

### Tabela Principal: USERS

```sql
CREATE TABLE master.users (
    id                         BIGINT PRIMARY KEY,
    person_id                  BIGINT NOT NULL REFERENCES people(id),
    email_address              VARCHAR NOT NULL UNIQUE,
    email_verified_at          TIMESTAMP,
    password                   VARCHAR NOT NULL,
    remember_token             VARCHAR,
    is_active                  BOOLEAN DEFAULT true,
    is_system_admin            BOOLEAN DEFAULT false,
    preferences                JSONB,
    notification_settings      JSONB,
    two_factor_secret          TEXT,
    two_factor_recovery_codes  TEXT,
    last_login_at              TIMESTAMP,
    password_changed_at        TIMESTAMP,
    created_at                 TIMESTAMP DEFAULT now(),
    updated_at                 TIMESTAMP DEFAULT now()
);
```

### Índices de Segurança
```sql
CREATE UNIQUE INDEX idx_users_email ON users(email_address);
CREATE INDEX idx_users_person ON users(person_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX idx_users_admin ON users(is_system_admin) WHERE is_system_admin = true;
```

### Views de Sistema
```sql
CREATE VIEW vw_users_complete AS
SELECT
    u.id, u.email_address, u.is_active, u.last_login_at,
    p.name, p.tax_id, COUNT(ur.role_id) AS roles_count
FROM users u
JOIN people p ON u.person_id = p.id
LEFT JOIN user_roles ur ON u.id = ur.user_id AND ur.status = 'active'
WHERE u.is_active = true
GROUP BY u.id, u.email_address, u.is_active, u.last_login_at, p.name, p.tax_id;
```

## Estrutura em Formato de Árvore

```
.
├── Backend
│   ├── app/domain/entities/user.py
│   ├── app/application/dto/user_dto.py
│   ├── app/application/use_cases/user_management_use_case.py
│   ├── app/application/use_cases/auth_use_case.py
│   ├── app/infrastructure/repositories/user_repository.py
│   ├── app/infrastructure/repositories/user_repository_enhanced.py
│   ├── app/infrastructure/repositories/hierarchical_user_repository.py
│   ├── app/infrastructure/services/auth_service.py
│   ├── app/infrastructure/services/email_service.py
│   ├── app/infrastructure/orm/models.py
│   ├── app/presentation/api/v1/users.py
│   ├── app/presentation/api/v1/user_activation.py
│   └── app/presentation/api/v1/users_hierarchical.py
├── Frontend
│   ├── frontend/src/pages/UsersPage.jsx
│   ├── frontend/src/pages/ActivationPage.jsx
│   ├── frontend/src/components/forms/UserForm.jsx
│   ├── frontend/src/components/mobile/RoleMobileCard.jsx
│   ├── frontend/src/hooks/useDataTable.ts
│   ├── frontend/src/hooks/useErrorHandler.ts
│   └── frontend/src/services/userActivationService.js
├── Configuração
│   └── database/
├── Testes
│   └── tests/test_auth.py
└── Scripts
    ├── scripts/admin/create_admin_user.py
    └── scripts/migrate_users_to_granular_permissions.py
```