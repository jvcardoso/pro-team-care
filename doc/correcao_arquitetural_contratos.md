# CORREÇÃO ARQUITETURAL: SEPARAÇÃO DE CONTRATOS

## 🔍 PROBLEMA IDENTIFICADO

O sistema atual tem **2 tipos de contratos distintos** sendo tratados de forma inadequada:

### 1. Contratos Home Care (B2C)
**Fluxo**: `Company → Establishment → Client → Contract`
- **Natureza**: Prestação de serviços de home care
- **Cobrança**: Clientes pagam pelos serviços home care
- **Volume**: Muitos contratos por establishment
- **Valor**: Relativamente baixo por contrato

### 2. Contratos SaaS (B2B)
**Fluxo**: `Company → CompanySubscription`
- **Natureza**: Assinatura do software Pro Team Care
- **Cobrança**: Empresas pagam pelo uso do sistema
- **Volume**: 1 contrato por company (podem ter vários establishments)
- **Valor**: Maior valor, baseado em quantidade de establishments

## 🚨 PROBLEMA ATUAL

O sistema de **billing implementado está direcionado para `Contract` (Home Care)** quando deveria ser direcionado para **`CompanySubscription` (SaaS)**.

### Análise da Implementação Atual:

```python
# ❌ INCORRETO - Billing aponta para contratos home care
class ContractBillingSchedule(Base):
    contract_id = Column(BigInteger, ForeignKey("master.contracts.id"))

# ✅ CORRETO - Já existe mas não é usado pelo billing
class CompanySubscription(Base):
    company_id = Column(BigInteger, ForeignKey("master.companies.id"))
    plan_id = Column(BigInteger)
    payment_method = Column("manual", "recurrent")  # JÁ TEM!
```

## 🎯 SOLUÇÃO ARQUITETURAL

### Opção 1: Refatoração Completa (Recomendada)

**1.1 Renomear tabelas existentes**
```sql
-- Billing atual (home care) vira específico
ALTER TABLE master.contract_billing_schedules
RENAME TO homecare_billing_schedules;

ALTER TABLE master.contract_invoices
RENAME TO homecare_invoices;
```

**1.2 Criar novo billing para SaaS**
```sql
-- Novo billing para assinaturas SaaS
CREATE TABLE master.saas_billing_schedules (
    id BIGINT PRIMARY KEY,
    company_subscription_id BIGINT REFERENCES master.company_subscriptions(id),
    billing_method VARCHAR(20) DEFAULT 'manual',
    pagbank_subscription_id VARCHAR(100),
    pagbank_customer_id VARCHAR(100),
    -- ... demais campos
);

CREATE TABLE master.saas_invoices (
    id BIGINT PRIMARY KEY,
    subscription_id BIGINT REFERENCES master.company_subscriptions(id),
    -- ... demais campos
);
```

**1.3 Atualizar todos os serviços**
- `SaasBillingRepository` para CompanySubscription
- `HomeCareBillingRepository` para Contract
- APIs separadas: `/api/v1/saas-billing/*` e `/api/v1/homecare-billing/*`

### Opção 2: Extensão Incremental (Mais Rápida)

**2.1 Manter estrutura atual + Adicionar nova**
```sql
-- Adicionar campos para identificar tipo de cobrança
ALTER TABLE master.contract_billing_schedules
ADD COLUMN billing_context VARCHAR(20) DEFAULT 'homecare';

ALTER TABLE master.contract_billing_schedules
ADD COLUMN subscription_id BIGINT REFERENCES master.company_subscriptions(id);

-- Constraint para garantir exclusividade
ALTER TABLE master.contract_billing_schedules
ADD CONSTRAINT billing_context_check
CHECK (
    (billing_context = 'homecare' AND contract_id IS NOT NULL AND subscription_id IS NULL) OR
    (billing_context = 'saas' AND contract_id IS NULL AND subscription_id IS NOT NULL)
);
```

