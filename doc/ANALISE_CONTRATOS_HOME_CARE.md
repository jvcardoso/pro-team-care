# 📋 Análise: Sistema de Contratos Home Care com Múltiplas Vidas

## 🎯 Cenários de Negócio

### 1. **Pessoa Física Individual**
- **Cliente**: João Silva (CPF: 123.456.789-00)
- **Vidas**: Titular + dependentes (esposa, 2 filhos)
- **Características**: Vidas fixas, alterações raras, plano familiar

### 2. **Pessoa Jurídica Corporativa**
- **Cliente**: UNIMED Regional (CNPJ: 12.345.678/0001-90)
- **Vidas**: 10 funcionários/mês (rotatividade permitida)
- **Características**: Quantidade fixa, lista flexível, controle mensal

### 3. **Pessoa Física Empresário**
- **Cliente**: Dr. Carlos (CPF) - Clínica médica
- **Vidas**: Equipe clínica (5 pessoas)
- **Características**: Pequeno porte, flexibilidade limitada

## 🏗️ Estrutura Proposta

### **Hierarquia Cliente → Contrato → Serviços → Vida → Serviços Específicos**

```
CLIENTE (PF/PJ)
├── CONTRATO 1 (Plano Básico - 10 vidas)
│   ├── SERVIÇOS PERMITIDOS NO CONTRATO
│   │   ├── ENF001: Aplicação Medicação EV (até 4/mês por vida)
│   │   ├── ENF002: Curativo Simples (até 8/mês por vida)
│   │   ├── FIS001: Fisioterapia Motora (até 8/mês por vida)
│   │   └── MED001: Consulta Médica (1/mês por vida)
│   ├── VIDA 1 (Maria Silva - Diabética)
│   │   ├── ✅ ENF001: Autorizada (insulina 2x/dia)
│   │   ├── ✅ ENF002: Autorizada
│   │   ├── ❌ FIS001: Não autorizada (sem indicação)
│   │   └── ✅ MED001: Autorizada
│   ├── VIDA 2 (João Santos - Pós-cirúrgico)
│   │   ├── ✅ ENF001: Autorizada (antibiótico)
│   │   ├── ✅ ENF002: Autorizada (curativo cirúrgico)
│   │   ├── ✅ FIS001: Autorizada (reabilitação)
│   │   └── ✅ MED001: Autorizada
│   └── VIDA 3 (Ana Costa - Idosa)
│       ├── ❌ ENF001: Não autorizada
│       ├── ✅ ENF002: Autorizada (úlceras)
│       ├── ✅ FIS001: Autorizada (mobilidade)
│       └── ✅ MED001: Autorizada
```

## 📊 Modelagem de Dados

### **1. Tabela: contracts**
```sql
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    contract_type VARCHAR(20) NOT NULL CHECK (contract_type IN ('INDIVIDUAL', 'CORPORATIVO', 'EMPRESARIAL')),

    -- Controle de Vidas
    lives_contracted INTEGER NOT NULL DEFAULT 1,
    lives_minimum INTEGER DEFAULT NULL, -- tolerância mínima
    lives_maximum INTEGER DEFAULT NULL, -- tolerância máxima

    -- Flexibilidade
    allows_substitution BOOLEAN DEFAULT false,
    control_period VARCHAR(10) DEFAULT 'MONTHLY' CHECK (control_period IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY')),

    -- Dados do Contrato
    plan_name VARCHAR(100) NOT NULL,
    monthly_value DECIMAL(10,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,

    -- Localização
    service_addresses JSONB, -- múltiplos endereços de atendimento

    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SUSPENDED', 'CANCELLED', 'EXPIRED')),

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);
```

### **2. Tabela: contract_lives**
```sql
CREATE TABLE contract_lives (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL REFERENCES contracts(id),
    person_id INTEGER NOT NULL REFERENCES people(id),

    -- Período de Vinculação
    start_date DATE NOT NULL,
    end_date DATE, -- NULL = ativa

    -- Tipo de Relação
    relationship_type VARCHAR(20) NOT NULL CHECK (relationship_type IN ('TITULAR', 'DEPENDENTE', 'FUNCIONARIO', 'BENEFICIARIO')),

    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUBSTITUTED', 'CANCELLED')),
    substitution_reason VARCHAR(100),

    -- Localização Específica
    primary_service_address JSONB,

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),

    -- Constraints
    UNIQUE(contract_id, person_id, start_date) -- mesma pessoa pode ter períodos diferentes
);
```

