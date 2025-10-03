# 📊 Índice Visual - Diagramas Pro Team Care

**Gerado em:** 2025-01-01
**Total de Diagramas:** 8 arquivos `.drawio`
**Tamanho Total:** ~98 KB

---

## 🗂️ Lista Rápida de Arquivos

| # | Arquivo | Tamanho | Descrição Curta |
|---|---------|---------|-----------------|
| 1 | `arquitetura_sistema.drawio` | 17 KB | **Arquitetura Clean Architecture completa** |
| 2 | `erd_core.drawio` | 12 KB | **ERD: Autenticação e Permissões** (8 tabelas) |
| 3 | `erd_multi-tenant.drawio` | 4.9 KB | **ERD: Multi-tenant** (2 tabelas) |
| 4 | `erd_cadastros.drawio` | 13 KB | **ERD: Cadastros Base** (6 tabelas) |
| 5 | `erd_home_care_contratos.drawio` | 9.2 KB | **ERD: Contratos e Serviços** (5 tabelas) |
| 6 | `erd_financeiro_contratos.drawio` | 6.9 KB | **ERD: Faturamento** (4 tabelas) |
| 7 | `fluxo_home_care.drawio` | 12 KB | **Fluxo de Negócio Home Care** (11 etapas) |
| 8 | `mapa_frontend.drawio` | 23 KB | **Mapa Frontend React** (27 páginas, 50+ componentes) |

---

## 🎯 Guia de Uso Rápido

### "Preciso entender a arquitetura geral"
👉 Abra: **`arquitetura_sistema.drawio`**

### "Preciso ver as tabelas do banco de dados"
👉 Abra os ERDs por módulo:
- `erd_core.drawio` (usuários, permissões)
- `erd_multi-tenant.drawio` (empresas, estabelecimentos)
- `erd_cadastros.drawio` (pessoas, clientes)
- `erd_home_care_contratos.drawio` (contratos, vidas, serviços)
- `erd_financeiro_contratos.drawio` (faturas, pagamentos)

### "Preciso entender como funciona o Home Care"
👉 Abra: **`fluxo_home_care.drawio`**

### "Preciso ver a estrutura do frontend"
👉 Abra: **`mapa_frontend.drawio`**

---

## 📈 Resumo Visual por Tipo

```
ARQUITETURA (1 diagrama)
└── arquitetura_sistema.drawio ..................... Visão macro do sistema

MODELO DE DADOS - ERD (5 diagramas modulares)
├── erd_core.drawio .............................. Users, Roles, Permissions
├── erd_multi-tenant.drawio ...................... Companies, Establishments
├── erd_cadastros.drawio ......................... People, Clients, Contacts
├── erd_home_care_contratos.drawio ............... Contracts, Lives, Services
└── erd_financeiro_contratos.drawio .............. Invoices, Payments, Receipts

FLUXOS DE NEGÓCIO (1 diagrama)
└── fluxo_home_care.drawio ....................... Jornada Cliente → Faturamento

FRONTEND (1 diagrama)
└── mapa_frontend.drawio ......................... Rotas, Componentes, Services
```

---

## 🔍 Busca Rápida por Entidade

**Procurando informações sobre...**

### Autenticação/Usuários
- Diagrama: `erd_core.drawio` + `arquitetura_sistema.drawio`
- Tabelas: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`

### Empresas/Estabelecimentos
- Diagrama: `erd_multi-tenant.drawio` + `arquitetura_sistema.drawio`
- Tabelas: `companies`, `establishments`

### Clientes
- Diagrama: `erd_cadastros.drawio` + `fluxo_home_care.drawio`
- Tabelas: `people`, `clients`, `phones`, `emails`, `addresses`

### Contratos Home Care
- Diagrama: `erd_home_care_contratos.drawio` + `fluxo_home_care.drawio`
- Tabelas: `contracts`, `contract_lives`, `contract_services`, `services_catalog`

### Faturamento
- Diagrama: `erd_financeiro_contratos.drawio` + `fluxo_home_care.drawio`
- Tabelas: `contract_invoices`, `payment_receipts`, `contract_billing_schedules`

### Frontend/Páginas
- Diagrama: `mapa_frontend.drawio` + `arquitetura_sistema.drawio`
- Módulos: Dashboard, Cadastros, Home Care, Financeiro

---

## 📊 Estatísticas dos Diagramas

### ERD - Modelo de Dados
- **Total de Tabelas Documentadas:** 25 tabelas (principais)
- **Total de Tabelas no Sistema:** 45 tabelas
- **Relacionamentos (Foreign Keys):** 96 relacionamentos
- **Módulos Organizados:** 5 módulos distintos

### Arquitetura
- **Camadas Documentadas:** 4 (Presentation, Application, Infrastructure, Domain)
- **Endpoints API:** 200+ documentados
- **Routers:** 38 arquivos
- **Componentes Frontend:** 50+ documentados

### Fluxo de Negócio
- **Etapas Principais:** 11 processos
- **Atores Envolvidos:** 4 (Comercial, Médico, Execução, Financeiro)
- **Decisões Críticas:** 2 pontos de decisão
- **Loops/Ciclos:** 1 ciclo de execução contínua

---

## 🛠️ Como Abrir os Diagramas

### Método 1: Draw.io Desktop (Recomendado)
```bash
# Baixe em: https://github.com/jgraph/drawio-desktop/releases
# Depois:
drawio doc/arquitetura_sistema.drawio
```

### Método 2: Draw.io Online
1. Acesse: https://app.diagrams.net/
2. Clique em "Open Existing Diagram"
3. Selecione o arquivo `.drawio` desejado

### Método 3: VS Code Extension
```bash
# Instale a extensão "Draw.io Integration"
code --install-extension hediet.vscode-drawio
# Depois abra os arquivos .drawio diretamente no VS Code
```

---

## 📝 Notas Importantes

### ⚠️ Limitações
- Os ERDs foram divididos em 5 arquivos para facilitar a leitura
- Alguns relacionamentos cruzados entre módulos não estão visíveis nos diagramas individuais
- Para ver o modelo completo de dados: consultar `app/infrastructure/orm/models.py`

### ✅ Vantagens da Divisão Modular
- Facilita manutenção (atualizar apenas o módulo afetado)
- Melhora legibilidade (evita diagramas gigantes)
- Acelera carregamento (arquivos menores)
- Permite foco por área de interesse

### 🔄 Atualização
Estes diagramas devem ser atualizados quando:
- Novas tabelas ou relacionamentos forem criados (ERDs)
- Novas camadas ou módulos forem adicionados (Arquitetura)
- Regras de negócio mudarem (Fluxos)
- Novas páginas ou componentes principais forem criados (Frontend)

---

## 📖 Documentação Adicional

- **README Principal:** `DIAGRAMAS_README.md` (documentação detalhada)
- **Código-Fonte:** `app/infrastructure/orm/models.py` (definição completa das tabelas)
- **Migrações:** `alembic/versions/*.py` (histórico de mudanças no banco)
- **Rotas API:** `app/presentation/api/v1/*.py` (endpoints disponíveis)

---

**Dica:** Para navegação rápida, mantenha este arquivo aberto enquanto trabalha com os diagramas!

---

_Gerado automaticamente por Claude Code - Pro Team Care © 2025_
