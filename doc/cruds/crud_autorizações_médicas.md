# Documento da Estrutura de Arquivos do CRUD de Autorizações Médicas

## Backend

- **app/infrastructure/orm/models.py**: Define os modelos SQLAlchemy para `MedicalAuthorization`, `AuthorizationRenewal` e `AuthorizationHistory` com relacionamentos e restrições. Inclui validação de status e soft delete.
- **app/presentation/schemas/medical_authorization.py**: Esquemas Pydantic para operações de criação/atualização/resposta, enums e regras de validação. Inclui validadores de campo e relacionamentos.
- **app/infrastructure/repositories/medical_authorization_repository.py**: Repositório de classe lidando com todas as operações de banco de dados, queries complexas e lógica de negócio. Inclui queries complexas e gerenciamento de transações.
- **app/presentation/api/v1/medical_authorizations.py**: Router FastAPI com 15+ endpoints para operações CRUD completas, estatísticas e gerenciamento de ciclo de vida. Inclui decoradores de permissão e tratamento de erros estruturado.
- **app/presentation/api/v1/api.py**: Inclui router de autorizações médicas na configuração da API principal.
- **app/infrastructure/services/contract_dashboard_service.py**: Serviço que usa autorizações médicas em métricas de dashboard e relatórios.
- **app/infrastructure/services/system_optimization_service.py**: Serviço que valida autorizações e inclui em verificações de saúde do sistema.
- **app/infrastructure/repositories/limits_repository.py**: Impõe limites de autorização e rastreia uso.

## Frontend

- **frontend/src/services/medicalAuthorizationsService.ts**: Serviço TypeScript para operações CRUD de autorizações médicas com cache HTTP e tratamento de erros.
- **frontend/src/pages/MedicalAuthorizationsPage.tsx**: Componente de página React para gerenciamento de autorizações médicas.
- **frontend/src/hooks/useDataTable.ts**: Hook genérico para tabelas de dados com métricas específicas de autorizações médicas.
- **frontend/src/hooks/useErrorHandler.ts**: Hook para tratamento de erros em operações de autorização.

## Tests

- **tests/test_medical_authorizations.py**: Testes básicos de esquema de criação e imports.
- **tests/test_home_care_business_rules.py**: Testes de validação de limites de autorizações e regras de negócio.
- **tests/test_home_care_integration.py**: Testes de integração end-to-end para fluxos de autorização.

## Config/Outros

- **migrations/010_medical_authorizations.py**: Cria tabelas core, índices, triggers e views para sistema de autorização.
- **migrations/011_automatic_limits_control.py**: Adiciona controle automático de limites e rastreamento de execução de serviço.
- **migrations/012_service_execution_interface.py**: Melhora interface de execução de serviço com validação de autorização.
- **scripts/add_contract_permissions.py**: Adiciona permissões granulares para autorizações médicas (criar/ver/atualizar/cancelar).
- **scripts/create_contract_menus_complete.py**: Cria itens de menu para gerenciamento de autorização.
- **scripts/create_contract_menus_simple.py**: Criação simplificada de menus para autorizações.
- **scripts/create_contract_menus.py**: Configuração básica de menus para acesso de autorização.
- **scripts/create_contract_views.py**: Cria views de banco para relatórios de autorização.

## Visão Geral Arquitetural

**Padrão Arquitetural Limpa:**
- **Camada de Domínio**: Esquemas Pydantic definem entidades e regras de validação
- **Camada de Aplicação**: Repositório implementa lógica de negócio e acesso a dados
- **Camada de Infraestrutura**: Modelos SQLAlchemy e operações de banco de dados
- **Camada de Apresentação**: Routers FastAPI com esquemas Pydantic e decoradores de segurança

**Arquitetura Multi-Tenant:**
- Operações de autorização escopadas por empresa através de relacionamentos de contrato
- Isolamento via Row Level Security (RLS)
- Validação de acesso a estabelecimento em todas as operações

**Fluxo de Dados:**
1. Componentes frontend disparam chamadas de API via camada de serviço
2. Routers FastAPI validam requisições e aplicam permissões
3. Repositório executa lógica de negócio e operações de banco
4. Respostas são serializadas através de esquemas Pydantic

## Modelo de Dados

