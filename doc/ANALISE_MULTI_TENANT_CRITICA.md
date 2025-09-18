# ANÁLISE CRÍTICA: PROBLEMAS DE MULTI-TENANCY NO SISTEMA PRO TEAM CARE

## 🚨 STATUS: CRÍTICO - VIOLAÇÃO DOS PRINCÍPIOS SAAS MULTI-TENANT

Data da Análise: 2025-09-14
Analista: Claude Code
Severidade: **CRÍTICA**

---

## 🔍 RESUMO EXECUTIVO

O sistema **Pro Team Care** apresenta uma **violação fundamental dos princípios de Multi-Tenancy** em um ambiente SaaS. A arquitetura atual permite **vazamento de dados entre empresas** (tenants) devido à ausência de isolamento adequado, particularmente na tabela `people` que possui constraint UNIQUE global no campo `tax_id`.

### ⚠️ RISCO IMEDIATO
- **Vazamento de Dados**: Empresas podem ver informações de clientes de outras empresas
- **Bloqueio de Negócios**: Uma empresa impede outras de cadastrar o mesmo CPF/CNPJ
- **Violação LGPD**: Compartilhamento não autorizado de dados pessoais
- **Compliance**: Não atende requisitos de isolamento para SaaS B2B

---

## 🏗️ ARQUITETURA ATUAL (PROBLEMÁTICA)

### Estrutura Identificada

```
master.people (TABELA CENTRAL - PROBLEMA CRÍTICO)
├── id (PK)
├── tax_id (STRING(14), UNIQUE GLOBAL) ⚠️ PROBLEMA
├── name, trade_name, person_type...
└── [SEM ISOLAMENTO POR TENANT]

master.companies
├── id (PK)
├── person_id (FK -> people.id, UNIQUE)
└── [TENANT RAIZ - MAS SEM ISOLAMENTO EFETIVO]

master.establishments
├── id (PK)
├── company_id (FK -> companies.id)
├── person_id (FK -> people.id)
└── code (UNIQUE PER company_id) ✓ CORRETO

master.clients
├── id (PK)
├── person_id (FK -> people.id)
├── establishment_id (FK -> establishments.id)
├── client_code (UNIQUE PER establishment_id) ✓ CORRETO
└── CONSTRAINT: UNIQUE(establishment_id, person_id) ✓ CORRETO

master.users
├── id (PK)
├── person_id (FK -> people.id)
├── email_address (UNIQUE GLOBAL) ⚠️ PROBLEMA SECUNDÁRIO
└── [SEM ISOLAMENTO DIRETO]
```

---

## 🛑 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **CONSTRAINT UNIQUE GLOBAL NO TAX_ID**

**Localização**: `master.people.tax_id`
```sql
-- PROBLEMÁTICO: Constraint atual
UniqueConstraint("tax_id", name="people_tax_id_unique")
```

**Problema**:
- Um CPF/CNPJ só pode existir uma vez em todo o sistema
- Empresas diferentes não podem ter o mesmo cliente (ex: fornecedor comum)
- Viola princípios básicos de Multi-Tenancy

**Cenário Real**:
```
Empresa A: Quer cadastrar cliente "João Silva - CPF 123.456.789-00"
Empresa B: Já cadastrou "João Silva - CPF 123.456.789-00"
Resultado: ❌ Empresa A é bloqueada de cadastrar seu próprio cliente
```

### 2. **AUSÊNCIA DE COMPANY_ID NA TABELA PEOPLE**

A tabela `people` não possui campo `company_id`, impossibilitando:
- Isolamento por tenant
- Row-Level Security
- Consultas restritas ao contexto da empresa

### 3. **EMAIL GLOBAL ÚNICO EM USERS**

```sql
UniqueConstraint("email_address", name="users_email_unique")
```

**Problema**: Mesmo email não pode ser reutilizado entre empresas diferentes.

---

## 💼 IMPACTOS NO NEGÓCIO

### Cenários Problemáticos Reais

1. **Fornecedor Comum**
   - Hospital A e Hospital B querem cadastrar a mesma empresa farmacêutica
   - Apenas um hospital consegue cadastrar
   - O segundo recebe erro de "CNPJ já existe"