### **3. Tabela: contract_lives_history**
```sql
CREATE TABLE contract_lives_history (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('ADDED', 'REMOVED', 'SUBSTITUTED', 'REACTIVATED')),
    action_date DATE NOT NULL,
    reason VARCHAR(200),
    previous_person_id INTEGER, -- em caso de substituição

    -- Contexto no momento da ação
    lives_count_before INTEGER,
    lives_count_after INTEGER,

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);
```

### **4. View: contract_current_lives**
```sql
CREATE VIEW contract_current_lives AS
SELECT
    cl.contract_id,
    cl.person_id,
    p.name as person_name,
    p.document_number,
    cl.relationship_type,
    cl.start_date,
    cl.primary_service_address,
    c.lives_contracted,
    c.lives_minimum,
    c.lives_maximum
FROM contract_lives cl
JOIN people p ON cl.person_id = p.id
JOIN contracts c ON cl.contract_id = c.id
WHERE cl.status = 'ACTIVE'
  AND cl.end_date IS NULL
  AND c.status = 'ACTIVE';
```

## 💡 Solução para Cenário UNIMED

### **Caso: "10 vidas/mês com rotatividade"**

```sql
-- 1. Criar contrato flexível
INSERT INTO contracts (
    client_id, contract_number, contract_type,
    lives_contracted, lives_minimum, lives_maximum,
    allows_substitution, control_period,
    plan_name, monthly_value, start_date
) VALUES (
    65, 'UNIMED-2025-001', 'CORPORATIVO',
    10, 8, 12,  -- 10 vidas, tolerância ±2
    true, 'MONTHLY',
    'Plano Corporativo UNIMED', 15000.00, '2025-01-01'
);

-- 2. Adicionar vidas iniciais
INSERT INTO contract_lives (contract_id, person_id, start_date, relationship_type) VALUES
(1001, 201, '2025-01-01', 'FUNCIONARIO'),
(1001, 202, '2025-01-01', 'FUNCIONARIO'),
-- ... até 10 pessoas

-- 3. Substituição em 15/01 (Ana sai, Pedro entra)
UPDATE contract_lives
SET status = 'SUBSTITUTED', end_date = '2025-01-15', substitution_reason = 'Desligamento da empresa'
WHERE contract_id = 1001 AND person_id = 203;

INSERT INTO contract_lives (contract_id, person_id, start_date, relationship_type) VALUES
(1001, 204, '2025-01-16', 'FUNCIONARIO');

-- 4. Registrar histórico
INSERT INTO contract_lives_history (contract_id, person_id, action_type, action_date, reason, previous_person_id, lives_count_before, lives_count_after, created_by) VALUES
(1001, 203, 'REMOVED', '2025-01-15', 'Desligamento da empresa', NULL, 10, 9, 1),
(1001, 204, 'SUBSTITUTED', '2025-01-16', 'Substituição por novo funcionário', 203, 9, 10, 1);
```

## 🏥 Gestão de Serviços Home Care

### **Estrutura de Serviços**

**Nível 1: Catálogo de Serviços (Global)**
- Todos os serviços disponíveis na empresa
- Características, limitações e valores padrão

**Nível 2: Serviços do Contrato**
- Quais serviços estão inclusos no contrato
- Limites e valores específicos por contrato

**Nível 3: Serviços por Vida**
- Personalização médica individual
- Autorizações e restrições específicas