**Entidades Core:**
```sql
medical_authorizations (
    id, contract_life_id, service_id, doctor_id,
    authorization_code (unique), authorization_date,
    valid_from, valid_until, sessions_authorized,
    sessions_remaining, monthly_limit, weekly_limit, daily_limit,
    medical_indication, contraindications, special_instructions,
    urgency_level, requires_supervision, supervision_notes,
    diagnosis_cid, diagnosis_description, treatment_goals,
    expected_duration_days, renewal_allowed, renewal_conditions,
    status, cancellation_reason, cancelled_at, cancelled_by,
    created_at, updated_at, created_by, updated_by
)
```

**Entidades Relacionadas:**
- `authorization_renewals`: Rastreia renovações de autorização com histórico de mudanças
- `authorization_history`: Trilha de auditoria para todas as mudanças de autorização
- `service_executions`: Liga a uso real de serviço (via chaves estrangeiras)

**Relacionamentos:**
- MedicalAuthorization → ContractLive (many-to-one)
- MedicalAuthorization → ServicesCatalog (many-to-one) 
- MedicalAuthorization → User (doctor, many-to-one)
- AuthorizationRenewal → MedicalAuthorization (original/new, many-to-one)
- AuthorizationHistory → MedicalAuthorization (many-to-one)

**Restrições & Validação:**
- Validação de faixa de datas (valid_from ≤ valid_until)
- Validação de limites de sessão (remaining ≤ authorized)
- Verificações de enum de status (active/expired/cancelled/suspended)
- Enum de nível de urgência (URGENT/HIGH/NORMAL/LOW)
- Códigos de autorização únicos com geração automática

## Segurança

**Autenticação & Autorização:**
- Autenticação JWT necessária para todas as operações
- Controle de acesso baseado em permissões (`medical_authorizations_create/view/update/cancel`)
- Decoradores de permissão nos endpoints da API
- Filtragem automática de empresa para usuários não-admin

**Proteção de Dados:**
- Trilha de auditoria em tabela `authorization_history` rastreia todas as mudanças
- Logging de endereço IP e user agent para monitoramento de segurança
- Soft deletes via mudanças de status (não hard deletes)
- Códigos de autorização como identificadores únicos (não IDs sequenciais)

**Validação de Entrada:**
- Esquemas Pydantic com validação rigorosa de tipo
- Prevenção de injeção SQL via queries parametrizadas
- Proteção XSS através de sanitização adequada de dados
- Validação de regras de negócio (limites de sessão, faixas de datas)

## Regras de Negócio

**Ciclo de Vida de Autorização:**
1. **Criação**: Códigos únicos auto-gerados, alocação inicial de sessão
2. **Validação**: Faixas de datas, limites de sessão, requisitos médicos
3. **Rastreamento de Uso**: Consumo de sessão com atualização de contagem restante
4. **Renovação**: Extensão com rastreamento de mudanças e workflow de aprovação
5. **Cancelamento**: Gravação de razão com trilha de auditoria
6. **Expiração**: Mudanças automáticas de status baseadas em datas

**Gerenciamento de Sessão:**
- Limites diários/semanais/mensais aplicados
- Cálculo de sessão restante e validação
- Rastreamento de uso por autorização
- Validação de limite antes da execução de serviço

**Validação Médica:**
- Indicação médica necessária para todas as autorizações
- Códigos CID-10 opcionais de diagnóstico
- Requisitos de supervisão para certos serviços
- Rastreamento de contraindicações e instruções especiais

## Performance

**Otimização de Banco de Dados:**
- Índices compostos em campos frequentemente consultados (status, dates, contract_id)
- Índices parciais excluindo registros deletados
- Views materializadas para queries comuns (`active_medical_authorizations`)

**Otimização de Query:**
- Eager loading com `joinedload` para entidades relacionadas
- Loading seletivo de campo para reduzir uso de memória
- Paginação com tamanhos de página configuráveis (1-100)
- Queries filtradas para limitar conjuntos de resultados

**Estratégia de Cache:**
- Cache de resposta HTTP para listas e detalhes de autorização
- Invalidação de cache em operações de mutação
- Cache de dados relacionados (contratos, clientes)