2. **Cliente Multi-Estabelecimento**
   - Paciente atendido em múltiplas clínicas independentes
   - Apenas a primeira clínica consegue cadastrar
   - Outras clínicas são impedidas de prestar atendimento

3. **Fusões e Aquisições**
   - Empresa adquirida não pode manter seus clientes
   - Dados ficam "presos" na empresa original

4. **Consultórios Médicos**
   - Médico com consultório próprio + trabalho em hospital
   - Não pode ser cadastrado em ambos os locais

---

## 🔒 IMPACTOS DE SEGURANÇA E COMPLIANCE

### LGPD (Lei Geral de Proteção de Dados)
- **Art. 46**: Dados devem ser tratados apenas pelo controlador autorizado
- **Vazamento**: Empresa A pode descobrir clientes da Empresa B
- **Consentimento**: Cliente consentiu com Empresa A, não com B

### ISO 27001 / SOC2
- **Isolamento de Dados**: Requisito fundamental não atendido
- **Controle de Acesso**: Falha na segregação de tenants
- **Auditoria**: Rastros de acesso misturados entre empresas

### Riscos Jurídicos
- Ações por vazamento de dados comerciais
- Multas LGPD (até 2% do faturamento)
- Perda de certificações de segurança

---

## 🏢 ANÁLISE MULTI-TENANT: COMO DEVERIA SER

### Padrão Adequado para SaaS B2B

```sql
-- SOLUÇÃO 1: ROW-LEVEL SECURITY (RECOMENDADA)
master.people
├── id (PK)
├── company_id (FK -> companies.id) ✓ ISOLAMENTO
├── tax_id (STRING(14))
├── CONSTRAINT: UNIQUE(company_id, tax_id) ✓ CORRETO
└── RLS Policy: WHERE company_id = current_company_context()

master.users
├── id (PK)
├── person_id (FK -> people.id)
├── company_id (FK -> companies.id) ✓ ISOLAMENTO
├── email_address (STRING)
└── CONSTRAINT: UNIQUE(company_id, email_address) ✓ CORRETO
```

### Benefícios da Correção

1. **Isolamento Completo**
   - Cada empresa vê apenas seus dados
   - Zero vazamento entre tenants

2. **Flexibilidade de Negócio**
   - Fornecedores podem atender múltiplas empresas
   - Clientes podem ser atendidos em diferentes estabelecimentos

3. **Compliance Automático**
   - LGPD: Dados tratados apenas pelo controlador correto
   - Auditoria: Logs separados por empresa

4. **Escalabilidade**
   - Performance isolada por tenant
   - Backup e restore por empresa

---

## 📊 ESTRATÉGIAS DE CORREÇÃO

### 🥇 OPÇÃO 1: ROW-LEVEL SECURITY (RECOMENDADA)

**Complexidade**: Média
**Impacto**: Médio
**Benefícios**: Alto

#### Implementação:
1. Adicionar `company_id` em tabelas críticas
2. Alterar constraints UNIQUE para incluir `company_id`
3. Implementar RLS policies
4. Atualizar queries da aplicação

```sql
-- Exemplo de migração
ALTER TABLE master.people ADD COLUMN company_id BIGINT;
ALTER TABLE master.people ADD CONSTRAINT fk_people_company
  FOREIGN KEY (company_id) REFERENCES master.companies(id);

DROP CONSTRAINT people_tax_id_unique;
ADD CONSTRAINT people_company_tax_id_unique
  UNIQUE(company_id, tax_id);
```

### 🥈 OPÇÃO 2: SCHEMA POR TENANT

**Complexidade**: Alta
**Impacto**: Alto
**Benefícios**: Muito Alto

- `company_123.people`, `company_456.people`
- Isolamento total de dados
- Backup/restore por empresa
- Mais complexo de gerenciar

### 🥉 OPÇÃO 3: DATABASE POR TENANT

**Complexidade**: Muito Alta
**Impacto**: Muito Alto
**Benefícios**: Máximo

- Cada empresa uma base separada
- Isolamento completo
- Custoso de manter
- Adequado apenas para clientes enterprise