### **1. Tabela: services_catalog**
```sql
CREATE TABLE services_catalog (
    id SERIAL PRIMARY KEY,
    service_code VARCHAR(20) UNIQUE NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    service_category VARCHAR(50) NOT NULL, -- 'ENFERMAGEM', 'FISIOTERAPIA', 'MEDICINA', 'NUTRIÇÃO'
    service_type VARCHAR(30) NOT NULL, -- 'VISITA', 'PROCEDIMENTO', 'MEDICAÇÃO', 'EQUIPAMENTO'

    -- Características do Serviço
    requires_prescription BOOLEAN DEFAULT false,
    requires_specialist BOOLEAN DEFAULT false,
    home_visit_required BOOLEAN DEFAULT true,

    -- Valores e Controle
    default_unit_value DECIMAL(10,2),
    billing_unit VARCHAR(20) DEFAULT 'UNIT', -- 'UNIT', 'HOUR', 'DAY', 'MONTH'

    -- Regulamentações
    anvisa_regulated BOOLEAN DEFAULT false,
    requires_authorization BOOLEAN DEFAULT false,

    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE',

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exemplos de serviços
INSERT INTO services_catalog (service_code, service_name, service_category, service_type, requires_prescription, home_visit_required, default_unit_value) VALUES
('ENF001', 'Aplicação de Medicação EV', 'ENFERMAGEM', 'PROCEDIMENTO', true, true, 80.00),
('ENF002', 'Curativo Simples', 'ENFERMAGEM', 'PROCEDIMENTO', false, true, 45.00),
('ENF003', 'Coleta de Sangue', 'ENFERMAGEM', 'EXAME', false, true, 35.00),
('FIS001', 'Fisioterapia Motora', 'FISIOTERAPIA', 'TERAPIA', true, true, 120.00),
('MED001', 'Consulta Médica Domiciliar', 'MEDICINA', 'CONSULTA', false, true, 250.00),
('EQP001', 'Locação Cama Hospitalar', 'EQUIPAMENTO', 'LOCAÇÃO', false, false, 300.00),
('NUT001', 'Consulta Nutricional', 'NUTRIÇÃO', 'CONSULTA', false, true, 150.00),
('PSI001', 'Atendimento Psicológico', 'PSICOLOGIA', 'CONSULTA', false, true, 120.00);
```

### **2. Tabela: contract_services**
```sql
CREATE TABLE contract_services (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL REFERENCES contracts(id),
    service_id INTEGER NOT NULL REFERENCES services_catalog(id),

    -- Limites e Controles do Contrato
    monthly_limit INTEGER, -- quantidade máxima por mês por vida (NULL = ilimitado)
    daily_limit INTEGER,   -- quantidade máxima por dia por vida
    annual_limit INTEGER,  -- limite anual por vida

    -- Valores Específicos do Contrato
    unit_value DECIMAL(10,2), -- valor específico para este contrato
    requires_pre_authorization BOOLEAN DEFAULT false,

    -- Período de Validade
    start_date DATE NOT NULL,
    end_date DATE,

    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE',

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id),

    UNIQUE(contract_id, service_id, start_date)
);
```

### **3. Tabela: contract_life_services**
```sql
CREATE TABLE contract_life_services (
    id SERIAL PRIMARY KEY,
    contract_life_id INTEGER NOT NULL REFERENCES contract_lives(id),
    service_id INTEGER NOT NULL REFERENCES services_catalog(id),

    -- Autorização Individual
    is_authorized BOOLEAN DEFAULT true,
    authorization_date DATE,
    authorized_by INTEGER REFERENCES users(id), -- médico responsável

    -- Limites Individuais (sobrepõem os do contrato)
    monthly_limit_override INTEGER,
    daily_limit_override INTEGER,
    annual_limit_override INTEGER,

    -- Dados Médicos
    medical_indication TEXT,
    contraindications TEXT,
    special_instructions TEXT,
    priority_level VARCHAR(20) DEFAULT 'NORMAL', -- 'URGENT', 'HIGH', 'NORMAL', 'LOW'

    -- Período de Autorização
    start_date DATE NOT NULL,
    end_date DATE,

    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE',

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),

    UNIQUE(contract_life_id, service_id, start_date)
);
```