**Considerações de Escalabilidade:**
- Chaves primárias BigInteger para suporte de alto volume
- Particionamento potencial para tabelas de autorização grandes
- Operações assíncronas para computações pesadas
- Pooling de conexões via SQLAlchemy

## Tratamento de Erros

**Respostas de Erro da API:**
- 400 Bad Request: Erros de validação, violações de regras de negócio
- 401 Unauthorized: Falhas de autenticação
- 403 Forbidden: Permissão negada
- 404 Not Found: Autorização não encontrada
- 500 Internal Server Error: Erros do sistema

**Erros de Lógica de Negócio:**
- Faixas de datas inválidas
- Limite de sessão excedido
- Autorização expirada/cancelada
- Serviços incompatíveis

**Logging & Monitoramento:**
- Logging estruturado com contexto (user_id, authorization_id, company_id)
- Rastreamento de erros com stack traces
- Métricas de performance para queries lentas
- Trilha de auditoria para todas as mudanças de autorização

## Integrações

**Serviços Internos:**
- **Dashboard de Contrato**: Métricas de autorização e relatórios de uso
- **Repositório de Limites**: Validação de uso de sessão e imposição
- **Otimização de Sistema**: Verificações de saúde e validação de dados
- **Sistema de Menu**: Geração dinâmica de menu para acesso de autorização

**Dependências Externas:**
- **PostgreSQL**: Armazenamento primário de dados com recursos avançados
- **Redis**: Armazenamento de sessão (não usado diretamente em autorizações)
- **Serviço de Email**: Notificações potenciais (não implementado)

**Integração de API:**
- Endpoints RESTful com documentação OpenAPI
- Formato de requisição/resposta JSON
- Configuração CORS para acesso frontend
- Rate limiting (implementação básica)

## Testes

**Cobertura de Testes:**
- **Testes Unitários**: Validação de esquema, operações básicas de repositório
- **Testes de Integração**: Fluxos completos de autorização, uso de sessão
- **Testes de Regras de Negócio**: Validação de limites, ciclo de vida de autorização

**Cenários de Teste:**
- CRUD completo de autorizações
- Gerenciamento de sessão e limites
- Cenários de erro e casos extremos
- Validação de permissões e isolamento

## Monitoramento

**Métricas Coletadas:**
- Taxas de criação/atualização de autorização
- Padrões de uso de sessão
- Taxas de erro por tipo de operação
- Performance de query de banco de dados

**Verificações de Saúde:**
- Conectividade de banco de dados
- Integridade de dados de autorização
- Funcionamento do sistema de permissões

**Auditoria & Compliance:**
- Histórico completo de mudanças rastreando
- Logging de ação do usuário com timestamps
- Endereço IP e user agent gravando
- Compliance regulamentar para dados médicos

## Decisões de Design

**Arquitetura Simplificada:**
- Sem camada de domínio separada (lógica incorporada no repositório)
- Mapeamento direto esquema-para-modelo
- Complexidade mínima de middleware
- Foco em performance sobre pureza arquitetural

**Foco em Integridade de Dados:**
- Restrições de nível de banco de dados e triggers
- Validação abrangente em múltiplas camadas
- Trilha de auditoria para todas as mudanças
- Referencial integrity enforcement

**Adaptação de Domínio Médico:**
- Estruturas flexíveis de limite de sessão
- Integração de terminologia médica
- Rastreamento de requisitos de supervisão
- Suporte a códigos de diagnóstico (CID-10)

**Trade-offs de Escalabilidade:**
- BigInteger para crescimento futuro
- Otimização de índice para performance de query
- Uso de view para agregações complexas
- Potencial de processamento assíncrono

## Análise DBA

**Estratégia de Índices:**
```sql
-- Índices de lookup primário
medical_authorizations_contract_life_id_idx
medical_authorizations_service_id_idx  
medical_authorizations_doctor_id_idx
medical_authorizations_status_idx
medical_authorizations_date_range_idx
medical_authorizations_code_idx

-- Índices de tabela de histórico
authorization_history_authorization_idx
authorization_history_action_idx
authorization_history_date_idx
```

**Considerações de Performance:**
- **Particionamento**: Considerar particionamento por contract_id para datasets grandes
- **Arquivamento**: Implementar estratégia de arquivamento para autorizações expiradas
- **Replicação**: Dados de autorização devem ser replicados para alta disponibilidade

