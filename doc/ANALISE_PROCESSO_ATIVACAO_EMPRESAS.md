# Análise Completa: Processo de Ativação de Empresas e Usuários

## 📋 Sumário Executivo

Este documento apresenta a análise detalhada do sistema atual de ativação de empresas/usuários e propõe melhorias significativas para implementar um fluxo completo de **aceitação de contrato + criação de usuário gestor + ativação de acesso**.

---

## 🔍 Situação Atual

### ✅ O que já existe implementado

#### 1. **Sistema de Envio de Emails** (`app/infrastructure/services/email_service.py`)
- ✅ Serviço completo de envio de emails via SMTP
- ✅ Templates HTML responsivos para:
  - Email de ativação de conta
  - Email de reset de senha
- ✅ Geração de tokens seguros (`secrets.token_urlsafe(32)`)
- ✅ Validação de expiração de tokens (24h para ativação, 1h para reset)
- ✅ Modo simulado para desenvolvimento (sem SMTP real)

#### 2. **Modelo de Usuários** (`app/infrastructure/orm/models.py`)
Tabela `users` com campos completos:
```python
# Campos de ativação já existentes
status                    # 'active', 'inactive', 'pending', 'suspended', 'blocked'
activation_token          # Token único de ativação
activation_expires_at     # Expiração do token (24h)
invited_by_user_id        # Quem convidou
invited_at                # Data do convite
activated_at              # Data da ativação
context_type              # 'company', 'establishment', 'client'
```

#### 3. **Endpoints de Ativação** (`app/presentation/api/v1/user_activation.py`)
- ✅ `POST /invite-company-manager` - Convida gestor de empresa
- ✅ `POST /invite-establishment-manager` - Convida gestor de estabelecimento
- ✅ `POST /activate` - Ativa conta com token + define senha
- ✅ `POST /resend-activation` - Reenvia email de ativação
- ✅ `GET /validate-token/{token}` - Valida se token é válido

#### 4. **Use Cases Implementados** (`app/application/use_cases/user_management_use_case.py`)
- ✅ `create_company_manager()` - Cria usuário gestor + envia email
- ✅ `create_establishment_manager()` - Cria usuário de estabelecimento + envia email
- ✅ `activate_user()` - Ativa usuário com token + define senha
- ✅ `resend_activation_email()` - Reenvia email de ativação

#### 5. **Modelo de Empresa** (`master.companies`)
```sql
-- Campos existentes
id                  -- PK
person_id           -- FK para people (dados CNPJ, nome, etc)
settings            -- JSONB (configurações gerais)
metadata            -- JSONB (dados adicionais)
display_order       -- Ordem de exibição
created_at
updated_at
deleted_at
```

#### 6. **Modelo People** (`master.people`)
```sql
-- Campos LGPD já existentes
lgpd_consent_version         -- Versão do consentimento
lgpd_consent_given_at        -- Data do consentimento
lgpd_data_retention_expires_at
status                       -- 'active', 'inactive', 'pending', 'suspended', 'blocked'
```

---

## ❌ O que está faltando

### 1. **Campos Novos Necessários**

#### Tabela `companies` (ou `company_settings`)
```sql
-- Processo de ativação de empresa
access_status VARCHAR(20) DEFAULT 'pending_contract'
  -- Estados: 'pending_contract', 'contract_signed', 'pending_user', 'active', 'suspended'

contract_terms_version VARCHAR(10)
  -- Versão dos termos aceitos (ex: "1.0", "1.1")

contract_accepted_at TIMESTAMP
  -- Data da aceitação do contrato

contract_accepted_by VARCHAR(255)
  -- Email/nome de quem aceitou

contract_ip_address VARCHAR(45)
  -- IP de onde foi aceito (compliance)

activation_sent_at TIMESTAMP
  -- Data de envio do email de ativação

activation_sent_to VARCHAR(255)
  -- Email para quem foi enviado

activated_at TIMESTAMP
  -- Data de ativação completa do acesso

activated_by_user_id BIGINT FK(users.id)
  -- Usuário que completou a ativação
```

#### Tabela `company_subscriptions`
```sql
-- Já existe, mas precisa validar integração
status                       -- 'active', 'cancelled', 'suspended', 'expired'
start_date
end_date
```