### **4. Tabela: service_executions**
```sql
CREATE TABLE service_executions (
    id SERIAL PRIMARY KEY,
    contract_life_id INTEGER NOT NULL REFERENCES contract_lives(id),
    service_id INTEGER NOT NULL REFERENCES services_catalog(id),

    -- Dados da Execução
    execution_date TIMESTAMP NOT NULL,
    professional_id INTEGER REFERENCES users(id),

    -- Detalhes da Execução
    quantity DECIMAL(8,2) DEFAULT 1,
    unit_value DECIMAL(10,2) NOT NULL,
    total_value DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_value) STORED,

    -- Localização
    service_address JSONB,
    arrival_time TIMESTAMP,
    departure_time TIMESTAMP,
    duration_minutes INTEGER,

    -- Observações Clínicas
    execution_notes TEXT,
    patient_response TEXT,
    complications TEXT,
    materials_used JSONB,

    -- Controle de Qualidade
    quality_score INTEGER CHECK (quality_score BETWEEN 1 AND 5),
    family_satisfaction INTEGER CHECK (family_satisfaction BETWEEN 1 AND 5),

    -- Status
    status VARCHAR(20) DEFAULT 'EXECUTED', -- 'SCHEDULED', 'EXECUTED', 'CANCELLED', 'NO_SHOW'
    cancellation_reason TEXT,

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);
```

## 📊 Views de Controle

### **1. Serviços Disponíveis por Vida**
```sql
CREATE VIEW available_services_per_life AS
SELECT
    cl.id as contract_life_id,
    cl.contract_id,
    p.name as person_name,
    p.document_number,
    sc.service_code,
    sc.service_name,
    sc.service_category,
    sc.service_type,

    -- Limites do Contrato
    cs.monthly_limit as contract_monthly_limit,
    cs.daily_limit as contract_daily_limit,
    cs.annual_limit as contract_annual_limit,
    cs.unit_value as contract_unit_value,

    -- Limites Específicos da Vida (override)
    COALESCE(cls.monthly_limit_override, cs.monthly_limit) as effective_monthly_limit,
    COALESCE(cls.daily_limit_override, cs.daily_limit) as effective_daily_limit,
    COALESCE(cls.annual_limit_override, cs.annual_limit) as effective_annual_limit,

    -- Status de Autorização
    COALESCE(cls.is_authorized, true) as is_authorized,
    cls.medical_indication,
    cls.special_instructions,
    cls.priority_level,

    -- Dados do Serviço
    sc.requires_prescription,
    sc.requires_specialist,
    sc.home_visit_required

FROM contract_lives cl
JOIN people p ON cl.person_id = p.id
JOIN contracts c ON cl.contract_id = c.id
JOIN contract_services cs ON c.id = cs.contract_id
JOIN services_catalog sc ON cs.service_id = sc.id
LEFT JOIN contract_life_services cls ON cl.id = cls.contract_life_id AND sc.id = cls.service_id

WHERE cl.status = 'ACTIVE'
  AND cl.end_date IS NULL
  AND cs.status = 'ACTIVE'
  AND (cs.end_date IS NULL OR cs.end_date >= CURRENT_DATE)
  AND (cls.status IS NULL OR cls.status = 'ACTIVE')
  AND (cls.end_date IS NULL OR cls.end_date >= CURRENT_DATE)
  AND sc.status = 'ACTIVE';
```

### **2. Controle de Consumo por Período**
```sql
CREATE VIEW service_consumption_control AS
SELECT
    cl.id as contract_life_id,
    p.name as person_name,
    se.service_id,
    sc.service_name,

    -- Consumo Diário
    COUNT(CASE WHEN se.execution_date::DATE = CURRENT_DATE AND se.status = 'EXECUTED' THEN 1 END) as today_count,

    -- Consumo Mensal
    COUNT(CASE WHEN DATE_TRUNC('month', se.execution_date) = DATE_TRUNC('month', CURRENT_DATE) AND se.status = 'EXECUTED' THEN 1 END) as month_count,

    -- Consumo Anual
    COUNT(CASE WHEN DATE_TRUNC('year', se.execution_date) = DATE_TRUNC('year', CURRENT_DATE) AND se.status = 'EXECUTED' THEN 1 END) as year_count,

    -- Valores
    SUM(CASE WHEN DATE_TRUNC('month', se.execution_date) = DATE_TRUNC('month', CURRENT_DATE) AND se.status = 'EXECUTED' THEN se.total_value ELSE 0 END) as month_value,

    -- Qualidade
    AVG(CASE WHEN se.quality_score IS NOT NULL AND se.status = 'EXECUTED' THEN se.quality_score END) as avg_quality_score,
    AVG(CASE WHEN se.family_satisfaction IS NOT NULL AND se.status = 'EXECUTED' THEN se.family_satisfaction END) as avg_satisfaction

FROM contract_lives cl
JOIN people p ON cl.person_id = p.id
LEFT JOIN service_executions se ON cl.id = se.contract_life_id
LEFT JOIN services_catalog sc ON se.service_id = sc.id
WHERE cl.status = 'ACTIVE' AND cl.end_date IS NULL
GROUP BY cl.id, p.name, se.service_id, sc.service_name;
```

