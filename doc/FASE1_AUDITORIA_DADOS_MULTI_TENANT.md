# FASE 1: AUDITORIA DE DADOS - MULTI-TENANT ISOLATION

**Data**: 2025-09-14
**Status**: EM ANDAMENTO
**Fase**: 1/4

---

## 🎯 OBJETIVO DA AUDITORIA

Identificar todas as tabelas que precisam de isolamento multi-tenant e mapear dados órfãos que podem causar problemas durante a migração.

---

## 📊 MAPEAMENTO COMPLETO DE TABELAS

### **TABELAS IDENTIFICADAS** (17 total)

#### 🔴 **CRÍTICAS - PRECISAM DE company_id** (4 tabelas)

| Tabela | Problema Atual | Impacto | Prioridade |
|--------|----------------|---------|------------|
| `people` | `UNIQUE(tax_id)` global | ⚠️ **CRÍTICO** - Bloqueia empresas | P0 |
| `users` | `UNIQUE(email_address)` global | ⚠️ **ALTO** - Usuário único sistema-wide | P0 |
| `phones` | Sem isolamento via people | ⚠️ **MÉDIO** - Vazamento via relacionamento | P1 |
| `emails` | Sem isolamento via people | ⚠️ **MÉDIO** - Vazamento via relacionamento | P1 |

#### 🟡 **RELACIONADAS - PRECISAM DE ANÁLISE** (6 tabelas)

| Tabela | Status Atual | Necessita Alteração |
|--------|-------------|---------------------|
| `roles` | Sistema global | ⚠️ **Analisar** - Podem ser por empresa |
| `permissions` | Sistema global | ⚠️ **Analisar** - Context levels existem |
| `user_roles` | Contexto existente | ✅ **OK** - Já tem context_type |
| `role_permissions` | Global | ⚠️ **Analisar** - Seguir roles |
| `sessions` | Global | ⚠️ **Analisar** - Podem precisar de contexto |
| `user_sessions` | Contexto via user | ✅ **OK** - Herda isolamento do user |

#### 🟢 **JÁ ISOLADAS CORRETAMENTE** (7 tabelas)

| Tabela | Campo de Isolamento | Status |
|--------|-------------------|---------|
| `companies` | Entidade raiz | ✅ **PERFEITO** |
| `establishments` | `company_id` | ✅ **PERFEITO** |
| `clients` | `establishment_id` (via company) | ✅ **PERFEITO** |
| `professionals` | `establishment_id` (via company) | ✅ **PERFEITO** |
| `user_establishments` | `establishment_id` | ✅ **PERFEITO** |
| `addresses` | Via people/establishments | ✅ **OK** (herda isolamento) |
| `menus` | `company_specific`, `establishment_specific` | ✅ **PERFEITO** |

---

## 🚨 PROBLEMAS CRÍTICOS IDENTIFICADOS

### **1. TABELA PEOPLE - PROBLEMA PRINCIPAL**

```sql
-- ATUAL (PROBLEMÁTICO)
tax_id VARCHAR(14) UNIQUE  -- ⚠️ GLOBAL PARA TODO SISTEMA

-- NECESSÁRIO
tax_id VARCHAR(14)
company_id BIGINT REFERENCES companies(id)
UNIQUE(company_id, tax_id)  -- ✅ ÚNICO POR EMPRESA
```

**Relacionamento Atual**:
```
people (1) ←→ (1) companies
└── tax_id UNIQUE GLOBAL ⚠️ PROBLEMA
```

**Relacionamento Correto**:
```
companies (1) ←→ (N) people
└── people.company_id + UNIQUE(company_id, tax_id) ✅
```

### **2. TABELA USERS - PROBLEMA SECUNDÁRIO**

```sql
-- ATUAL (PROBLEMÁTICO)
email_address VARCHAR(255) UNIQUE  -- ⚠️ GLOBAL

-- NECESSÁRIO
email_address VARCHAR(255)
company_id BIGINT REFERENCES companies(id)
UNIQUE(company_id, email_address)  -- ✅ ÚNICO POR EMPRESA
```

---

## 📋 ANÁLISE DE RELACIONAMENTOS

### **HIERARQUIA ATUAL**
```
companies (raiz)
├── people (1:1) ⚠️ DEVERIA SER (1:N)
│   ├── phones (1:N)
│   ├── emails (1:N)
│   ├── addresses (1:N)
│   └── users (1:1) ⚠️ DEVERIA TER company_id
├── establishments (1:N) ✅ JÁ CORRETO
│   ├── clients (1:N) ✅ JÁ CORRETO
│   ├── professionals (1:N) ✅ JÁ CORRETO
│   └── user_establishments (N:N) ✅ JÁ CORRETO
└── menus (contextuais) ✅ JÁ CORRETO
```