### 2. **Templates de Email Faltantes**

#### Email de Aceite de Contrato
```html
Subject: [ProTeamCare] Ative sua empresa - Aceite os Termos de Uso

Conteúdo:
- Boas-vindas
- Explicação sobre criação da empresa
- Link para página de aceite de contrato
- Prazo de validade (ex: 7 dias)
```

#### Email de Convite para Criar Usuário Gestor
```html
Subject: [ProTeamCare] Configure o acesso de gestor da empresa

Conteúdo:
- Contrato foi aceito ✓
- Agora criar usuário gestor
- Link para página de criação de conta
- Prazo de validade (24h)
```

### 3. **Endpoints Faltantes**

```python
# Novos endpoints necessários

POST /api/v1/company-activation/send-contract-email/{company_id}
  # Envia email de aceite de contrato

POST /api/v1/company-activation/accept-contract
  {
    "company_id": 123,
    "contract_version": "1.0",
    "accepted_by_name": "João Silva",
    "accepted_by_email": "joao@empresa.com",
    "ip_address": "192.168.1.100"
  }

POST /api/v1/company-activation/send-user-creation-email/{company_id}
  # Envia email para criar usuário gestor

GET /api/v1/companies?filter=pending_activation
  # Lista empresas sem ativação

PUT /api/v1/companies/{id}/resend-activation
  # Botão de reenviar ativação
```

### 4. **Páginas Frontend Faltantes**

```
/contract-acceptance/{token}
  - Página de aceite de contrato
  - Exibe termos de uso completos
  - Checkbox de aceite
  - Botão "Aceitar e Continuar"

/create-manager-account/{token}
  - Formulário de criação de usuário gestor
  - Nome completo
  - Email
  - Senha
  - Confirmar senha
```

### 5. **Componentes Frontend Faltantes**

```tsx
// Filtro de status de ativação na lista de empresas
<CompanyActivationStatusFilter />

// Botão de ações na lista
<ActionDropdown>
  <SendContractEmail />        // Enviar email de contrato
  <ResendActivation />          // Reenviar ativação
  <ViewActivationDetails />     // Ver detalhes
</ActionDropdown>

// Badge de status visual
<CompanyActivationBadge status={company.access_status} />
  // pending_contract: Amarelo
  // contract_signed: Azul
  // pending_user: Laranja
  // active: Verde
  // suspended: Vermelho
```

---

## 🎯 Fluxo Proposto Completo

### **FASE 1: Cadastro da Empresa** (Já implementado)
```
Admin cadastra empresa no sistema
  ↓
Empresa criada com status: access_status = 'pending_contract'
  ↓
[NOVO] Sistema NÃO envia email automaticamente
```

### **FASE 2: Envio de Contrato** (NOVO)
```
Admin clica em "Enviar Email de Ativação" na lista de empresas
  ↓
Sistema envia email para responsável da empresa
  - Link: /contract-acceptance/{token}
  - Expira em 7 dias
  ↓
Campo atualizado: activation_sent_at = now()
```

### **FASE 3: Aceite de Contrato** (NOVO)
```
Responsável acessa link do email
  ↓
Página exibe termos de uso completos
  ↓
Responsável lê e aceita
  ↓
Sistema registra:
  - access_status = 'contract_signed'
  - contract_accepted_at = now()
  - contract_accepted_by = email
  - contract_ip_address = IP
  ↓
Sistema AUTOMATICAMENTE envia email de criação de usuário
```

### **FASE 4: Criação de Usuário Gestor** (Adaptar existente)
```
Responsável recebe email com link
  - Link: /create-manager-account/{token}
  - Expira em 24h
  ↓
Preenche formulário:
  - Nome completo
  - Email
  - Senha
  ↓
Sistema cria usuário com:
  - status = 'active'
  - context_type = 'company'
  - company_id = {id}
  ↓
Atualiza empresa:
  - access_status = 'active'
  - activated_at = now()
  - activated_by_user_id = {user_id}
```

### **FASE 5: Acesso Liberado** ✅
```
Empresa com status 'active' pode:
  ✓ Criar assinatura (se não tiver)
  ✓ Criar estabelecimentos
  ✓ Criar clientes
  ✓ Acessar sistema normalmente
```

---