**2.2 Atualizar lógica de negócio**
```python
class BillingRepository:
    async def get_saas_billing_schedule(self, subscription_id: int):
        return await self.get_billing_schedule_by_subscription(subscription_id)

    async def get_homecare_billing_schedule(self, contract_id: int):
        return await self.get_billing_schedule_by_contract(contract_id)
```

## 🎯 RECOMENDAÇÃO: OPÇÃO 1 (REFATORAÇÃO)

### Justificativas:

1. **Clareza Arquitetural**: Separação clara entre SaaS e Home Care
2. **Manutenibilidade**: Código mais limpo e fácil de manter
3. **Escalabilidade**: Permite evoluir cada billing independentemente
4. **Performance**: Queries mais rápidas (tabelas menores e específicas)
5. **Regras de Negócio**: Lógicas distintas para cada tipo de cobrança

### Cronograma de Refatoração:

**Sprint 1: Preparação (3 dias)**
- [ ] Backup completo do sistema
- [ ] Criação das novas tabelas SaaS
- [ ] Migração de dados existentes
- [ ] Testes de integridade

**Sprint 2: Backend (5 dias)**
- [ ] `SaasBillingRepository`
- [ ] `SaasBillingService`
- [ ] APIs `/api/v1/saas-billing/*`
- [ ] Atualização do PagBank integration

**Sprint 3: Frontend (4 dias)**
- [ ] Componentes SaaS billing
- [ ] Separação das telas
- [ ] Integração com novas APIs
- [ ] Testes E2E

**Sprint 4: Migração e Cleanup (3 dias)**
- [ ] Migração gradual dos dados
- [ ] Deprecação das APIs antigas
- [ ] Cleanup do código legado
- [ ] Documentação final

## 🔧 IMPLEMENTAÇÃO DETALHADA

### Nova Estrutura de Tabelas:

```sql
-- ==========================================
-- SAAS BILLING TABLES (Company Subscriptions)
-- ==========================================

CREATE TABLE master.saas_billing_schedules (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    subscription_id BIGINT REFERENCES master.company_subscriptions(id) ON DELETE CASCADE,
    billing_cycle VARCHAR(20) NOT NULL DEFAULT 'MONTHLY',
    billing_day INTEGER NOT NULL DEFAULT 1,
    next_billing_date DATE NOT NULL,
    amount_per_cycle DECIMAL(10,2) NOT NULL,

    -- PagBank Integration
    billing_method VARCHAR(20) DEFAULT 'manual',
    pagbank_subscription_id VARCHAR(100),
    pagbank_customer_id VARCHAR(100),
    auto_fallback_enabled BOOLEAN DEFAULT TRUE,
    last_attempt_date DATE,
    attempt_count INTEGER DEFAULT 0,

    -- Audit
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by BIGINT REFERENCES master.users(id),

    CONSTRAINT saas_billing_method_check CHECK (billing_method IN ('recurrent', 'manual')),
    CONSTRAINT saas_billing_cycle_check CHECK (billing_cycle IN ('MONTHLY', 'QUARTERLY', 'ANNUAL')),
    CONSTRAINT saas_billing_day_check CHECK (billing_day >= 1 AND billing_day <= 31),
    UNIQUE (subscription_id)
);

CREATE TABLE master.saas_invoices (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    subscription_id BIGINT REFERENCES master.company_subscriptions(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,

    -- Período de Cobrança
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,

    -- Valores (baseado em establishments ativos)
    establishments_count INTEGER NOT NULL,
    base_amount DECIMAL(10,2) NOT NULL,
    additional_services_amount DECIMAL(10,2) DEFAULT 0.00,
    discounts DECIMAL(10,2) DEFAULT 0.00,
    taxes DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,

    -- Status e Pagamento
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    due_date DATE NOT NULL,
    issued_date DATE NOT NULL DEFAULT CURRENT_DATE,
    paid_date DATE,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    payment_notes TEXT,
    observations TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by BIGINT REFERENCES master.users(id),
    updated_by BIGINT REFERENCES master.users(id),

    CONSTRAINT saas_invoices_status_check CHECK (status IN ('pendente', 'enviada', 'paga', 'vencida', 'cancelada', 'em_atraso')),
    CONSTRAINT saas_invoices_establishments_count_check CHECK (establishments_count >= 0),
    CONSTRAINT saas_invoices_base_amount_check CHECK (base_amount >= 0),
    CONSTRAINT saas_invoices_total_amount_check CHECK (total_amount >= 0)
);

-- ==========================================
-- HOMECARE BILLING TABLES (Remain unchanged)
-- ==========================================
-- As tabelas contract_billing_schedules e contract_invoices
-- permanecem para billing de contratos home care

-- ==========================================
-- SHARED PAGBANK TRANSACTIONS
-- ==========================================
ALTER TABLE master.pagbank_transactions
ADD COLUMN billing_context VARCHAR(20) DEFAULT 'homecare';

ALTER TABLE master.pagbank_transactions
ADD COLUMN subscription_invoice_id BIGINT REFERENCES master.saas_invoices(id);

-- Constraint para garantir referência correta
ALTER TABLE master.pagbank_transactions
ADD CONSTRAINT pagbank_billing_context_check
CHECK (
    (billing_context = 'homecare' AND invoice_id IS NOT NULL AND subscription_invoice_id IS NULL) OR
    (billing_context = 'saas' AND invoice_id IS NULL AND subscription_invoice_id IS NOT NULL)
);
```