---

## ⚡ PLANO DE CORREÇÃO RECOMENDADO

### FASE 1: ANÁLISE E PREPARAÇÃO (1-2 semanas)
- [ ] Mapear todas as tabelas com dados compartilhados
- [ ] Identificar queries que precisam de company_context
- [ ] Planejar migração de dados existentes
- [ ] Criar ambiente de teste isolado

### FASE 2: IMPLEMENTAÇÃO CORE (2-3 semanas)
- [ ] Adicionar company_id em tabelas críticas
- [ ] Migrar constraints UNIQUE globais
- [ ] Implementar RLS policies
- [ ] Atualizar models e repositories

### FASE 3: APLICAÇÃO E TESTES (1-2 semanas)
- [ ] Atualizar todas as queries
- [ ] Implementar middleware de contexto
- [ ] Testes de isolamento rigorosos
- [ ] Validação de compliance

### FASE 4: MIGRAÇÃO DE DADOS (1 semana)
- [ ] Script de migração de dados existentes
- [ ] Associar dados órfãos às empresas corretas
- [ ] Validação de integridade
- [ ] Rollback plan

---

## 🎯 PRÓXIMOS PASSOS CRÍTICOS

### IMEDIATO (Próximos 2 dias)
1. **Avaliar Exposição Atual**: Verificar se já houve vazamento de dados
2. **Implementar Workaround**: Adicionar filtros manuais nas consultas críticas
3. **Documentar Casos**: Mapear todos os cenários de negócio afetados

### CURTO PRAZO (2 semanas)
1. **Aprovação Executiva**: Apresentar análise e obter budget
2. **Montar Equipe**: Definir responsáveis técnicos
3. **Planejar Downtime**: Migração pode exigir manutenção

### MÉDIO PRAZO (1-2 meses)
1. **Implementar Solução Completa**
2. **Migrar Dados Existentes**
3. **Certificar Compliance**

---

## 💰 ESTIMATIVA DE IMPACTO

### Custo da NÃO Correção
- **Multas LGPD**: R$ 50.000 - R$ 50.000.000
- **Perda de Clientes**: Empresas abandonam por falta de isolamento
- **Reputação**: Marca prejudicada por problemas de segurança
- **Legal**: Processos por vazamento de dados comerciais

### Custo da Correção
- **Desenvolvimento**: 80-120 horas (R$ 40.000 - R$ 60.000)
- **Infraestrutura**: Mínimo (usar recursos existentes)
- **Risco**: Controlado com testes adequados

### ROI
**Retorno do investimento imediato** através de:
- Compliance automático
- Capacidade de expandir customer base
- Redução de riscos jurídicos
- Melhoria na experiência do cliente

---

## ✅ CONCLUSÕES E RECOMENDAÇÕES

### ⚠️ URGÊNCIA MÁXIMA
Esta correção deve ser tratada como **PRIORIDADE 0** por:

1. **Risco Jurídico**: Violação ativa da LGPD
2. **Risco de Negócio**: Perda de competitividade
3. **Risco Técnico**: Arquitetura insustentável
4. **Risco Reputacional**: Perda de confiança do mercado

### 🎯 RECOMENDAÇÃO FINAL

**Implementar OPÇÃO 1 (Row-Level Security)** imediatamente:

✅ **Prós**:
- Correção fundamental do problema
- Implementação em 4-6 semanas
- Custo controlado
- Mantém compatibilidade com código existente

❌ **Contras**:
- Requer migração de dados
- Downtime para alterações de schema
- Testes extensivos necessários

---

## 📞 CONTATO E SUPORTE

**Documento preparado por**: Claude Code
**Data**: 2025-09-14
**Versão**: 1.0
**Classificação**: CONFIDENCIAL - ANÁLISE TÉCNICA

**Para dúvidas técnicas sobre esta análise:**
- Revisar documentação em `/doc/`
- Consultar modelos em `/app/infrastructure/orm/models.py`
- Analisar constraints em banco de dados

---

**⚡ AÇÃO REQUERIDA: Este documento requer análise e aprovação executiva imediata para início da correção.**