## 📊 Diagrama de Estados

```
┌─────────────────────┐
│ pending_contract    │ ← Empresa criada (inicial)
└──────────┬──────────┘
           │ Admin envia email
           ↓
┌─────────────────────┐
│ contract_signed     │ ← Responsável aceita contrato
└──────────┬──────────┘
           │ Sistema envia email automático
           ↓
┌─────────────────────┐
│ pending_user        │ ← Aguardando criação de usuário
└──────────┬──────────┘
           │ Responsável cria conta
           ↓
┌─────────────────────┐
│ active              │ ← Empresa ativa e funcional ✅
└─────────────────────┘
           │ Admin pode suspender
           ↓
┌─────────────────────┐
│ suspended           │ ← Empresa suspensa (sem acesso)
└─────────────────────┘
```

---

## 🔧 Alterações Necessárias

### 1. **Migration de Banco de Dados**

```sql
-- Migration: 018_company_activation_fields.sql

ALTER TABLE master.companies
ADD COLUMN access_status VARCHAR(20) DEFAULT 'pending_contract',
ADD COLUMN contract_terms_version VARCHAR(10),
ADD COLUMN contract_accepted_at TIMESTAMP,
ADD COLUMN contract_accepted_by VARCHAR(255),
ADD COLUMN contract_ip_address VARCHAR(45),
ADD COLUMN activation_sent_at TIMESTAMP,
ADD COLUMN activation_sent_to VARCHAR(255),
ADD COLUMN activated_at TIMESTAMP,
ADD COLUMN activated_by_user_id BIGINT REFERENCES master.users(id);

-- Índices para performance
CREATE INDEX idx_companies_access_status ON master.companies(access_status);
CREATE INDEX idx_companies_contract_accepted_at ON master.companies(contract_accepted_at);
CREATE INDEX idx_companies_activated_at ON master.companies(activated_at);

-- Constraint de status
ALTER TABLE master.companies
ADD CONSTRAINT companies_access_status_check
CHECK (access_status IN (
  'pending_contract',
  'contract_signed',
  'pending_user',
  'active',
  'suspended'
));
```

### 2. **Atualizar Model** (`app/infrastructure/orm/models.py`)

```python
class Company(Base):
    __tablename__ = "companies"

    # ... campos existentes ...

    # Novos campos de ativação
    access_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="pending_contract"
    )
    contract_terms_version: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    contract_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    contract_accepted_by: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    contract_ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    activation_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    activation_sent_to: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    activated_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("master.users.id"), nullable=True
    )
```

### 3. **Novo Serviço de Email** (`app/infrastructure/services/email_service.py`)

```python
async def send_contract_acceptance_email(
    self,
    company_name: str,
    email: str,
    contract_token: str,
) -> bool:
    """Envia email de aceite de contrato"""
    # Template HTML com termos de uso
    pass

async def send_create_manager_email(
    self,
    company_name: str,
    email: str,
    user_creation_token: str,
) -> bool:
    """Envia email para criar usuário gestor"""
    # Template HTML com link de criação
    pass
```

### 4. **Novo Endpoint** (`app/presentation/api/v1/company_activation.py`)

```python
@router.post("/send-contract-email/{company_id}")
async def send_contract_email(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Envia email de aceite de contrato para empresa"""
    pass

@router.post("/accept-contract")
async def accept_contract(
    contract_data: ContractAcceptance,
    db: AsyncSession = Depends(get_db),
):
    """Registra aceite de contrato e envia email de criação de usuário"""
    pass
```

### 5. **Frontend: Lista de Empresas**

```tsx
// Adicionar filtro de status
const [statusFilter, setStatusFilter] = useState('all');

<select value={statusFilter} onChange={...}>
  <option value="all">Todas</option>
  <option value="pending_contract">Aguardando Contrato</option>
  <option value="contract_signed">Contrato Assinado</option>
  <option value="pending_user">Aguardando Usuário</option>
  <option value="active">Ativas</option>
  <option value="suspended">Suspensas</option>
</select>

// Adicionar botão de ação
<ActionDropdown>
  {company.access_status === 'pending_contract' && (
    <button onClick={() => sendContractEmail(company.id)}>
      📧 Enviar Email de Ativação
    </button>
  )}
  {company.access_status === 'pending_user' && (
    <button onClick={() => resendUserCreationEmail(company.id)}>
      🔄 Reenviar Criação de Usuário
    </button>
  )}
</ActionDropdown>
```