**Backup & Recuperação:**
- Capacidade de recuperação point-in-time
- Dados de autorização com criticidade médica (registros médicos)
- Estratégias de backup incremental
- Planejamento de recuperação de desastre

**Arquivamento de Dados:**
- Status-based archiving (autorizações expiradas)
- Gerenciamento de tamanho de tabela de histórico
- Retenção conforme regulamentos médicos
- Validação de dados arquivados

## Análise DBA - Estrutura do Banco de Dados

### Tabelas Principais e Relacionamentos

#### 1. **MEDICAL_AUTHORIZATIONS** (Tabela Central)
```sql
CREATE TABLE master.medical_authorizations (
    id                           BIGINT PRIMARY KEY DEFAULT nextval('medical_authorizations_id_seq'),
    contract_life_id             BIGINT NOT NULL REFERENCES contract_lives(id),
    service_id                   BIGINT NOT NULL REFERENCES services_catalog(id),
    doctor_id                    BIGINT NOT NULL REFERENCES users(id),
    authorization_code           VARCHAR(50) NOT NULL UNIQUE,
    authorization_date           DATE NOT NULL,
    valid_from                   DATE NOT NULL,
    valid_until                  DATE NOT NULL,
    -- Limites de sessão
    sessions_authorized          INTEGER,
    sessions_remaining           INTEGER,
    monthly_limit                INTEGER,
    weekly_limit                 INTEGER,
    daily_limit                  INTEGER,
    -- Informações médicas
    medical_indication           TEXT NOT NULL,
    contraindications            TEXT,
    special_instructions         TEXT,
    urgency_level                VARCHAR(20) CHECK (urgency_level IN ('URGENT','HIGH','NORMAL','LOW')),
    requires_supervision         BOOLEAN DEFAULT false,
    supervision_notes            TEXT,
    diagnosis_cid                VARCHAR(10),
    diagnosis_description        TEXT,
    treatment_goals              TEXT,
    expected_duration_days       INTEGER,
    -- Renovação
    renewal_allowed              BOOLEAN DEFAULT true,
    renewal_conditions           TEXT,
    -- Status e cancelamento
    status                       VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','expired','cancelled','suspended')),
    cancellation_reason          TEXT,
    cancelled_at                 TIMESTAMP,
    cancelled_by                 BIGINT REFERENCES users(id),
    -- Auditoria
    created_at                   TIMESTAMP NOT NULL DEFAULT now(),
    updated_at                   TIMESTAMP NOT NULL DEFAULT now(),
    created_by                   BIGINT REFERENCES users(id),
    updated_by                   BIGINT REFERENCES users(id)
);
```

**Características:**
- Código de autorização único para identificação externa
- Controle granular de limites (diário, semanal, mensal)
- Informações médicas obrigatórias (indicação)
- Suporte a renovação com condições específicas
- Múltiplos níveis de urgência
- Trilha completa de auditoria

#### 2. **AUTHORIZATION_HISTORY** (Trilha de Auditoria)
```sql
CREATE TABLE master.authorization_history (
    id                           BIGINT PRIMARY KEY DEFAULT nextval('authorization_history_id_seq'),
    authorization_id             BIGINT NOT NULL REFERENCES medical_authorizations(id),
    action                       VARCHAR(50) NOT NULL,
    field_changed                VARCHAR(100),
    old_value                    TEXT,
    new_value                    TEXT,
    reason                       TEXT,
    performed_by                 BIGINT NOT NULL REFERENCES users(id),
    performed_at                 TIMESTAMP NOT NULL DEFAULT now(),
    ip_address                   VARCHAR(45),
    user_agent                   TEXT
);
```

**Características:**
- Rastreamento granular de mudanças por campo
- Valores anteriores e novos armazenados
- Contexto completo (IP, user agent)
- Reasons obrigatórias para mudanças críticas

