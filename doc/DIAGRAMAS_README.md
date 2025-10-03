# Diagramas do Sistema - Pro Team Care

Este diretório contém a documentação visual completa da arquitetura e funcionamento do sistema Pro Team Care.

## 📚 Índice de Diagramas

### 1. Arquitetura Geral

#### `arquitetura_sistema.drawio`
**Descrição:** Diagrama completo da arquitetura Clean Architecture do sistema
**Conteúdo:**
- Camadas: Presentation, Application, Infrastructure, Domain
- Frontend: React/TypeScript (27 páginas, 50+ componentes)
- Backend: FastAPI (38 routers, 200+ endpoints)
- Banco de Dados: PostgreSQL (45 tabelas)
- Integrações: PagBank, Redis Cache
- Fluxo de dados entre camadas

**Como usar:** Ideal para entender a estrutura macro do sistema e as responsabilidades de cada camada.

---

### 2. Modelo de Dados (ERD - Entity Relationship Diagrams)

Os diagramas ERD foram divididos por módulo para facilitar a leitura:

#### `erd_core.drawio`
**Módulo:** Core (Autenticação e Permissões)
**Tabelas:**
- `users` - Usuários do sistema
- `roles` - Perfis de acesso (19 roles)
- `permissions` - Permissões granulares (215 permissões)
- `user_roles` - Relacionamento usuário-perfil
- `role_permissions` - Relacionamento perfil-permissão
- `user_establishments` - Vínculo usuário-estabelecimento-perfil
- `sessions` - Sessões ativas
- `user_sessions` - Contextos de usuário (system/company/establishment)

**Relacionamentos:** 12 foreign keys

---

#### `erd_multi-tenant.drawio`
**Módulo:** Multi-tenant (Empresas e Estabelecimentos)
**Tabelas:**
- `companies` - Empresas clientes do SaaS
- `establishments` - Estabelecimentos/filiais das empresas

**Relacionamentos:** Hierarquia company → establishments → users

---

#### `erd_cadastros.drawio`
**Módulo:** Cadastros Base
**Tabelas:**
- `people` - Cadastro universal de pessoas (PF/PJ)
- `clients` - Clientes que contratam serviços Home Care
- `professionals` - Profissionais de saúde
- `phones` - Telefones (vinculados a people)
- `emails` - E-mails (vinculados a people)
- `addresses` - Endereços (vinculados a people)

**Relacionamentos:** Sistema unificado de cadastro com pivot em `people`

---

#### `erd_home_care_contratos.drawio`
**Módulo:** Home Care - Contratos e Serviços
**Tabelas:**
- `contracts` - Contratos com clientes (individual, corporativo, empresarial)
- `contract_lives` - Vidas/beneficiários do contrato
- `services_catalog` - Catálogo de serviços disponíveis (enfermagem, fisioterapia, medicina, etc.)
- `contract_services` - Serviços vinculados ao contrato (com limites)
- `contract_life_services` - Serviços autorizados por vida específica

**Relacionamentos:** Hierarquia contract → lives → services

---

#### `erd_financeiro_contratos.drawio`
**Módulo:** Financeiro - Faturamento de Contratos
**Tabelas:**
- `contract_billing_schedules` - Agendamento de cobranças (mensal, trimestral, etc.)
- `contract_invoices` - Faturas geradas
- `payment_receipts` - Comprovantes de pagamento (upload de arquivos)
- `billing_audit_log` - Log de auditoria de operações financeiras

**Relacionamentos:** contract → billing_schedule → invoices → receipts

---

### 3. Fluxos de Negócio

#### `fluxo_home_care.drawio`
**Descrição:** Fluxo completo do processo de negócio Home Care
**Conteúdo:**
1. **Comercial:** Cadastro de cliente → Criação de contrato → Adição de vidas → Definição de serviços
2. **Equipe Médica:** Solicitação de autorização → Aprovação/rejeição
3. **Execução:** Agendamento → Execução de serviços → Registro de checklist
4. **Financeiro:** Geração de faturas → Cobrança → Recebimento de pagamentos

**Controles Automáticos:**
- Verificação de limites de serviços
- Alertas de violação
- Rastreamento de uso

**Como usar:** Ideal para entender o ciclo de vida completo de um contrato Home Care.

---

### 4. Frontend

#### `mapa_frontend.drawio`
**Descrição:** Mapa completo da estrutura do frontend React
**Conteúdo:**
- **Estrutura de Rotas:** App.jsx → AdminLayout → Páginas protegidas
- **Módulos de Páginas:**
  - Dashboard
  - Cadastros (empresas, estabelecimentos, clientes, usuários, perfis, menus)
  - Home Care (contratos, vidas, serviços, autorizações médicas, relatórios)
  - Financeiro (dashboard, faturas, B2B, planos)
- **Componentes Compartilhados:**
  - Forms (CompanyForm, ClientForm, ContractForm, etc.)
  - Views/Details (CompanyDetails, ClientDetails, etc.)
  - UI Components (Button, Modal, DataTable, Breadcrumb, etc.)