---

## 🎨 Interface Proposta

### Lista de Empresas com Status

```
┌─────────────────────────────────────────────────────────────┐
│ 🏢 Empresas                                    [+ Nova]      │
├─────────────────────────────────────────────────────────────┤
│ Filtro: [Todas ▼] [Aguardando Contrato] [Ativas]           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 🏢 HOME CARE BRASIL                      [⚠️ Aguardando]    │
│    CNPJ: 12.345.678/0001-90                                 │
│    Criada em: 02/10/2025                                    │
│    [📧 Enviar Email de Ativação] [👁️ Ver] [✏️ Editar]      │
│                                                               │
│ 🏢 SAÚDE TOTAL LTDA                      [✅ Ativa]         │
│    CNPJ: 98.765.432/0001-10                                 │
│    Ativada em: 28/09/2025                                   │
│    [👁️ Ver] [✏️ Editar] [🔄 Reativar]                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Detalhes da Empresa - Aba Ativação (NOVA)

```
┌─────────────────────────────────────────────────────────────┐
│ 🏢 HOME CARE BRASIL                                         │
├─────────────────────────────────────────────────────────────┤
│ [Info] [Estabelec.] [Clientes] [🔐 Ativação] [Faturamento] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 📋 Status de Ativação                                       │
│                                                               │
│ ┌─────────────────────────────────────────┐                 │
│ │ Status Atual: ⚠️ Aguardando Contrato   │                 │
│ └─────────────────────────────────────────┘                 │
│                                                               │
│ Timeline:                                                    │
│ ✅ Empresa cadastrada - 02/10/2025 10:30                    │
│ ⏳ Email de contrato enviado - Não enviado                  │
│ ⏳ Contrato aceito - Pendente                               │
│ ⏳ Usuário gestor criado - Pendente                         │
│ ⏳ Acesso ativado - Pendente                                │
│                                                               │
│ Ações:                                                       │
│ [📧 Enviar Email de Contrato]                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Plano de Implementação

### Sprint 1: Backend Foundation
1. ✅ Criar migration com novos campos
2. ✅ Atualizar model Company
3. ✅ Criar novos schemas Pydantic
4. ✅ Criar endpoints de ativação
5. ✅ Criar templates de email

### Sprint 2: Backend Logic
6. ✅ Implementar use case de envio de contrato
7. ✅ Implementar use case de aceite de contrato
8. ✅ Implementar use case de criação de usuário gestor
9. ✅ Adicionar validações de status
10. ✅ Testes unitários

### Sprint 3: Frontend - Lista
11. ✅ Adicionar filtro de status
12. ✅ Adicionar badge visual de status
13. ✅ Adicionar botões de ação por status
14. ✅ Implementar modal de confirmação
15. ✅ Integração com endpoints

### Sprint 4: Frontend - Páginas
16. ✅ Página de aceite de contrato
17. ✅ Página de criação de usuário gestor
18. ✅ Aba de ativação em detalhes da empresa
19. ✅ Timeline visual de ativação
20. ✅ Testes E2E

---

## ✅ Vantagens do Novo Processo

1. **Compliance Legal**: Registro de aceite de contrato com IP e timestamp
2. **Segurança**: Processo em etapas com validação
3. **Rastreabilidade**: Timeline completa de ativação
4. **Controle Admin**: Admin decide quando enviar ativação
5. **UX Melhor**: Fluxo guiado e claro para o cliente
6. **Audit Trail**: Registro de quem/quando/onde aceitou
7. **Flexibilidade**: Possibilidade de reenvio em cada etapa

---

## 📝 Observações Importantes

- ✅ Estrutura de usuários já está completa
- ✅ Sistema de emails já está funcional
- ✅ Endpoints de ativação já existem (adaptar)
- ❌ Falta apenas adicionar campos de controle na empresa
- ❌ Falta criar as páginas públicas de aceite/criação
- ❌ Falta criar os filtros e ações no frontend

---

## 🎯 Próximos Passos

Aguardando aprovação para iniciar implementação seguindo este documento.