#### 3. **AUTHORIZATION_RENEWALS** (Histórico de Renovações)
```sql
CREATE TABLE master.authorization_renewals (
    id                           BIGINT PRIMARY KEY DEFAULT nextval('authorization_renewals_id_seq'),
    original_authorization_id    BIGINT NOT NULL REFERENCES medical_authorizations(id),
    new_authorization_id         BIGINT NOT NULL REFERENCES medical_authorizations(id),
    renewal_date                 DATE NOT NULL,
    renewal_reason               TEXT,
    changes_made                 TEXT,
    approved_by                  BIGINT NOT NULL REFERENCES users(id),
    created_at                   TIMESTAMP NOT NULL DEFAULT now()
);
```

**Características:**
- Relacionamento entre autorização original e nova
- Documentação de mudanças na renovação
- Aprovação obrigatória por usuário autorizado

#### 4. **ACTIVE_MEDICAL_AUTHORIZATIONS** (View Materializada)
```sql
-- View que agrega dados de autorizações ativas com informações relacionadas
CREATE VIEW master.active_medical_authorizations AS
SELECT
    ma.*,
    sc.name AS service_name,
    sc.category AS service_category,
    sc.type AS service_type,
    u.person_id,
    p.name AS doctor_name,
    pe.email_address AS doctor_email,
    pp.name AS patient_name
FROM medical_authorizations ma
JOIN services_catalog sc ON ma.service_id = sc.id
JOIN users u ON ma.doctor_id = u.id
JOIN people p ON u.person_id = p.id
LEFT JOIN emails pe ON pe.emailable_type = 'App\\Models\\People' AND pe.emailable_id = p.id
JOIN contract_lives cl ON ma.contract_life_id = cl.id
JOIN contracts c ON cl.contract_id = c.id
JOIN clients cli ON c.client_id = cli.id
JOIN people pp ON cli.person_id = pp.id
WHERE ma.status = 'active'
  AND ma.valid_until >= CURRENT_DATE
  AND ma.deleted_at IS NULL;
```

#### 5. **SERVICE_EXECUTIONS** (Execução de Serviços)
```sql
CREATE TABLE master.service_executions (
    id                           BIGINT PRIMARY KEY DEFAULT nextval('service_executions_id_seq'),
    contract_life_id             BIGINT NOT NULL REFERENCES contract_lives(id),
    service_id                   BIGINT NOT NULL REFERENCES services_catalog(id),
    execution_date               TIMESTAMP NOT NULL,
    professional_id              BIGINT REFERENCES users(id),
    quantity                     NUMERIC(8,2) DEFAULT 1.0,
    unit_value                   NUMERIC(10,2) NOT NULL,
    total_value                  NUMERIC(10,2) GENERATED ALWAYS AS (quantity * unit_value) STORED,
    -- Endereço do serviço
    service_address              JSON,
    -- Controle de tempo
    arrival_time                 TIMESTAMP,
    departure_time               TIMESTAMP,
    duration_minutes             INTEGER GENERATED ALWAYS AS (
        CASE WHEN departure_time IS NOT NULL AND arrival_time IS NOT NULL
        THEN EXTRACT(epoch FROM departure_time - arrival_time) / 60
        ELSE NULL END
    ) STORED,
    -- Informações clínicas
    execution_notes              TEXT,
    patient_response             TEXT,
    complications                TEXT,
    materials_used               JSON,
    -- Qualidade
    quality_score                INTEGER CHECK (quality_score BETWEEN 1 AND 10),
    family_satisfaction          INTEGER CHECK (family_satisfaction BETWEEN 1 AND 5),
    -- Status
    status                       VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('scheduled','in_progress','completed','cancelled')),
    cancellation_reason          TEXT,
    created_at                   TIMESTAMP NOT NULL DEFAULT now(),
    created_by                   BIGINT REFERENCES users(id)
);
```

### Índices Estratégicos