## 🎯 Exemplo Prático: Contrato UNIMED

```sql
-- 1. Criar contrato UNIMED com serviços
INSERT INTO contracts (client_id, contract_number, contract_type, lives_contracted, allows_substitution, plan_name, monthly_value)
VALUES (65, 'UNIMED-2025-001', 'CORPORATIVO', 10, true, 'Plano Home Care Corporativo', 15000.00);

-- 2. Definir serviços permitidos no contrato
INSERT INTO contract_services (contract_id, service_id, monthly_limit, unit_value, requires_pre_authorization) VALUES
(1001, 1, 4, 80.00, false),    -- ENF001: Até 4 aplicações EV por mês por vida
(1001, 2, 8, 45.00, false),    -- ENF002: Até 8 curativos por mês por vida
(1001, 3, 2, 35.00, false),    -- ENF003: Até 2 coletas por mês por vida
(1001, 4, 8, 120.00, true),    -- FIS001: Até 8 sessões de fisio por mês (precisa autorização)
(1001, 5, 1, 250.00, false),   -- MED001: 1 consulta médica por mês por vida
(1001, 7, 1, 150.00, true);    -- NUT001: 1 consulta nutricional por mês (precisa autorização)

-- 3. Adicionar vida ao contrato (Maria - Diabética)
INSERT INTO contract_lives (contract_id, person_id, start_date, relationship_type)
VALUES (1001, 201, '2025-01-01', 'FUNCIONARIO');

-- 4. Personalizar serviços para Maria (diabética)
INSERT INTO contract_life_services (contract_life_id, service_id, medical_indication, special_instructions, is_authorized, priority_level) VALUES
(2001, 1, 'Diabetes tipo 2 - insulina NPH e regular', 'Aplicar conforme prescrição médica. NPH pela manhã, regular antes das refeições', true, 'HIGH'),
(2001, 3, 'Controle glicêmico - HbA1c e glicemia', 'Coleta mensal para hemoglobina glicada e glicemia de jejum', true, 'NORMAL'),
(2001, 7, 'Orientação nutricional para diabetes', 'Dieta para controle glicêmico', true, 'NORMAL');

-- 5. Restringir fisioterapia para Maria (não tem indicação)
INSERT INTO contract_life_services (contract_life_id, service_id, is_authorized, medical_indication)
VALUES (2001, 4, false, 'Sem indicação clínica atual');

-- 6. Registrar execução de serviços
INSERT INTO service_executions (contract_life_id, service_id, execution_date, professional_id, unit_value, execution_notes, quality_score) VALUES
(2001, 1, '2025-01-15 08:00:00', 10, 80.00, 'Aplicação de insulina NPH - 20UI subcutânea', 5),
(2001, 1, '2025-01-15 18:00:00', 10, 80.00, 'Aplicação de insulina regular - 8UI subcutânea', 5),
(2001, 3, '2025-01-20 07:00:00', 12, 35.00, 'Coleta para glicemia de jejum - paciente em jejum há 12h', 4);
```

## 🔍 Funções de Validação