- **Services:** Clientes HTTP para cada módulo (api.js, companiesService, contractsService, billingService, etc.)
- **Hooks:** Custom hooks (useCompanyForm, useBreadcrumbs, useDataTable, etc.)
- **Contexts:** AuthContext, ThemeContext

**Como usar:** Ideal para desenvolvedores frontend entenderem a organização dos componentes e rotas.

---

## 📊 Estatísticas do Sistema

### Backend
- **Linguagem:** Python 3.12 + FastAPI
- **Arquitetura:** Clean Architecture (Hexagonal)
- **API Endpoints:** 200+ (REST)
- **Routers:** 38 arquivos
- **Repositórios:** 15+
- **Serviços de Negócio:** 12+
- **Schemas Pydantic:** 15+

### Frontend
- **Framework:** React 18 + TypeScript
- **Páginas:** 27
- **Componentes:** 50+
- **Services (API Clients):** 15+
- **Custom Hooks:** 10+
- **Contexts:** 2 (Auth, Theme)
- **Roteamento:** React Router v6
- **UI:** TailwindCSS + Flowbite

### Banco de Dados
- **SGBD:** PostgreSQL 14+
- **Schema:** `master`
- **Tabelas:** 45
- **Foreign Keys:** 96 relacionamentos
- **Migrations:** 17 arquivos Alembic

### Segurança
- **Autenticação:** JWT (JSON Web Tokens)
- **Autorização:** Sistema de permissões granulares
  - 19 Roles (perfis de acesso)
  - 215 Permissions (permissões específicas)
  - Contextos: system, company, establishment
- **Multi-tenant:** Isolamento por `company_id`
- **Cache:** Redis para performance de permissões

### Integrações
- **PagBank:** Gateway de pagamentos (cobranças recorrentes, checkout)
- **Geolocalização:** APIs de geocoding para endereços

---

## 🎯 Como Usar os Diagramas

### Para Desenvolvedores Novos no Projeto
1. **Comece por:** `arquitetura_sistema.drawio` (visão geral)
2. **Depois:** `mapa_frontend.drawio` OU ERDs por módulo (dependendo do seu foco)
3. **Aprofunde:** `fluxo_home_care.drawio` para entender regras de negócio

### Para Arquitetos/Tech Leads
1. **Arquitetura:** `arquitetura_sistema.drawio`
2. **Modelo de Dados Completo:** Todos os ERDs (`erd_*.drawio`)
3. **Fluxos Críticos:** `fluxo_home_care.drawio`

### Para Product Owners/Gestores
1. **Fluxo de Negócio:** `fluxo_home_care.drawio`
2. **Mapa de Funcionalidades:** `mapa_frontend.drawio` (páginas disponíveis)

---

## 🛠️ Ferramentas Necessárias

Para abrir e editar os diagramas:

### Opção 1: Draw.io Desktop (Recomendado)
- Download: https://github.com/jgraph/drawio-desktop/releases
- Gratuito e open-source
- Funciona offline

### Opção 2: Draw.io Online
- Acesse: https://app.diagrams.net/
- Abra os arquivos `.drawio` diretamente
- Não requer instalação

### Opção 3: VS Code Extension
- Extensão: "Draw.io Integration" (hediet.vscode-drawio)
- Permite editar `.drawio` diretamente no VS Code

---

## 📝 Manutenção dos Diagramas

### Quando Atualizar

Os diagramas devem ser atualizados quando:
- **ERD:** Novas tabelas ou relacionamentos forem criados (migrations)
- **Arquitetura:** Novas camadas ou componentes principais forem adicionados
- **Frontend:** Novas páginas ou módulos forem implementados
- **Fluxo:** Regras de negócio mudarem significativamente

### Como Atualizar

1. Abra o arquivo `.drawio` no Draw.io
2. Edite visualmente conforme necessário
3. Salve o arquivo
4. Commit no repositório com mensagem descritiva

---

## 📌 Observações Importantes

### Limitações Conhecidas
- **ERD Completo em um único arquivo:** Devido à complexidade (45 tabelas), os ERDs foram divididos por módulo para melhor legibilidade
- **Relacionamentos Cruzados:** Alguns relacionamentos entre módulos não estão visíveis nos ERDs individuais (consultar `models.py` para detalhes completos)

### Próximos Passos (Sugestões)
- [ ] Criar diagrama de sequência para autenticação JWT
- [ ] Adicionar diagrama de deployment (infraestrutura/servidores)
- [ ] Criar diagrama C4 Model completo (Context, Containers, Components, Code)
- [ ] Documentar integrações externas (APIs de terceiros)

---

## 📧 Contato

Para dúvidas sobre os diagramas ou sugestões de melhoria, entre em contato com a equipe de arquitetura.

---

**Gerado automaticamente por Claude Code em 2025-01-01**
**Última atualização:** 2025-01-01