```sql
-- Índices primários para performance
CREATE INDEX idx_medical_authorizations_contract_life ON medical_authorizations(contract_life_id);
CREATE INDEX idx_medical_authorizations_service ON medical_authorizations(service_id);
CREATE INDEX idx_medical_authorizations_doctor ON medical_authorizations(doctor_id);
CREATE INDEX idx_medical_authorizations_status ON medical_authorizations(status) WHERE status != 'cancelled';
CREATE INDEX idx_medical_authorizations_dates ON medical_authorizations(valid_from, valid_until);
CREATE UNIQUE INDEX idx_medical_authorizations_code ON medical_authorizations(authorization_code);

-- Índices de auditoria
CREATE INDEX idx_authorization_history_auth ON authorization_history(authorization_id);
CREATE INDEX idx_authorization_history_action ON authorization_history(action);
CREATE INDEX idx_authorization_history_date ON authorization_history(performed_at);

-- Índices para execuções
CREATE INDEX idx_service_executions_contract_life ON service_executions(contract_life_id);
CREATE INDEX idx_service_executions_date ON service_executions(execution_date);
CREATE INDEX idx_service_executions_professional ON service_executions(professional_id);
CREATE INDEX idx_service_executions_status ON service_executions(status);

-- Índices compostos para queries complexas
CREATE INDEX idx_authorizations_active_lookup ON medical_authorizations(status, valid_until)
WHERE status = 'active';
CREATE INDEX idx_executions_date_status ON service_executions(execution_date, status)
WHERE status = 'completed';
```

### Triggers e Automatizações

```sql
-- Trigger para atualização automática de sessions_remaining
CREATE OR REPLACE FUNCTION update_sessions_remaining()
RETURNS TRIGGER AS $$
BEGIN
    -- Decrementar sessões restantes quando serviço é executado
    UPDATE medical_authorizations
    SET sessions_remaining = sessions_remaining - NEW.quantity,
        updated_at = now()
    WHERE id = (
        SELECT ma.id
        FROM medical_authorizations ma
        JOIN contract_lives cl ON ma.contract_life_id = cl.id
        WHERE cl.id = NEW.contract_life_id
          AND ma.service_id = NEW.service_id
          AND ma.status = 'active'
          AND NEW.execution_date BETWEEN ma.valid_from AND ma.valid_until
        LIMIT 1
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_sessions_remaining
    AFTER INSERT ON service_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_sessions_remaining();

-- Trigger para histórico de mudanças
CREATE OR REPLACE FUNCTION log_authorization_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- Log apenas campos que mudaram
        IF OLD.status != NEW.status THEN
            INSERT INTO authorization_history (authorization_id, action, field_changed, old_value, new_value, performed_by)
            VALUES (NEW.id, 'UPDATE', 'status', OLD.status, NEW.status, NEW.updated_by);
        END IF;

        IF OLD.sessions_remaining != NEW.sessions_remaining THEN
            INSERT INTO authorization_history (authorization_id, action, field_changed, old_value, new_value, performed_by)
            VALUES (NEW.id, 'UPDATE', 'sessions_remaining', OLD.sessions_remaining::text, NEW.sessions_remaining::text, NEW.updated_by);
        END IF;

        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO authorization_history (authorization_id, action, performed_by)
        VALUES (NEW.id, 'CREATE', NEW.created_by);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_authorization_changes
    AFTER INSERT OR UPDATE ON medical_authorizations
    FOR EACH ROW
    EXECUTE FUNCTION log_authorization_changes();
```

### Views Especializadas

```sql
-- View para dashboard de autorizações
CREATE VIEW vw_authorization_dashboard AS
SELECT
    ma.id,
    ma.authorization_code,
    pp.name AS patient_name,
    sc.name AS service_name,
    ma.sessions_authorized,
    ma.sessions_remaining,
    ma.valid_until,
    CASE
        WHEN ma.valid_until < CURRENT_DATE THEN 'expired'
        WHEN ma.sessions_remaining <= 0 THEN 'exhausted'
        WHEN ma.valid_until <= CURRENT_DATE + INTERVAL '7 days' THEN 'expiring_soon'
        ELSE 'active'
    END as urgency_status,
    pd.name AS doctor_name
FROM medical_authorizations ma
JOIN contract_lives cl ON ma.contract_life_id = cl.id
JOIN contracts c ON cl.contract_id = c.id
JOIN clients cli ON c.client_id = cli.id
JOIN people pp ON cli.person_id = pp.id
JOIN services_catalog sc ON ma.service_id = sc.id
JOIN users u ON ma.doctor_id = u.id
JOIN people pd ON u.person_id = pd.id
WHERE ma.status = 'active';

-- View para relatórios de uso
CREATE VIEW vw_service_usage_summary AS
SELECT
    ma.authorization_code,
    sc.name AS service_name,
    ma.sessions_authorized,
    ma.sessions_remaining,
    COALESCE(executed.total_executions, 0) AS sessions_used,
    ROUND(
        (COALESCE(executed.total_executions, 0)::numeric / NULLIF(ma.sessions_authorized, 0)) * 100,
        2
    ) AS usage_percentage
FROM medical_authorizations ma
JOIN services_catalog sc ON ma.service_id = sc.id
LEFT JOIN (
    SELECT
        se.contract_life_id,
        se.service_id,
        SUM(se.quantity) AS total_executions
    FROM service_executions se
    WHERE se.status = 'completed'
    GROUP BY se.contract_life_id, se.service_id
) executed ON executed.contract_life_id = ma.contract_life_id
           AND executed.service_id = ma.service_id
WHERE ma.status = 'active';
```