### **Validação de Limites de Serviço**
```sql
CREATE OR REPLACE FUNCTION validate_service_limits(
    p_contract_life_id INTEGER,
    p_service_id INTEGER,
    p_execution_date DATE,
    p_quantity DECIMAL DEFAULT 1
) RETURNS TEXT AS $$
DECLARE
    daily_used DECIMAL;
    monthly_used DECIMAL;
    annual_used DECIMAL;
    daily_limit INTEGER;
    monthly_limit INTEGER;
    annual_limit INTEGER;
    is_authorized BOOLEAN;
    result TEXT;
BEGIN
    -- Buscar limites efetivos e autorização
    SELECT
        effective_daily_limit,
        effective_monthly_limit,
        effective_annual_limit,
        is_authorized
    INTO daily_limit, monthly_limit, annual_limit, is_authorized
    FROM available_services_per_life
    WHERE contract_life_id = p_contract_life_id
      AND service_id = p_service_id;

    -- Verificar se serviço está autorizado
    IF NOT COALESCE(is_authorized, false) THEN
        RETURN 'SERVICE_NOT_AUTHORIZED';
    END IF;

    -- Verificar uso diário
    SELECT COALESCE(SUM(quantity), 0)
    INTO daily_used
    FROM service_executions
    WHERE contract_life_id = p_contract_life_id
      AND service_id = p_service_id
      AND execution_date::DATE = p_execution_date
      AND status = 'EXECUTED';

    -- Verificar uso mensal
    SELECT COALESCE(SUM(quantity), 0)
    INTO monthly_used
    FROM service_executions
    WHERE contract_life_id = p_contract_life_id
      AND service_id = p_service_id
      AND DATE_TRUNC('month', execution_date) = DATE_TRUNC('month', p_execution_date)
      AND status = 'EXECUTED';

    -- Verificar uso anual
    SELECT COALESCE(SUM(quantity), 0)
    INTO annual_used
    FROM service_executions
    WHERE contract_life_id = p_contract_life_id
      AND service_id = p_service_id
      AND DATE_TRUNC('year', execution_date) = DATE_TRUNC('year', p_execution_date)
      AND status = 'EXECUTED';

    -- Validar limites
    IF daily_limit IS NOT NULL AND (daily_used + p_quantity) > daily_limit THEN
        result := 'DAILY_LIMIT_EXCEEDED';
    ELSIF monthly_limit IS NOT NULL AND (monthly_used + p_quantity) > monthly_limit THEN
        result := 'MONTHLY_LIMIT_EXCEEDED';
    ELSIF annual_limit IS NOT NULL AND (annual_used + p_quantity) > annual_limit THEN
        result := 'ANNUAL_LIMIT_EXCEEDED';
    ELSE
        result := 'WITHIN_LIMITS';
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

## 🔄 Controle de Rotatividade

### **Regras de Negócio**

1. **Validação Mensal**: Verificar quantidade no último dia do mês
2. **Tolerância**: Permitir variação dentro dos limites (±2 vidas)
3. **Substituição**: Livre durante o mês para contratos flexíveis
4. **Faturamento**: Sempre baseado na quantidade contratada
5. **Histórico**: Rastrear todas as alterações para auditoria

### **Funções de Controle**

```sql
-- Função: Validar quantidade de vidas no mês
CREATE OR REPLACE FUNCTION validate_contract_lives_month(
    p_contract_id INTEGER,
    p_year_month DATE
) RETURNS TEXT AS $$
DECLARE
    active_lives INTEGER;
    contract_data RECORD;
    result TEXT;