### Nova Lógica de Cálculo SaaS:

```python
class SaasBillingService:
    async def calculate_saas_invoice_amount(self, subscription_id: int) -> Decimal:
        """Calcular valor baseado na quantidade de establishments ativos"""

        # Buscar subscription
        subscription = await self.get_subscription(subscription_id)

        # Contar establishments ativos da company
        active_establishments = await self.count_active_establishments(subscription.company_id)

        # Calcular valor baseado no plano
        base_price_per_establishment = Decimal("99.90")  # Configurável
        total_amount = active_establishments * base_price_per_establishment

        # Aplicar desconto por volume
        if active_establishments >= 10:
            total_amount *= Decimal("0.85")  # 15% desconto
        elif active_establishments >= 5:
            total_amount *= Decimal("0.90")  # 10% desconto

        return total_amount
```

## 🚀 BENEFÍCIOS DA REFATORAÇÃO

1. **Billing SaaS Correto**: Companies pagam pelo uso do sistema
2. **Billing Home Care Independente**: Establishments podem ter billing próprio para seus clientes
3. **Métricas Precisas**: Dashboards separados para cada tipo de receita
4. **Escalabilidade**: Cada billing pode evoluir independentemente
5. **Manutenção**: Código mais limpo e específico
6. **Performance**: Queries otimizadas para cada contexto

## 📋 CHECKLIST DE MIGRAÇÃO

- [ ] **Análise de Impacto**: Identificar todos os pontos que referenciam billing atual
- [ ] **Backup Completo**: Dump do banco antes da migração
- [ ] **Criação das Novas Tabelas**: SQL da nova estrutura
- [ ] **Migração de Dados**: Scripts para mover dados existentes
- [ ] **Atualização de Repositories**: Separar SaaS e HomeCare
- [ ] **Atualização de Services**: Lógicas específicas para cada contexto
- [ ] **Atualização de APIs**: Endpoints separados
- [ ] **Atualização de Frontend**: Componentes específicos
- [ ] **Testes de Integração**: Validar ambos os billings
- [ ] **Documentação**: Atualizar docs e diagramas

---

**Esta refatoração é CRÍTICA para o negócio funcionar corretamente!**

O sistema atual cobra os contratos home care (clients) quando deveria cobrar as assinaturas SaaS (companies que usam o sistema).