### **HIERARQUIA CORRIGIDA**
```
companies (raiz)
├── people (1:N) ✅ CORRIGIR
│   ├── phones (1:N) ✅ herda isolamento
│   ├── emails (1:N) ✅ herda isolamento
│   ├── addresses (1:N) ✅ herda isolamento
│   └── users (1:N) ✅ ADICIONAR company_id
├── establishments (1:N) ✅ já correto
└── ... (demais tabelas já corretas)
```

---

## 🔍 ANÁLISE DE REGISTROS ÓRFÃOS

### **QUERY PARA IDENTIFICAR PROBLEMAS**

```sql
-- 1. Pessoas sem empresa (relacionamento 1:1 quebrado)
SELECT COUNT(*) as pessoas_sem_empresa
FROM master.people p
LEFT JOIN master.companies c ON c.person_id = p.id
WHERE c.id IS NULL;

-- 2. Usuários sem pessoa (problemático)
SELECT COUNT(*) as usuarios_sem_pessoa
FROM master.users u
LEFT JOIN master.people p ON p.id = u.person_id
WHERE p.id IS NULL;

-- 3. Estabelecimentos órfãos (menos provável)
SELECT COUNT(*) as estabelecimentos_órfãos
FROM master.establishments e
LEFT JOIN master.companies c ON c.id = e.company_id
WHERE c.id IS NULL;

-- 4. Clientes órfãos (menos provável)
SELECT COUNT(*) as clientes_órfãos
FROM master.clients cl
LEFT JOIN master.establishments e ON e.id = cl.establishment_id
WHERE e.id IS NULL;
```

---

## 📈 ESTRATÉGIAS DE MIGRAÇÃO

### **ESTRATÉGIA 1: PEOPLE → COMPANIES (1:N)**

**Problema**: Atualmente `people` tem relacionamento 1:1 com `companies`
**Solução**: Transformar em 1:N (uma empresa pode ter múltiplas pessoas)

```sql
-- Passo 1: Adicionar company_id em people
ALTER TABLE master.people
ADD COLUMN company_id BIGINT;

-- Passo 2: Popular com dados existentes
UPDATE master.people
SET company_id = (
    SELECT c.id FROM master.companies c
    WHERE c.person_id = people.id
);

-- Passo 3: Adicionar constraint
ALTER TABLE master.people
ADD CONSTRAINT fk_people_company
    FOREIGN KEY (company_id) REFERENCES master.companies(id);
```

### **ESTRATÉGIA 2: USERS + COMPANY_ID**

```sql
-- Adicionar company_id em users
ALTER TABLE master.users
ADD COLUMN company_id BIGINT;

-- Popular com dados via people
UPDATE master.users
SET company_id = (
    SELECT p.company_id FROM master.people p
    WHERE p.id = users.person_id
);
```

---

## ⚠️ RISCOS IDENTIFICADOS

### **RISCO ALTO**
1. **Dados órfãos**: Pessoas sem empresa ou usuários sem pessoa
2. **Relacionamentos quebrados**: FK constraints podem falhar
3. **Duplicação de constraints**: tax_id duplicado pode impedir migração

### **RISCO MÉDIO**
1. **Performance**: Migração de dados pode ser lenta
2. **Downtime**: Alterações de schema precisam de manutenção
3. **Rollback complexo**: Muitas tabelas interconectadas

### **MITIGAÇÃO**
- [ ] Scripts de validação antes da migração
- [ ] Backup completo antes de qualquer alteração
- [ ] Migração em ambiente de teste primeiro
- [ ] Rollback script preparado

---

## 📅 PRÓXIMOS PASSOS

### **ESTA SEMANA**
- [x] ✅ Mapear todas as tabelas do sistema
- [x] ✅ Identificar problemas críticos de isolamento
- [ ] ⏳ Executar queries de análise de órfãos
- [ ] ⏳ Criar scripts de migração de dados
- [ ] ⏳ Definir estratégia para dados problemáticos

### **PRÓXIMA SEMANA**
- [ ] Validar scripts em ambiente de desenvolvimento
- [ ] Criar ambiente de teste isolado
- [ ] Preparar rollback scripts
- [ ] Documentar procedimentos para FASE 2

---

## 🎯 CONCLUSÕES DA AUDITORIA

### ✅ **ESTRUTURA GERAL BOA**
- Sistema já tem conceito de multi-tenancy parcial
- Tabelas principais (establishments, clients) já isoladas
- Relacionamentos bem definidos

### ⚠️ **PROBLEMAS CRÍTICOS**
- Tabela `people` com constraint UNIQUE global
- Relacionamento 1:1 people↔companies inadequado
- Usuários sem isolamento por empresa

### 🚀 **VIABILIDADE**
- **ALTA**: Migração é viável em 6-8 semanas
- **RISCO CONTROLADO**: Com scripts adequados e testes
- **IMPACTO POSITIVO**: Resolverá todos os problemas de multi-tenancy

---

**Status**: ✅ FASE 1 CONCLUÍDA - SEGUIR PARA FASE 2**