BEGIN
    -- Buscar dados do contrato
    SELECT lives_contracted, lives_minimum, lives_maximum
    INTO contract_data
    FROM contracts
    WHERE id = p_contract_id;

    -- Contar vidas ativas no período
    SELECT COUNT(*)
    INTO active_lives
    FROM contract_lives cl
    WHERE cl.contract_id = p_contract_id
      AND cl.start_date <= (p_year_month + INTERVAL '1 month' - INTERVAL '1 day')
      AND (cl.end_date IS NULL OR cl.end_date >= p_year_month)
      AND cl.status = 'ACTIVE';

    -- Validar limites
    IF active_lives < COALESCE(contract_data.lives_minimum, contract_data.lives_contracted) THEN
        result := 'BELOW_MINIMUM';
    ELSIF active_lives > COALESCE(contract_data.lives_maximum, contract_data.lives_contracted) THEN
        result := 'ABOVE_MAXIMUM';
    ELSE
        result := 'WITHIN_LIMITS';
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Função: Obter relatório mensal de vidas
CREATE OR REPLACE FUNCTION get_monthly_lives_report(
    p_contract_id INTEGER,
    p_year_month DATE
) RETURNS TABLE (
    person_id INTEGER,
    person_name VARCHAR,
    relationship_type VARCHAR,
    days_active INTEGER,
    start_date DATE,
    end_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cl.person_id,
        p.name::VARCHAR as person_name,
        cl.relationship_type::VARCHAR,
        (LEAST(
            (p_year_month + INTERVAL '1 month' - INTERVAL '1 day')::DATE,
            COALESCE(cl.end_date, CURRENT_DATE)
        ) - GREATEST(cl.start_date, p_year_month) + 1)::INTEGER as days_active,
        cl.start_date,
        cl.end_date
    FROM contract_lives cl
    JOIN people p ON cl.person_id = p.id
    WHERE cl.contract_id = p_contract_id
      AND cl.start_date <= (p_year_month + INTERVAL '1 month' - INTERVAL '1 day')
      AND (cl.end_date IS NULL OR cl.end_date >= p_year_month)
    ORDER BY cl.start_date, p.name;
END;
$$ LANGUAGE plpgsql;
```

## 📈 Dashboard de Controle

### **Métricas Importantes**

1. **Ocupação Atual**: 10/10 vidas (100%)
2. **Substituições no Mês**: 2 trocas
3. **Histórico de Alterações**: Timeline completo
4. **Faturamento**: Baseado em 10 vidas independente da ocupação real
5. **Alertas**: Quando sair dos limites de tolerância

### **Relatórios Necessários**

1. **Mensal**: Vidas ativas por contrato
2. **Histórico**: Todas as substituições e motivos
3. **Faturamento**: Controle de cobrança por período
4. **Auditoria**: Rastreabilidade completa de mudanças

## 📊 Dashboard de Gestão Home Care

### **Métricas Principais**

**1. Visão Geral do Contrato**
- Ocupação de vidas: 8/10 (80%)
- Faturamento mensal: R$ 15.000,00
- Serviços mais utilizados
- Score de qualidade médio

**2. Controle de Serviços por Vida**
- Utilização mensal por categoria
- Alertas de limite (próximo do máximo)
- Autorizações pendentes
- Histórico de execuções

**3. Qualidade e Satisfação**
- Score médio por profissional
- Satisfação familiar por serviço
- Tempo médio de atendimento
- Taxa de não comparecimento

**4. Financeiro**
- Faturamento por categoria de serviço
- Receita por vida/mês
- Comparativo orçado vs realizado
- Projeção de consumo

### **Relatórios Automatizados**

**Relatório Mensal por Contrato:**
```sql
-- Relatório executivo mensal
SELECT
    c.contract_number,
    c.plan_name,
    COUNT(DISTINCT cl.id) as active_lives,
    c.lives_contracted,
    SUM(se.total_value) as monthly_revenue,
    AVG(se.quality_score) as avg_quality,
    COUNT(se.id) as total_services,

    -- Por categoria
    COUNT(CASE WHEN sc.service_category = 'ENFERMAGEM' THEN 1 END) as nursing_services,
    COUNT(CASE WHEN sc.service_category = 'FISIOTERAPIA' THEN 1 END) as physio_services,
    COUNT(CASE WHEN sc.service_category = 'MEDICINA' THEN 1 END) as medical_services

FROM contracts c
LEFT JOIN contract_lives cl ON c.id = cl.contract_id AND cl.status = 'ACTIVE'
LEFT JOIN service_executions se ON cl.id = se.contract_life_id
    AND DATE_TRUNC('month', se.execution_date) = DATE_TRUNC('month', CURRENT_DATE)
    AND se.status = 'EXECUTED'
LEFT JOIN services_catalog sc ON se.service_id = sc.id
WHERE c.status = 'ACTIVE'
GROUP BY c.id, c.contract_number, c.plan_name;
```

**Alerta de Limites:**
```sql
-- Vidas próximas dos limites mensais
SELECT
    p.name as person_name,
    sc.service_name,
    COUNT(se.id) as used_this_month,
    avs.effective_monthly_limit as monthly_limit,
    ROUND((COUNT(se.id)::DECIMAL / avs.effective_monthly_limit) * 100, 1) as usage_percentage

FROM available_services_per_life avs
JOIN people p ON avs.person_name = p.name
JOIN services_catalog sc ON avs.service_code = sc.service_code
LEFT JOIN service_executions se ON avs.contract_life_id = se.contract_life_id
    AND avs.service_id = se.service_id
    AND DATE_TRUNC('month', se.execution_date) = DATE_TRUNC('month', CURRENT_DATE)
    AND se.status = 'EXECUTED'

WHERE avs.effective_monthly_limit IS NOT NULL
GROUP BY p.name, sc.service_name, avs.effective_monthly_limit
HAVING COUNT(se.id)::DECIMAL / avs.effective_monthly_limit >= 0.8  -- 80% do limite
ORDER BY usage_percentage DESC;
```

## 🔧 Integração com Sistema Atual

### **Mapeamento de Tabelas Existentes**

**Aproveitamento das tabelas atuais:**
- `clients` → Mantém como está (PF/PJ)
- `people` → Mantém como está (vidas individuais)
- `users` → Mantém como está (profissionais)

**Novas tabelas necessárias:**
- `contracts` → Nova (contratos por cliente)
- `contract_lives` → Nova (vidas vinculadas)
- `services_catalog` → Nova (catálogo de serviços)
- `contract_services` → Nova (serviços do contrato)
- `contract_life_services` → Nova (personalizações)
- `service_executions` → Nova (histórico execuções)

### **APIs Necessárias**

**1. Gestão de Contratos:**
- `POST /api/v1/contracts` - Criar contrato
- `GET /api/v1/contracts/{id}` - Detalhes do contrato
- `PUT /api/v1/contracts/{id}/lives` - Gerenciar vidas
- `GET /api/v1/contracts/{id}/services` - Serviços disponíveis

**2. Gestão de Serviços:**
- `GET /api/v1/services/catalog` - Catálogo completo
- `POST /api/v1/services/executions` - Registrar execução
- `GET /api/v1/services/limits/{life_id}` - Verificar limites
- `POST /api/v1/services/authorize` - Autorizar serviço

**3. Relatórios:**
- `GET /api/v1/reports/contract/{id}/monthly` - Relatório mensal
- `GET /api/v1/reports/alerts/limits` - Alertas de limites
- `GET /api/v1/dashboard/contract/{id}` - Dashboard executivo

## 🚀 Roadmap de Implementação

### **Fase 1: Estrutura Base (2-3 semanas)**
1. ✅ **Análise completa** (atual)
2. 🔄 **Criação das tabelas** de contratos e serviços
3. 🔄 **APIs básicas** de CRUD
4. 🔄 **Testes unitários** das validações

### **Fase 2: Gestão de Serviços (3-4 semanas)**
1. 🔄 **Catálogo de serviços** completo
2. 🔄 **Sistema de autorizações** médicas
3. 🔄 **Controle de limites** automático
4. 🔄 **Interface de execução** de serviços

### **Fase 3: Relatórios e Dashboard (2-3 semanas)**
1. 🔄 **Dashboard executivo** por contrato
2. 🔄 **Relatórios automáticos** mensais
3. 🔄 **Sistema de alertas** de limites
4. 🔄 **Métricas de qualidade** e satisfação

### **Fase 4: Integração e Testes (2-3 semanas)**
1. 🔄 **Migração de dados** existentes
2. 🔄 **Testes com UNIMED** (piloto)
3. 🔄 **Ajustes e otimizações**
4. 🔄 **Treinamento da equipe**

## ✅ Benefícios da Solução

### **Para a Empresa**
- ✅ **Controle total** de contratos e serviços
- ✅ **Faturamento preciso** e automático
- ✅ **Gestão de qualidade** integrada
- ✅ **Histórico completo** para auditoria

### **Para os Clientes (UNIMED)**
- ✅ **Flexibilidade** na troca de vidas
- ✅ **Transparência** no consumo de serviços
- ✅ **Relatórios detalhados** mensais
- ✅ **Controle de custos** previsível

### **Para as Vidas (Pacientes)**
- ✅ **Serviços personalizados** conforme necessidade médica
- ✅ **Qualidade assegurada** com métricas
- ✅ **Atendimento domiciliar** humanizado
- ✅ **Acompanhamento contínuo** da saúde

---

**Esta estrutura resolve completamente o desafio dos contratos home care com múltiplas vidas, oferecendo flexibilidade operacional com controle rigoroso financeiro e de qualidade.**