### Estratégias de Performance

#### Particionamento por Data
```sql
-- Particionamento da tabela de execuções por mês
CREATE TABLE service_executions_2024_01 PARTITION OF service_executions
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE service_executions_2024_02 PARTITION OF service_executions
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

#### Políticas de Retenção
```sql
-- Política para arquivamento de autorizações expiradas
CREATE OR REPLACE FUNCTION archive_expired_authorizations()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Mover autorizações expiradas há mais de 2 anos para tabela de arquivo
    WITH moved_rows AS (
        DELETE FROM medical_authorizations
        WHERE status = 'expired'
          AND valid_until < CURRENT_DATE - INTERVAL '2 years'
        RETURNING *
    )
    INSERT INTO medical_authorizations_archive
    SELECT * FROM moved_rows;

    GET DIAGNOSTICS archived_count = ROW_COUNT;
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Job automático de arquivamento (executar mensalmente)
SELECT cron.schedule('archive-expired-authorizations', '0 2 1 * *', 'SELECT archive_expired_authorizations();');
```

### Compliance e Auditoria

#### Retenção LGPD
```sql
-- Função para anonização de dados médicos sensíveis
CREATE OR REPLACE FUNCTION anonymize_medical_data(auth_id BIGINT)
RETURNS VOID AS $$
BEGIN
    UPDATE medical_authorizations
    SET
        medical_indication = '[ANONIMIZADO]',
        contraindications = '[ANONIMIZADO]',
        diagnosis_description = '[ANONIMIZADO]',
        treatment_goals = '[ANONIMIZADO]',
        updated_at = now()
    WHERE id = auth_id;

    -- Log da anonização
    INSERT INTO authorization_history (authorization_id, action, reason, performed_by)
    VALUES (auth_id, 'ANONYMIZE', 'Compliance LGPD', 1);
END;
$$ LANGUAGE plpgsql;
```

Esta implementação abrangente fornece um sistema de autorização médica seguro, escalável com trilhas de auditoria completas, imposição de regras de negócio e capacidades de integração adequadas para requisitos de domínio médico.

## Estrutura em Formato de Árvore

```
.
├── Backend
│   ├── app/infrastructure/orm/models.py
│   ├── app/presentation/schemas/medical_authorization.py
│   ├── app/infrastructure/repositories/medical_authorization_repository.py
│   ├── app/presentation/api/v1/medical_authorizations.py
│   ├── app/presentation/api/v1/api.py
│   ├── app/infrastructure/services/contract_dashboard_service.py
│   ├── app/infrastructure/services/system_optimization_service.py
│   └── app/infrastructure/repositories/limits_repository.py
├── Frontend
│   ├── frontend/src/services/medicalAuthorizationsService.ts
│   ├── frontend/src/pages/MedicalAuthorizationsPage.tsx
│   ├── frontend/src/hooks/useDataTable.ts
│   └── frontend/src/hooks/useErrorHandler.ts
├── Tests
│   ├── tests/test_medical_authorizations.py
│   ├── tests/test_home_care_business_rules.py
│   └── tests/test_home_care_integration.py
├── Config/Outros
│   ├── migrations/010_medical_authorizations.py
│   ├── migrations/011_automatic_limits_control.py
│   ├── migrations/012_service_execution_interface.py
│   ├── scripts/add_contract_permissions.py
│   ├── scripts/create_contract_menus_complete.py
│   ├── scripts/create_contract_menus_simple.py
│   ├── scripts/create_contract_menus.py
│   └── scripts/create_contract_views.py
```